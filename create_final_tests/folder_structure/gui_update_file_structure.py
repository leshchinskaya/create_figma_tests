import os
import re
import shutil
from heapq import merge
from pathlib import Path

import dearpygui.dearpygui as dpg


# --- Configuration ---
SCRIPT_DIR = Path(__file__).resolve().parent
REQ_PATH = SCRIPT_DIR.parent / "artifacts" / "req.md"
CONFIG_FILE_PATH = SCRIPT_DIR / "task_list_configuration.md"
OUTPUT_MD_FILE = SCRIPT_DIR / "file_structure.md"

# --- Font Configuration ---
FONT_REGULAR = SCRIPT_DIR / "OpenSans-Regular.ttf"
FONT_SYMBOLS = SCRIPT_DIR / "NotoSansSymbols2-Regular.ttf"


def load_config_from_md(config_path: Path):
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
            scan_base_dir = default_scan_base_dir
        match_root_section = re.search(
            r"### ROOT_DIRS_TO_SCAN\s*\n((?:-\s*`[^`]+`\s*\n?)+)", content, re.MULTILINE
        )
        if match_root_section:
            items_block = match_root_section.group(1)
            root_dirs_to_scan = [item.strip() for item in re.findall(r"`([^`]+)`", items_block)]
    except FileNotFoundError:
        print(f"Config file {config_path} not found. Using defaults.")
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
        self.state = 0
        self.checkbox_id = None
        self.tree_id = None
        self.text_id = None

    def build_children(self):
        if not self.is_dir:
            return
        try:
            entries = os.listdir(self.path)
            files = sorted([e for e in entries if os.path.isfile(os.path.join(self.path, e))])
            dirs = sorted([e for e in entries if os.path.isdir(os.path.join(self.path, e))])
            for entry in dirs + files:
                if entry.startswith(".") or entry == "__pycache__":
                    continue
                child_path = os.path.join(self.path, entry)
                child = Node(child_path, parent=self)
                if child.is_dir:
                    child.build_children()
                self.children.append(child)
        except Exception as e:
            print(f"Cannot access {self.path}: {e}")

    def update_display(self):
        if not dpg.does_item_exist(self.checkbox_id): return
        dpg.set_value(self.checkbox_id, self.state != 0)
        base_name = os.path.basename(self.path)
        prefixes = {0: "[ ]", 1: "[+]", 2: "[-]"}
        new_label = f"{prefixes.get(self.state, '[-_]')} {base_name}"
        if self.is_dir and dpg.does_item_exist(self.tree_id):
            dpg.configure_item(self.tree_id, label=new_label)
        elif dpg.does_item_exist(self.text_id):
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
        with dpg.group(parent=parent_id, horizontal=True):
            self.checkbox_id = dpg.add_checkbox(callback=self.on_check, user_data=self)
            dpg.add_spacer(width=4)
            placeholder = f"[ ] {os.path.basename(self.path)}"
            if self.is_dir:
                with dpg.tree_node(label=placeholder) as self.tree_id:
                    for ch in self.children:
                        ch.build_gui(self.tree_id)
            else:
                self.text_id = dpg.add_text(placeholder)
        self.update_display()

    def collect_selected_files(self):
        selected = []
        if self.is_dir:
            if self.state == 1:
                for root, _, files in os.walk(self.path):
                    for f in files:
                        if f.startswith("."): continue
                        selected.append(os.path.join(root, f))
            elif self.state == 2:
                for ch in self.children:
                    selected.extend(ch.collect_selected_files())
        elif self.state == 1:
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
                print(f"Warning: Root directory not found: {abs_root}")
        self.all_expanded = False
        for font_file in [FONT_REGULAR, FONT_SYMBOLS]:
            if not Path(font_file).exists():
                raise FileNotFoundError(f"Required font not found: {font_file}")
        dpg.create_context()
        with dpg.font_registry():
            with dpg.font(str(FONT_REGULAR), 16) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
        dpg.bind_font(default_font)
        dpg.create_viewport(title="Select Files", width=1024, height=768)
        with dpg.theme() as green_button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 179, 113, 255))
        with dpg.window(label="File Selector") as self.window:
            with dpg.group(horizontal=True):
                self.expand_btn = dpg.add_button(label="Expand All", callback=self.toggle_expand_collapse_all)
                dpg.add_button(label="Select All", callback=self.select_all)
                dpg.add_button(label="Unselect All", callback=self.unselect_all)
                generate_btn = dpg.add_button(label="Generate", callback=self.generate)
                dpg.bind_item_theme(generate_btn, green_button_theme)
            with dpg.child_window(width=-1, height=-1, border=False) as self.tree_area:
                for node in self.root_nodes:
                    node.build_gui(self.tree_area)
            with dpg.window(tag="success_modal", label="Success", modal=True, show=False, width=400):
                dpg.add_text("Operation completed successfully!")
                dpg.add_separator()
                dpg.add_text("", tag="success_modal_details", wrap=380)
                dpg.add_button(label="OK", width=-1, callback=lambda: dpg.configure_item("success_modal", show=False))
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.window, True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def select_all(self):
        for node in self.root_nodes:
            node.set_state(1)

    def unselect_all(self):
        for node in self.root_nodes:
            node.set_state(0)

    def toggle_expand_collapse_all(self):
        self.all_expanded = not self.all_expanded
        for node in self.root_nodes:
            self._set_open_recursive(node, self.all_expanded)
        new_label = "Collapse All" if self.all_expanded else "Expand All"
        dpg.configure_item(self.expand_btn, label=new_label)

    def _set_open_recursive(self, node, open_flag):
        if node.is_dir and dpg.does_item_exist(node.tree_id):
            # --- FIX: Use `dpg.set_value()` to open/close a tree_node ---
            # This is the correct method, not `dpg.configure_item()`.
            dpg.set_value(node.tree_id, open_flag)
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
            dpg.set_value("success_modal_details", "No files selected.")
            dpg.configure_item("success_modal", show=True)
            return
        try:
            final_output = build_output(selected_files, self.base_dir)
            output_abs = OUTPUT_MD_FILE.resolve()
            with open(output_abs, "w", encoding="utf-8") as f:
                f.write(final_output)
            req_abs_path = REQ_PATH
            copy_message = ""
            try:
                req_abs_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(output_abs, req_abs_path)
                copy_message = f"\n\nAlso copied to:\n{req_abs_path}"
            except Exception as e:
                copy_message = f"\n\nCould not copy: {e}"
            dpg.set_value("success_modal_details", f"Output written to:\n{output_abs}{copy_message}")
            dpg.configure_item("success_modal", show=True)
        except Exception as e:
            dpg.set_value("success_modal_details", f"An error occurred:\n{e}")
            dpg.configure_item("success_modal", show=True)


def build_tree_dict(selected_files_abs, base_dir):
    tree = {}
    for file_path in selected_files_abs:
        try:
            rel_path = os.path.relpath(file_path, base_dir)
            # noinspection PyTypeChecker
            parts = Path(rel_path).parts
            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node.setdefault("files", []).append(parts[-1])
        except ValueError:
            continue
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
    tagged_paths = sorted([(os.path.relpath(p, base_dir).replace(os.sep, "/"), p) for p in selected_files_abs])
    for rel_path, abs_path in tagged_paths:
        content = ""
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            content_blocks.append(f'<file path="{rel_path}">\n{content}\n</file>')
        except Exception:
            msg = "[Error: Cannot display content]"
            content_blocks.append(f'<file path="{rel_path}">\n{msg}\n</file>')
    final_parts = [part for part in [tree_string.strip(), "\n\n\n".join(content_blocks)] if part]
    final_output_string = "\n\n\n".join(final_parts) + "\n" if final_parts else ""
    return final_output_string


if __name__ == "__main__":
    scan_base, root_dirs_to_scan = load_config_from_md(CONFIG_FILE_PATH)
    base_dir_path = (SCRIPT_DIR / scan_base).resolve()
    print(f"Base directory: {base_dir_path}")
    print(f"Root folders: {root_dirs_to_scan}")
    FileSelectorGUI(base_dir_path, root_dirs_to_scan)
