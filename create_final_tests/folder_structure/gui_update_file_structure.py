import os
import re
import shutil
from pathlib import Path

import dearpygui.dearpygui as dpg

# --- Configuration ---

REQ_PATH = Path("..") / "artifacts" / "req.md"
CONFIG_FILE_PATH = "task_list_configuration.md"
OUTPUT_MD_FILE = "file_structure.md"


def load_config_from_md(config_path):
    """Load SCAN_BASE_DIR and ROOT_DIRS_TO_SCAN from a markdown configuration file."""
    scan_base_dir = None
    root_dirs_to_scan = []

    default_scan_base_dir = "../../../../../../"
    default_root_dirs_to_scan = ["docs", "lib"]

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        match_base_dir = re.search(r"### SCAN_BASE_DIR\s*\n`([^`]+)`", content)
        if match_base_dir:
            scan_base_dir = match_base_dir.group(1).strip()
        else:
            print(f"Warning: SCAN_BASE_DIR not found in {config_path}. Using default.")
            scan_base_dir = default_scan_base_dir

        match_root_section = re.search(
            r"### ROOT_DIRS_TO_SCAN\s*\n((?:-\s*`[^`]+`\s*\n?)+)",
            content,
            re.MULTILINE,
        )
        if match_root_section:
            items_block = match_root_section.group(1)
            root_dirs_to_scan = [item.strip() for item in re.findall(r"`([^`]+)`", items_block)]
    except FileNotFoundError:
        print(f"Config file {config_path} not found. Using defaults.")
    except Exception as e:
        print(f"Error parsing config {config_path}: {e}")

    if not scan_base_dir:
        scan_base_dir = default_scan_base_dir
    if not root_dirs_to_scan:
        root_dirs_to_scan = default_root_dirs_to_scan

    return scan_base_dir, root_dirs_to_scan


class Node:
    """Represents a file or directory in the GUI tree."""

    def __init__(self, path, parent=None):
        self.path = path
        self.parent = parent
        self.is_dir = os.path.isdir(path)
        self.children = []
        self.state = 0  # 0: unchecked, 1: checked, 2: partial
        self.checkbox_id = None
        self.tree_id = None
        self.text_id = None

    def build_children(self):
        if not self.is_dir:
            return
        try:
            # Sort files and directories separately, then combine
            entries = os.listdir(self.path)
            files = sorted([e for e in entries if os.path.isfile(os.path.join(self.path, e))])
            dirs = sorted([e for e in entries if os.path.isdir(os.path.join(self.path, e))])

            for entry in dirs + files:
                if entry.startswith(".") or entry == "__pycache__":
                    continue
                child_path = os.path.join(self.path, entry)
                child = Node(child_path, parent=self)
                # Recursively build the tree
                if child.is_dir:
                    child.build_children()
                self.children.append(child)
        except Exception as e:
            print(f"Cannot access {self.path}: {e}")

    def update_display(self):
        if self.checkbox_id is None:
            return

        dpg.set_value(self.checkbox_id, self.state != 0)

        base_name = os.path.basename(self.path)
        if self.state == 1:
            prefix = "[+]"
        elif self.state == 0:
            prefix = "[ ]"
        else:  # state == 2
            prefix = "[-]"
        new_label = f"{prefix} {base_name}"

        if self.is_dir and self.tree_id:
            dpg.configure_item(self.tree_id, label=new_label)
        elif self.text_id:
            dpg.set_value(self.text_id, new_label)

    def set_state(self, state):
        self.state = state
        if self.is_dir:
            for ch in self.children:
                ch.set_state(state)
        self.update_display()

    def refresh_from_children(self):
        if not self.is_dir or not self.children:
            return

        child_states = {c.state for c in self.children}

        if len(child_states) == 1:
            self.state = child_states.pop()
        else:
            self.state = 2

        self.update_display()

        if self.parent:
            self.parent.refresh_from_children()

    def on_check(self, sender, app_data, user_data):
        node_instance = user_data
        new_state = 1 if dpg.get_value(sender) else 0
        node_instance.set_state(new_state)
        if node_instance.parent:
            node_instance.parent.refresh_from_children()

    def build_gui(self, parent_id):
        with dpg.group(horizontal=True, parent=parent_id):
            self.checkbox_id = dpg.add_checkbox(callback=self.on_check, user_data=self)

            placeholder = f"[ ] {os.path.basename(self.path)}"
            if self.is_dir:
                with dpg.tree_node(label=placeholder, indent=10) as self.tree_id:
                    for ch in self.children:
                        ch.build_gui(self.tree_id)
            else:
                self.text_id = dpg.add_text(placeholder, indent=10)
        self.update_display()

    def collect_selected_files(self):
        selected = []
        if self.is_dir:
            if self.state == 1:
                for root, _, files in os.walk(self.path):
                    for f in files:
                        if f.startswith("."):
                            continue
                        selected.append(os.path.join(root, f))
            elif self.state == 2:
                for ch in self.children:
                    selected.extend(ch.collect_selected_files())
        else:
            if self.state == 1:
                selected.append(self.path)
        return selected


class FileSelectorGUI:
    def __init__(self, base_dir, root_dirs):
        self.base_dir = os.path.abspath(base_dir)
        self.root_dirs = root_dirs
        self.root_nodes = []
        for rd in self.root_dirs:
            abs_root = os.path.join(self.base_dir, rd)
            if os.path.exists(abs_root):
                node = Node(abs_root)
                node.build_children()
                self.root_nodes.append(node)
            else:
                print(f"Warning: Root directory not found and skipped: {abs_root}")

        self.all_expanded = False

        dpg.create_context()

        font_path = "OpenSans-Regular.ttf"
        if os.path.exists(font_path):
            try:
                with dpg.font_registry():
                    with dpg.font(font_path, 16) as default_font:
                        dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
                dpg.bind_font(default_font)
            except Exception as e:
                print(f"Error loading font '{font_path}': {e}. Characters may not render correctly.")
        else:
            print(f"Warning: Font file '{font_path}' not found. Cyrillic characters may not display correctly.")

        dpg.create_viewport(title="Select Files to Include", width=1024, height=768)

        with dpg.theme() as green_button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 179, 113, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (85, 194, 138, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (40, 140, 90, 255))

        with dpg.window(label="File Selector") as self.window:
            with dpg.group(horizontal=True):
                self.expand_btn = dpg.add_button(label="Expand All", callback=self.toggle_expand_collapse_all)
                generate_btn = dpg.add_button(label="✅ Generate", callback=self.generate)
                dpg.bind_item_theme(generate_btn, green_button_theme)

            with dpg.child_window(width=-1, height=-1, border=False) as self.tree_area:
                for node in self.root_nodes:
                    node.build_gui(self.tree_area)

            # --- FIX: Replaced dpg.modal with dpg.window(modal=True) for backward compatibility ---
            with dpg.window(tag="success_modal", label="Success", modal=True, show=False, no_close=True, width=400):
                dpg.add_text("Operation completed successfully!")
                dpg.add_separator()
                dpg.add_text("", tag="success_modal_details", wrap=380)  # wrap width smaller than window width
                dpg.add_spacer(height=10)
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("success_modal", show=False))

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.window, True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def toggle_expand_collapse_all(self):
        self.all_expanded = not self.all_expanded
        for node in self.root_nodes:
            self._set_open_recursive(node, self.all_expanded)

        new_label = "Collapse All" if self.all_expanded else "Expand All"
        dpg.configure_item(self.expand_btn, label=new_label)

    def _set_open_recursive(self, node, open_flag):
        if node.is_dir and node.tree_id is not None:
            try:
                dpg.configure_item(node.tree_id, open=open_flag)
            except SystemError as e:
                print(f"Error toggling node state: {e}. Consider updating dearpygui.")

            for ch in node.children:
                self._set_open_recursive(ch, open_flag)

    def get_selected_files(self):
        files = []
        for node in self.root_nodes:
            files.extend(node.collect_selected_files())
        return sorted(list(set(files)))

    def generate(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            print("No files selected for processing.")
            dpg.set_value("success_modal_details", "No files were selected. Nothing to generate.")
            dpg.configure_item("success_modal", show=True)
            return

        try:
            final_output = build_output(selected_files, self.base_dir)

            output_abs = os.path.abspath(OUTPUT_MD_FILE)
            with open(output_abs, "w", encoding="utf-8") as f:
                f.write(final_output)
            print(f"Output successfully written to: {output_abs}")

            req_abs_path = Path(__file__).resolve().parent / REQ_PATH
            copy_message = ""
            try:
                req_abs_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(output_abs, req_abs_path)
                copy_message = f"\n\nAlso copied to:\n{req_abs_path}"
                print(f"Copied result to: {req_abs_path}")
            except Exception as e:
                copy_message = f"\n\nCould not copy to artifacts path:\n{e}"
                print(f"Error copying to '{req_abs_path}': {e}")

            dpg.set_value("success_modal_details", f"Output written to:\n{output_abs}{copy_message}")
            dpg.configure_item("success_modal", show=True)

        except Exception as e:
            print(f"Error during generation: {e}")
            dpg.set_value("success_modal_details", f"An error occurred:\n{e}")
            dpg.configure_item("success_modal", show=True)


def build_tree_dict(selected_files_abs, base_dir):
    tree = {}
    for file_path in selected_files_abs:
        try:
            rel_path = os.path.relpath(file_path, base_dir)
        except ValueError:
            print(f"Warning: Could not get relative path for {file_path}")
            continue

        parts = Path(rel_path).parts
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault("files", []).append(parts[-1])
    return tree


def _build_md_lines(node, indent, lines):
    dirs = sorted([k for k in node.keys() if k != "files"])
    files = sorted(node.get("files", []))

    for d in dirs:
        lines.append("  " * indent + f"- {d}/")
        _build_md_lines(node[d], indent + 1, lines)
    for f in files:
        lines.append("  " * indent + f"- {f}")


def build_output(selected_files_abs, base_dir):
    tree_dict = build_tree_dict(selected_files_abs, base_dir)
    tree_lines = []
    for root_name in sorted(tree_dict.keys()):
        tree_lines.append(f"- {root_name}/")
        _build_md_lines(tree_dict[root_name], 1, tree_lines)
    tree_string = "\n".join(tree_lines)

    content_blocks = []
    tagged_paths = sorted(
        [(os.path.relpath(p, base_dir).replace(os.sep, "/"), p) for p in selected_files_abs]
    )

    for rel_path, abs_path in tagged_paths:
        content = ""
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            content_blocks.append(f'<file path="{rel_path}">\n{content}\n</file>')
        except UnicodeDecodeError:
            msg = "[Error: Cannot display content of binary file]"
            content_blocks.append(f'<file path="{rel_path}">\n{msg}\n</file>')
        except Exception as e:
            msg = f"[Error reading file: {e}]"
            content_blocks.append(f'<file path="{rel_path}">\n{msg}\n</file>')

    final_parts = []
    if tree_string.strip():
        final_parts.append(tree_string.strip())

    if content_blocks:
        files_section_string = "\n\n\n".join(content_blocks)
        final_parts.append(files_section_string)

    final_output_string = "\n\n\n".join(final_parts)
    if final_output_string:
        final_output_string += "\n"

    return final_output_string


if __name__ == "__main__":
    scan_base_dir, root_dirs = load_config_from_md(CONFIG_FILE_PATH)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir_abs = os.path.abspath(os.path.join(script_dir, scan_base_dir))

    print(f"Scanning base directory: {base_dir_abs}")
    print(f"Scanning root folders: {root_dirs}")

    FileSelectorGUI(base_dir_abs, root_dirs)
