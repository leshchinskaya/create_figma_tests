import os
import re
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# --- Configuration ---
REQ_PATH = Path("..") / "artifacts" / "req.md"
CONFIG_FILE_PATH = "task_list_configuration.md"
OUTPUT_MD_FILE = "file_structure.md"


def load_config_from_md(config_path):
    """Load SCAN_BASE_DIR and ROOT_DIRS_TO_SCAN from markdown config."""
    scan_base_dir = None
    root_dirs_to_scan = []

    default_scan_base_dir = "../../../../../../"
    default_root_dirs_to_scan = ["docs", "lib"]

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match_base_dir = re.search(r"### SCAN_BASE_DIR\s*\n`([^`]+)`", content)
        if match_base_dir:
            scan_base_dir = match_base_dir.group(1).strip()
        else:
            print(f"Warning: SCAN_BASE_DIR not found in {config_path}. Using default.")
            scan_base_dir = default_scan_base_dir

        match_root_section = re.search(r"### ROOT_DIRS_TO_SCAN\s*\n((?:-\s*`[^`]+`\s*\n?)+)",
                                        content, re.MULTILINE)
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


class FileSelectorGUI:
    SYMBOLS = {0: '\u2610', 1: '\u25EA', 2: '\u2611'}  # unchecked, partial, checked

    def __init__(self, base_dir, root_dirs):
        self.base_dir = os.path.abspath(base_dir)
        self.root_dirs = root_dirs
        self.root = tk.Tk()
        self.root.title("Select files to include")

        style = ttk.Style(self.root)
        style.configure('Treeview', rowheight=26, font=('TkDefaultFont', 12))
        self.root.option_add('*Treeview.Font', ('TkDefaultFont', 12))

        self.tree = ttk.Treeview(self.root, show='tree')
        yscroll = ttk.Scrollbar(self.root, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        yscroll.pack(side='right', fill='y')

        self.item_state = {}
        self.item_path = {}

        for rd in self.root_dirs:
            abs_root = os.path.join(self.base_dir, rd)
            self._add_path_recursive('', abs_root, rd)

        self.tree.bind('<Button-1>', self._on_click)

        btn = ttk.Button(self.root, text="Generate", command=self.generate)
        btn.pack(fill='x')

        self.root.mainloop()

    def _format_text(self, name, state):
        return f"{self.SYMBOLS[state]} {name}"

    def _add_item(self, parent, abs_path, display_name):
        state = 0
        item_id = self.tree.insert(parent, 'end', text=self._format_text(display_name, state), open=False)
        self.item_state[item_id] = state
        self.item_path[item_id] = abs_path
        return item_id

    def _add_path_recursive(self, parent, abs_path, display_name=None):
        name = display_name if display_name is not None else os.path.basename(abs_path)
        item_id = self._add_item(parent, abs_path, name)
        if os.path.isdir(abs_path):
            try:
                entries = sorted(os.listdir(abs_path))
            except Exception as e:
                print(f"Cannot access {abs_path}: {e}")
                return
            for entry in entries:
                if entry == '.DS_Store':
                    continue
                self._add_path_recursive(item_id, os.path.join(abs_path, entry))
        return item_id

    def _on_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        element = self.tree.identify('element', event.x, event.y)
        if element == 'indicator':
            return  # allow normal expand/collapse
        state = self.item_state.get(item, 0)
        new_state = 0 if state == 2 else 2
        self._set_state_recursive(item, new_state)
        parent = self.tree.parent(item)
        while parent:
            self._update_parent_state(parent)
            parent = self.tree.parent(parent)

    def _set_state_recursive(self, item, state):
        self.item_state[item] = state
        name = os.path.basename(self.item_path[item]) if '/' in self.item_path[item] else self.item_path[item]
        display = self.tree.item(item, 'text').split(' ', 1)[-1]
        # Use existing display text without symbol
        self.tree.item(item, text=self._format_text(display, state))
        for child in self.tree.get_children(item):
            self._set_state_recursive(child, state)

    def _update_parent_state(self, item):
        child_states = [self.item_state.get(ch, 0) for ch in self.tree.get_children(item)]
        if not child_states:
            return
        if all(st == 2 for st in child_states):
            state = 2
        elif all(st == 0 for st in child_states):
            state = 0
        else:
            state = 1
        self.item_state[item] = state
        display = self.tree.item(item, 'text').split(' ', 1)[-1]
        self.tree.item(item, text=self._format_text(display, state))

    def _collect_files(self, item):
        path = self.item_path[item]
        state = self.item_state.get(item, 0)
        selected = []
        if os.path.isfile(path):
            if state == 2:
                selected.append(path)
        else:
            if state == 2:
                for root, _, files in os.walk(path):
                    for f in files:
                        if f == '.DS_Store':
                            continue
                        selected.append(os.path.join(root, f))
            else:
                for ch in self.tree.get_children(item):
                    selected.extend(self._collect_files(ch))
        return selected

    def get_selected_files(self):
        files = []
        for root_item in self.tree.get_children(''):
            files.extend(self._collect_files(root_item))
        return sorted(set(files))

    def generate(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showinfo("Nothing selected", "No files selected for processing")
            return
        try:
            final_output = build_output(selected_files, self.base_dir)
            output_abs = os.path.join(os.getcwd(), OUTPUT_MD_FILE)
            with open(output_abs, 'w', encoding='utf-8') as f:
                f.write(final_output)
            req_abs = Path(__file__).resolve().parent / REQ_PATH
            try:
                shutil.copyfile(output_abs, req_abs)
                print(f"Copied result to: {req_abs}")
            except Exception as e:
                print(f"Error copying to '{req_abs}': {e}")
            messagebox.showinfo("Done", f"Output written to {output_abs}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


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
        node.setdefault('__files__', []).append(parts[-1])
    return tree


def _build_md_lines(node, indent, lines):
    dirs = sorted([k for k in node.keys() if k != '__files__'])
    files = sorted(node.get('__files__', []))
    for d in dirs:
        lines.append(' ' * indent + f"- {d}/")
        _build_md_lines(node[d], indent + 2, lines)
    for f in files:
        lines.append(' ' * indent + f"- {f}")


def build_output(selected_files_abs, base_dir):
    tree = build_tree_dict(selected_files_abs, base_dir)
    lines = []
    for root_idx, root_name in enumerate(sorted(tree.keys())):
        lines.append(f"- {root_name}/")
        _build_md_lines(tree[root_name], 2, lines)
        if root_idx < len(tree) - 1:
            lines.append('')
    tree_string = '\n'.join(lines)

    content_blocks = []
    tagged_paths = []
    for file_path in selected_files_abs:
        rel = os.path.relpath(file_path, base_dir).replace(os.sep, '/')
        tagged_paths.append((rel, file_path))
    tagged_paths.sort(key=lambda x: x[0])
    for tag, abs_path in tagged_paths:
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if abs_path.endswith('.md'):
                content_blocks.append(f'<file path="{tag}">\n{content}\n</file>')
        except Exception as e:
            content_blocks.append(f'<file path="{tag}">\nError reading file: {e}\n</file>')

    if not tree_string.strip() and not content_blocks:
        final_output_string = '\n'
    elif not content_blocks:
        final_output_string = tree_string
        if not final_output_string.endswith('\n'):
            final_output_string += '\n'
    else:
        components = []
        if tree_string.strip():
            components.append(tree_string)
            if not tree_string.endswith('\n'):
                components.append('\n')
            components.append('\n\n\n')
        files_section_string = '\n\n\n'.join(content_blocks)
        components.append(files_section_string)
        final_output_string = ''.join(components)
        final_output_string = final_output_string.rstrip('\n') + '\n'

    return final_output_string


if __name__ == '__main__':
    scan_base_dir, root_dirs = load_config_from_md(CONFIG_FILE_PATH)
    base_dir_abs = os.path.abspath(os.path.join(os.getcwd(), scan_base_dir))
    FileSelectorGUI(base_dir_abs, root_dirs)
