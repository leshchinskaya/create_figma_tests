from pathlib import Path
import os
import re  # For parsing the config file
import shutil

# --- Configuration ---
CONFIG_FILE_PATH = Path("task_list_configuration.md")  # Path to the central configuration file
OUTPUT_MD_FILE = Path("file_structure.md")  # The output markdown file
REQ_PATH = Path("..") / "artifacts" / "req.md"

# todo ignore .DS_Store
def load_config_from_md(config_path):
    """Loads SCAN_BASE_DIR and ROOT_DIRS_TO_SCAN from the markdown configuration file."""
    scan_base_dir = None
    root_dirs_to_scan = []

    # Default values in case the config file is missing or parsing fails
    default_scan_base_dir = "../../../../../../"
    default_root_dirs_to_scan = ["docs", "lib"]

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract SCAN_BASE_DIR
        match_base_dir = re.search(r"### SCAN_BASE_DIR\s*\n`([^`]+)`", content)
        if match_base_dir:
            scan_base_dir = match_base_dir.group(1).strip()
        else:
            print(f"Warning: SCAN_BASE_DIR not found in {config_path}. Using default: '{default_scan_base_dir}'")
            scan_base_dir = default_scan_base_dir

        # Extract ROOT_DIRS_TO_SCAN
        # This regex looks for the "### ROOT_DIRS_TO_SCAN" header,
        # then captures the subsequent list items formatted as "- `directory_name`".
        match_root_dirs_section = re.search(r"### ROOT_DIRS_TO_SCAN\s*\n((?:-\s*`[^`]+`\s*\n?)+)", content, re.MULTILINE)
        if match_root_dirs_section:
            items_block = match_root_dirs_section.group(1)
            # Extract individual directory names from the captured block
            root_dirs_to_scan = [item.strip() for item in re.findall(r"`([^`]+)`", items_block)]
            if not root_dirs_to_scan:
                print(f"Warning: ROOT_DIRS_TO_SCAN found but no items parsed in {config_path}. Using defaults.")
                root_dirs_to_scan = default_root_dirs_to_scan
        else:
            print(f"Warning: ROOT_DIRS_TO_SCAN section not found or malformed in {config_path}. Using defaults.")
            root_dirs_to_scan = default_root_dirs_to_scan

    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        print(f"Using default SCAN_BASE_DIR: '{default_scan_base_dir}' and ROOT_DIRS_TO_SCAN: {default_root_dirs_to_scan}")
        scan_base_dir = default_scan_base_dir
        root_dirs_to_scan = default_root_dirs_to_scan
    except Exception as e:
        print(f"Error reading or parsing configuration file '{config_path}': {e}")
        print(f"Using default SCAN_BASE_DIR: '{default_scan_base_dir}' and ROOT_DIRS_TO_SCAN: {default_root_dirs_to_scan}")
        scan_base_dir = default_scan_base_dir
        root_dirs_to_scan = default_root_dirs_to_scan

    # Final check if values were somehow not set, though covered by above logic
    if scan_base_dir is None:
        print(f"SCAN_BASE_DIR could not be determined. Using default: '{default_scan_base_dir}'")
        scan_base_dir = default_scan_base_dir
    if not root_dirs_to_scan: # Check if list is empty
        print(f"ROOT_DIRS_TO_SCAN is empty or could not be determined. Using defaults: {default_root_dirs_to_scan}")
        root_dirs_to_scan = default_root_dirs_to_scan

    return scan_base_dir, root_dirs_to_scan

SCAN_BASE_DIR, ROOT_DIRS_TO_SCAN = load_config_from_md(CONFIG_FILE_PATH)
# ---------------------

def generate_file_structure_md(base_dir_relative_to_workspace, dirs_in_base_to_scan, output_md_file):
    """
    Generates a markdown file representing the directory structure and content of .md files
    from a list of specified subdirectories within a base directory.
    """
    all_structure_segments = [] # Holds strings for each root's tree and separators
    collected_md_files_for_content = []  # Stores (path_for_tag, absolute_path_for_reading) for all roots
    abs_workspace_root = Path.cwd()

    # Nested helper function to generate tree for a single root directory
    def _generate_tree_recursive_for_single_root(
        current_dir_abs,
        current_prefix,
        lines_for_this_tree_segment, # List to append this root's tree lines to
        _abs_scan_root_for_this_iteration, # The absolute path of the root directory for this specific scan iteration
        _relative_scan_root_path_to_workspace # The relative path of the root (e.g., Req/Main) for display
    ):
        # Add the root directory name itself (relative to workspace) when it's the starting point
        if current_dir_abs == _abs_scan_root_for_this_iteration:
            lines_for_this_tree_segment.append(_relative_scan_root_path_to_workspace + "/") # Display full relative path

        try:
            items = sorted(Path(current_dir_abs).iterdir())
        except OSError as e:
            print(f"Warning: Could not list directory {current_dir_abs}: {e}")
            return

        for i, item_name in enumerate(items):
            if item_name == ".DS_Store":
                continue
            item_abs_path = current_dir_abs / item_name
            is_last_item = (i == len(items) - 1)
            connector = "└── " if is_last_item else "├── "

            if item_abs_path.is_dir():
                lines_for_this_tree_segment.append(current_prefix + connector + item_name + "/")
                new_prefix_for_children = current_prefix + ("    " if is_last_item else "│   ")
                _generate_tree_recursive_for_single_root(
                    item_abs_path,
                    new_prefix_for_children,
                    lines_for_this_tree_segment,
                    _abs_scan_root_for_this_iteration,
                    _relative_scan_root_path_to_workspace
                )
            else:  # It's a file
                lines_for_this_tree_segment.append(current_prefix + connector + item_name)
                if item_name.endswith(".md"):
                    tag_path = item_abs_path.relative_to(abs_workspace_root)
                    normalized_tag_path = str(tag_path).replace(os.sep, '/')
                    collected_md_files_for_content.append((normalized_tag_path, str(item_abs_path)))

    first_valid_root_processed_and_yielded_content = False
    for dir_name_in_base in dirs_in_base_to_scan:
        # Construct the full relative path from workspace to the current target subdirectory
        current_target_root_relative_to_workspace = Path(base_dir_relative_to_workspace) / dir_name_in_base
        current_scan_root_abs_path = abs_workspace_root / current_target_root_relative_to_workspace

        if not current_scan_root_abs_path.is_dir():
            print(f"Error: Target directory '{current_target_root_relative_to_workspace}' not found at '{current_scan_root_abs_path}'.")
            continue

        if first_valid_root_processed_and_yielded_content:
            all_structure_segments.append("\n\n")

        current_segment_lines = []
        _generate_tree_recursive_for_single_root(
            current_scan_root_abs_path,
            "", # Initial prefix for items directly under this root
            current_segment_lines,
            current_scan_root_abs_path,
            current_target_root_relative_to_workspace # Pass the full relative path for display
        )

        if current_segment_lines:
            all_structure_segments.append("\n".join(current_segment_lines))
            first_valid_root_processed_and_yielded_content = True

    content_blocks = []
    collected_md_files_for_content.sort(key=lambda x: x[0])

    for tag_path, file_abs_path in collected_md_files_for_content:
        try:
            with open(file_abs_path, 'r', encoding='utf-8') as f:
                file_content = f.read().strip()
            content_blocks.append(f'<file path="{tag_path}">\n{file_content}\n</file>')
        except Exception as e:
            content_blocks.append(f'<file path="{tag_path}">\nError reading file: {e}\n</file>')

    tree_string = "".join(all_structure_segments)

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
        final_output_string = final_output_string.rstrip('\n') + '\n'

    try:
        output_abs_path = abs_workspace_root / output_md_file
        with open(output_abs_path, 'w', encoding='utf-8') as f:
            f.write(final_output_string)
        print(f"Successfully updated '{output_md_file}' based on subdirectories {dirs_in_base_to_scan} within '{base_dir_relative_to_workspace}'.")
        print(f"Output written to: {output_abs_path}")

        req_abs = Path(__file__).resolve().parent / REQ_PATH
        try:
            shutil.copyfile(output_abs_path, req_abs)
            print(f"Also copied result to: {req_abs}")
        except Exception as e:
            print(f"Error copying to '{req_abs}': {e}")
    except Exception as e:
        print(f"Error writing to '{output_md_file}': {e}")

if __name__ == "__main__":
    generate_file_structure_md(SCAN_BASE_DIR, ROOT_DIRS_TO_SCAN, OUTPUT_MD_FILE)