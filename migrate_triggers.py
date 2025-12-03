#!/usr/bin/env python3
"""
Migration script for refactoring trigger architecture.

Migrates from old structure:
  - modules/*/triggers/  (mixed regex and callback-based)
  - modules/*/commands/  (regex-based)
  - modules/*/widgets/   (callback-based)

To new structure:
  - modules/*/telnet_triggers/  (regex-based only)
  - modules/*/callback_handlers/ (callback-based, includes widgets)

Also updates function signatures to unified format:
  handler(module, metadata, dispatchers_id=None)
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


def analyze_file(file_path: Path) -> str:
    """
    Determine if file is telnet_trigger or callback_handler.

    Returns:
        "telnet_trigger" if has "triggers" key with regex patterns
        "callback_handler" if has "handlers" key with paths
        "unknown" if can't determine
    """
    content = file_path.read_text()

    # Check for telnet trigger pattern (has "triggers" list with regex)
    if '"triggers":' in content or "'triggers':" in content:
        return "telnet_trigger"

    # Check for callback handler pattern (has "handlers" dict with paths)
    if '"handlers":' in content or "'handlers':" in content:
        return "callback_handler"

    return "unknown"


def find_modules() -> List[Path]:
    """Find all module directories."""
    modules_dir = Path("bot/modules")
    return [d for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]


def analyze_module(module_path: Path) -> Dict[str, List[Path]]:
    """
    Analyze a module and categorize its files.

    Returns dict with keys:
        - telnet_triggers: list of files to move to telnet_triggers/
        - callback_handlers: list of files to move to callback_handlers/
        - already_migrated: list of files already in new structure
    """
    result = {
        "telnet_triggers": [],
        "callback_handlers": [],
        "already_migrated": []
    }

    # Check old directories
    for subdir in ["triggers", "commands"]:
        subdir_path = module_path / subdir
        if subdir_path.exists():
            for file in subdir_path.glob("*.py"):
                if file.name in ("__init__.py", "common.py"):
                    continue

                file_type = analyze_file(file)
                if file_type == "telnet_trigger":
                    result["telnet_triggers"].append(file)
                elif file_type == "callback_handler":
                    result["callback_handlers"].append(file)

    # Widgets are always callback_handlers
    widgets_dir = module_path / "widgets"
    if widgets_dir.exists():
        for file in widgets_dir.glob("*.py"):
            if file.name not in ("__init__.py", "common.py"):
                result["callback_handlers"].append(file)

    # Check for already migrated files
    for new_dir in ["telnet_triggers", "callback_handlers"]:
        new_dir_path = module_path / new_dir
        if new_dir_path.exists():
            for file in new_dir_path.glob("*.py"):
                if file.name not in ("__init__.py", "common.py"):
                    result["already_migrated"].append(file)

    return result


def get_function_signature_info(content: str, func_name: str = "main_function") -> Dict:
    """
    Extract information about a function's signature.

    Returns dict with:
        - found: bool
        - line_start: int (line number where function starts)
        - original_sig: str (the def line)
        - params: list of parameter names
    """
    # Match function definition
    pattern = rf'^def {func_name}\((.*?)\):'

    for i, line in enumerate(content.split('\n'), 1):
        match = re.match(pattern, line)
        if match:
            params_str = match.group(1)
            # Parse parameters (simple parsing, may need refinement)
            params = [p.strip().split('=')[0].strip('*') for p in params_str.split(',') if p.strip()]

            return {
                "found": True,
                "line_start": i,
                "original_sig": line,
                "params": params
            }

    return {"found": False}


def update_callback_handler_signature(content: str, func_name: str = "main_function") -> str:
    """
    Update callback handler signature from various formats to:
    def handler(module, callback_meta, dispatchers_id=None):

    Also updates function body to use callback_meta instead of kwargs.
    """
    lines = content.split('\n')

    # Find function definition
    func_pattern = rf'^def {func_name}\((.*?)\):'

    for i, line in enumerate(lines):
        match = re.match(func_pattern, line)
        if match:
            # Get indentation
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent

            # Replace signature
            lines[i] = f"{indent_str}def {func_name}(module, callback_meta, dispatchers_id=None):"

            # Update function body - replace common kwargs access patterns
            # This is basic - may need manual review
            j = i + 1
            while j < len(lines):
                # Stop at next function definition
                if lines[j].strip() and not lines[j].strip().startswith('#') and lines[j][0] not in (' ', '\t'):
                    break

                # Replace kwargs.get(...) with callback_meta.get(...)
                lines[j] = lines[j].replace('kwargs.get(', 'callback_meta.get(')
                lines[j] = lines[j].replace('widget.get(', 'callback_meta.get(')

                j += 1
            break

    return '\n'.join(lines)


def update_telnet_trigger_signature(content: str, func_name: str = "main_function") -> str:
    """
    Update telnet trigger signature to:
    def handler(module, trigger_meta, dispatchers_id=None):

    Also updates function body to use trigger_meta.
    """
    lines = content.split('\n')

    func_pattern = rf'^def {func_name}\((.*?)\):'

    for i, line in enumerate(lines):
        match = re.match(func_pattern, line)
        if match:
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent

            lines[i] = f"{indent_str}def {func_name}(module, trigger_meta, dispatchers_id=None):"

            # Update function body
            j = i + 1
            while j < len(lines):
                if lines[j].strip() and not lines[j].strip().startswith('#') and lines[j][0] not in (' ', '\t'):
                    break

                # Replace common telnet trigger patterns
                lines[j] = lines[j].replace('kwargs.get("regex_results")', 'trigger_meta["regex_result"]')
                lines[j] = lines[j].replace('regex_results', 'trigger_meta["regex_result"]')
                lines[j] = lines[j].replace('regex_result', 'trigger_meta["regex_result"]')
                lines[j] = lines[j].replace('calling_module', 'trigger_meta["source_module"]')
                lines[j] = lines[j].replace('source_module', 'trigger_meta["source_module"]')

                j += 1
            break

    return '\n'.join(lines)


def update_registration_call(content: str, old_func: str, new_func: str) -> str:
    """Update registration function calls (e.g., register_trigger -> register_telnet_trigger)"""
    return content.replace(f'.{old_func}(', f'.{new_func}(')


def migrate_file(file_path: Path, target_dir: Path, file_type: str) -> None:
    """
    Migrate a single file:
    1. Move to new directory
    2. Update signature
    3. Update registration call
    """
    print(f"  Migrating: {file_path.relative_to(Path('bot/modules'))}")

    # Read content
    content = file_path.read_text()

    # Update signatures
    if file_type == "callback_handler":
        # Update main_function signature
        if "def main_function(" in content:
            content = update_callback_handler_signature(content, "main_function")

        # Update widget functions (update_widget, main_widget, etc.)
        for func in ["update_widget", "main_widget", "select_widget_view", "main_view", "options_view"]:
            if f"def {func}(" in content:
                content = update_callback_handler_signature(content, func)

        # Update registration call
        content = update_registration_call(content, "register_trigger", "register_callback_handler")
        content = update_registration_call(content, "register_widget", "register_widget")  # widgets keep their register

    elif file_type == "telnet_trigger":
        if "def main_function(" in content:
            content = update_telnet_trigger_signature(content, "main_function")

        content = update_registration_call(content, "register_trigger", "register_telnet_trigger")

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Write to new location
    target_file = target_dir / file_path.name
    target_file.write_text(content)

    print(f"    -> {target_file.relative_to(Path('bot/modules'))}")


def migrate_module(module_path: Path, dry_run: bool = True) -> None:
    """Migrate a single module."""
    print(f"\n{'='*60}")
    print(f"Module: {module_path.name}")
    print(f"{'='*60}")

    analysis = analyze_module(module_path)

    if analysis["already_migrated"]:
        print(f"  Already migrated: {len(analysis['already_migrated'])} files")

    if not analysis["telnet_triggers"] and not analysis["callback_handlers"]:
        print("  Nothing to migrate")
        return

    print(f"  Telnet triggers: {len(analysis['telnet_triggers'])}")
    print(f"  Callback handlers: {len(analysis['callback_handlers'])}")

    if dry_run:
        print("  [DRY RUN - no changes made]")
        for file in analysis["telnet_triggers"]:
            print(f"    Would move: {file.name} -> telnet_triggers/")
        for file in analysis["callback_handlers"]:
            print(f"    Would move: {file.name} -> callback_handlers/")
    else:
        # Migrate files
        for file in analysis["telnet_triggers"]:
            target_dir = module_path / "telnet_triggers"
            migrate_file(file, target_dir, "telnet_trigger")

        for file in analysis["callback_handlers"]:
            # Widgets stay in widgets/ but get updated
            if "widgets" in file.parts:
                target_dir = file.parent
            else:
                target_dir = module_path / "callback_handlers"
            migrate_file(file, target_dir, "callback_handler")


def main():
    import sys

    dry_run = "--execute" not in sys.argv

    if dry_run:
        print("\n" + "="*60)
        print("DRY RUN MODE - Use --execute to actually migrate")
        print("="*60)

    modules = find_modules()

    for module_path in sorted(modules):
        migrate_module(module_path, dry_run=dry_run)

    print("\n" + "="*60)
    if dry_run:
        print("DRY RUN COMPLETE - Run with --execute to apply changes")
    else:
        print("MIGRATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
