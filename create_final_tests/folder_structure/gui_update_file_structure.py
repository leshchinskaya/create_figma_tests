import os
import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
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


class TreeItem:
    """Represents a file or directory in the GUI tree."""

    def __init__(self, gui, parent_frame, abs_path, parent=None):
        self.gui = gui
        self.parent = parent
        self.abs_path = abs_path
        self.is_dir = os.path.isdir(abs_path)
        self.children = []
        self.var = tk.IntVar(value=0)

        self.frame = ttk.Frame(parent_frame)
        self.frame.pack(fill="x", anchor="w")

        if self.is_dir:
            self.expanded = False
            self.toggle_btn = ttk.Button(
                self.frame,
                width=2,
                text="+",
                command=self.toggle,
                padding=(2, 0, 2, 0),
            )
            self.toggle_btn.pack(side="left")
        else:
            ttk.Label(self.frame, width=2).pack(side="left")

        self.chk = ttk.Checkbutton(
            self.frame,
            variable=self.var,
            command=self.on_check,
        )
        self.chk.pack(side="left")

        name = os.path.basename(abs_path)
        ttk.Label(self.frame, text=name, font=("TkDefaultFont", 14)).pack(side="left", anchor="w")

        self.children_frame = ttk.Frame(parent_frame)
        if self.is_dir:
            try:
                entries = os.listdir(abs_path)
                files = sorted([e for e in entries if os.path.isfile(os.path.join(abs_path, e))])
                dirs = sorted([e for e in entries if os.path.isdir(os.path.join(abs_path, e))])
                for entry in files + dirs:
                    if entry == ".DS_Store":
                        continue
                    child_path = os.path.join(abs_path, entry)
                    child = TreeItem(gui, self.children_frame, child_path, parent=self)
                    self.children.append(child)
            except Exception as e:
                print(f"Cannot access {abs_path}: {e}")

    def toggle(self):
        if not self.is_dir:
            return
        if self.expanded:
            self.children_frame.pack_forget()
            self.toggle_btn.config(text="+")
            self.expanded = False
        else:
            self.children_frame.pack(fill="x", anchor="w", padx=20, after=self.frame)
            self.toggle_btn.config(text="-")
            self.expanded = True
        # force layout update to avoid stale display on some systems
        self.gui.root.update_idletasks()

    def on_check(self):
        state = self.var.get()
        self.set_state(state)
        if self.parent:
            self.parent.refresh_state_from_children()

    def set_state(self, state):
        self.var.set(state)
        self.chk.state(["!alternate"])
        if self.is_dir:
            for child in self.children:
                child.set_state(state)

    def refresh_state_from_children(self):
        if not self.is_dir:
            return
        child_states = [child.var.get() for child in self.children]
        if all(s == 1 for s in child_states):
            self.var.set(1)
            self.chk.state(["!alternate"])
        elif all(s == 0 for s in child_states):
            self.var.set(0)
            self.chk.state(["!alternate"])
        else:
            self.var.set(-1)
            self.chk.state(["alternate"])
        if self.parent:
            self.parent.refresh_state_from_children()

    def collect_selected_files(self):
        selected = []
        if os.path.isfile(self.abs_path):
            if self.var.get() == 1:
                selected.append(self.abs_path)
        else:
            if self.var.get() == 1 and not self.chk.instate(["alternate"]):
                for root, _, files in os.walk(self.abs_path):
                    for f in files:
                        if f == ".DS_Store":
                            continue
                        selected.append(os.path.join(root, f))
            else:
                for ch in self.children:
                    selected.extend(ch.collect_selected_files())
        return selected


class FileSelectorGUI:
    def __init__(self, base_dir, root_dirs):
        self.base_dir = os.path.abspath(base_dir)
        self.root_dirs = root_dirs

        self.root = tk.Tk()
        self.root.title("Select files to include")
        self.root.geometry("1024x720")
        self.root.after(100, lambda: (self.root.lift(), self.root.focus_force()))

        canvas = tk.Canvas(self.root, borderwidth=0)
        yscroll = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.container = ttk.Frame(canvas)

        self.container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.container, anchor="nw")
        canvas.configure(yscrollcommand=yscroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        self.items = []
        for rd in self.root_dirs:
            abs_root = os.path.join(self.base_dir, rd)
            item = TreeItem(self, self.container, abs_root)
            self.items.append(item)

        controls = ttk.Frame(self.root)
        controls.pack(fill="x")
        self.all_expanded = False
        self.expand_btn = ttk.Button(controls, text="Expand All", command=self.toggle_expand_collapse_all)
        self.expand_btn.pack(side="left", fill="x", expand=True)
        btn = ttk.Button(controls, text="Generate", command=self.generate)
        btn.pack(side="left", fill="x", expand=True)

        # Ensure geometry is calculated so the UI is responsive on start
        self.root.update_idletasks()
        # On some systems the window stays blank until an initial update
        self.root.update()

        self.root.mainloop()

    def toggle_expand_collapse_all(self):
        for item in self.items:
            self._toggle_item_recursive(item, not self.all_expanded)
        self.all_expanded = not self.all_expanded
        self.expand_btn.config(text="Collapse All" if self.all_expanded else "Expand All")

    def _toggle_item_recursive(self, item, expand):
        if item.is_dir:
            if expand and not item.expanded:
                item.toggle()
            elif not expand and item.expanded:
                item.toggle()
            for ch in item.children:
                self._toggle_item_recursive(ch, expand)

    def get_selected_files(self):
        files = []
        for item in self.items:
            files.extend(item.collect_selected_files())
        return sorted(set(files))

    def generate(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showinfo("Nothing selected", "No files selected for processing")
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

