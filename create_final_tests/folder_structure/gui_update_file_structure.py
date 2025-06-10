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
            if not root_dirs_to_scan:
                root_dirs_to_scan = default_root_dirs_to_scan
        else:
            print(f"Warning: ROOT_DIRS_TO_SCAN not found in {config_path}. Using default list.")
            root_dirs_to_scan = default_root_dirs_to_scan

    except FileNotFoundError:
        print(f"Config file {config_path} not found. Using defaults.")
        scan_base_dir = default_scan_base_dir
        root_dirs_to_scan = default_root_dirs_to_scan
    except Exception as e:
        print(f"Error parsing config {config_path}: {e}")
        scan_base_dir = default_scan_base_dir
        root_dirs_to_scan = default_root_dirs_to_scan

    if scan_base_dir is None:
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
            entries = os.listdir(self.path)
        except Exception as e:
            print(f"Cannot access {self.path}: {e}")
            entries = []
        files = sorted([e for e in entries if os.path.isfile(os.path.join(self.path, e))])
        dirs = sorted([e for e in entries if os.path.isdir(os.path.join(self.path, e))])
        for entry in files + dirs:
            if entry == ".DS_Store":
                continue
            child_path = os.path.join(self.path, entry)
            child = Node(child_path, parent=self)
            child.build_children()
            self.children.append(child)

    # --- GUI helpers ---
    def update_display(self):
        if self.checkbox_id is None:
            return
        if self.state == 2:
            dpg.set_value(self.checkbox_id, True)
            dpg.set_item_label(self.checkbox_id, "mixed")
        else:
            dpg.set_item_label(self.checkbox_id, "")
            dpg.set_value(self.checkbox_id, bool(self.state))

    def set_state(self, state):
        self.state = state
        self.update_display()
        if self.is_dir:
            for ch in self.children:
                ch.set_state(state)

    def refresh_from_children(self):
        if not self.is_dir:
            return
        child_states = [c.state for c in self.children]
        if all(s == 1 for s in child_states):
            self.state = 1
        elif all(s == 0 for s in child_states):
            self.state = 0
        else:
            self.state = 2
        self.update_display()
        if self.parent:
            self.parent.refresh_from_children()

    def on_check(self, sender, app_data):
        val = dpg.get_value(sender)
        self.state = 1 if val else 0
        self.update_display()
        if self.is_dir:
            for ch in self.children:
                ch.set_state(self.state)
        if self.parent:
            self.parent.refresh_from_children()

    def build_gui(self, parent_id):
        with dpg.group(parent=parent_id):
            self.checkbox_id = dpg.add_checkbox(label="", callback=self.on_check, user_data=self)
            dpg.add_same_line()
            if self.is_dir:
                self.tree_id = dpg.add_tree_node(label=os.path.basename(self.path))
                for ch in self.children:
                    ch.build_gui(self.tree_id)
            else:
                self.text_id = dpg.add_text(os.path.basename(self.path))
        self.update_display()

    def collect_selected_files(self):
        selected = []
        if self.is_dir:
            if self.state == 1 and all(ch.state == 1 for ch in self.children):
                for root, _, files in os.walk(self.path):
                    for f in files:
                        if f == ".DS_Store":
                            continue
                        selected.append(os.path.join(root, f))
            else:
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
            node = Node(abs_root)
            node.build_children()
            self.root_nodes.append(node)

        dpg.create_context()
        dpg.create_viewport(title="Select files to include", width=1024, height=720)

        with dpg.window(label="File Selector", width=1024, height=720) as self.window:
            self.expand_btn = dpg.add_button(label="Expand All", callback=self.toggle_expand_collapse_all)
            dpg.add_same_line()
            dpg.add_button(label="Generate", callback=self.generate)
            with dpg.child_window(width=-1, height=-1) as self.tree_area:
                for node in self.root_nodes:
                    node.build_gui(self.tree_area)

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.window, True)
        dpg.focus_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

    def toggle_expand_collapse_all(self, sender, app_data):
        expand = not getattr(self, "all_expanded", False)
        for node in self.root_nodes:
            self._set_open_recursive(node, expand)
        self.all_expanded = expand
        dpg.configure_item(self.expand_btn, label="Collapse All" if expand else "Expand All")

    def _set_open_recursive(self, node, open_flag):
        if node.tree_id is not None:
            dpg.set_tree_node_open(node.tree_id, open_flag)
        for ch in node.children:
            self._set_open_recursive(ch, open_flag)

    def get_selected_files(self):
        files = []
        for node in self.root_nodes:
            files.extend(node.collect_selected_files())
        return sorted(set(files))

    def generate(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            print("No files selected for processing")
            return
        try:
            final_output = build_output(selected_files, self.base_dir)
            output_abs = os.path.join(os.getcwd(), OUTPUT_MD_FILE)
            with open(output_abs, "w", encoding="utf-8") as f:
                f.write(final_output)
            req_abs = Path(__file__).resolve().parent / REQ_PATH
            try:
                shutil.copyfile(output_abs, req_abs)
                print(f"Copied result to: {req_abs}")
            except Exception as e:
                print(f"Error copying to '{req_abs}': {e}")
            print(f"Output written to {output_abs}")
        except Exception as e:
            print(f"Error: {e}")


def build_tree_dict(selected_files_abs, base_dir):
    tree = {}
    for file_path in selected_files_abs:
        try:
            rel = os.path.relpath(file_path, base_dir)
        except ValueError:
            continue
        parts = rel.split(os.sep)
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault("__files__", []).append(parts[-1])
    return tree


def _build_md_lines(node, indent, lines):
    dirs = sorted([k for k in node.keys() if k != "__files__"])
    files = sorted(node.get("__files__", []))
    for d in dirs:
        lines.append(" " * indent + f"- {d}/")
        _build_md_lines(node[d], indent + 2, lines)
    for f in files:
        lines.append(" " * indent + f"- {f}")


def build_output(selected_files_abs, base_dir):
    tree = build_tree_dict(selected_files_abs, base_dir)
    lines = []
    for idx, root_name in enumerate(sorted(tree.keys())):
        lines.append(f"- {root_name}/")
        _build_md_lines(tree[root_name], 2, lines)
        if idx < len(tree) - 1:
            lines.append("")
    tree_string = "\n".join(lines)

    content_blocks = []
    tagged_paths = []
    for file_path in selected_files_abs:
        rel = os.path.relpath(file_path, base_dir).replace(os.sep, "/")
        tagged_paths.append((rel, file_path))
    tagged_paths.sort(key=lambda x: x[0])
    for tag, abs_path in tagged_paths:
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if abs_path.endswith(".md"):
                content_blocks.append(f'<file path="{tag}">\n{content}\n</file>')
        except Exception as e:
            content_blocks.append(f'<file path="{tag}">\nError reading file: {e}\n</file>')

    if not tree_string.strip() and not content_blocks:
        final_output_string = "\n"
    elif not content_blocks:
        final_output_string = tree_string
        if not final_output_string.endswith("\n"):
            final_output_string += "\n"
    else:
        components = []
        if tree_string.strip():
            components.append(tree_string)
            if not tree_string.endswith("\n"):
                components.append("\n")
            components.append("\n\n\n")
        files_section_string = "\n\n\n".join(content_blocks)
        components.append(files_section_string)
        final_output_string = "".join(components)
        final_output_string = final_output_string.rstrip("\n") + "\n"

    return final_output_string


if __name__ == "__main__":
    scan_base_dir, root_dirs = load_config_from_md(CONFIG_FILE_PATH)
    base_dir_abs = os.path.abspath(os.path.join(os.getcwd(), scan_base_dir))
    FileSelectorGUI(base_dir_abs, root_dirs)
