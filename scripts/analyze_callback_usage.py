#!/usr/bin/env python3
"""
Callback Dict Usage Analyzer

Scans the codebase for all callback_dict usage:
- dom.data.upsert() calls
- dom.data.append() calls
- dom.data.remove_key_by_path() calls
- widget_meta["handlers"] registrations

Generates a complete inventory for Phase 0 of the refactoring plan.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


class CallbackAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.results = {
            "upsert_calls": [],
            "append_calls": [],
            "remove_calls": [],
            "handler_registrations": []
        }

    def analyze(self):
        """Run all analysis passes."""
        print("🔍 Analyzing callback_dict usage...")
        print(f"📁 Root directory: {self.root_dir}\n")

        # Find all Python files in bot/modules
        modules_dir = self.root_dir / "bot" / "modules"
        if not modules_dir.exists():
            print(f"❌ Error: {modules_dir} does not exist!")
            return

        python_files = list(modules_dir.rglob("*.py"))
        print(f"📄 Found {len(python_files)} Python files\n")

        # Analyze each file
        for py_file in python_files:
            self._analyze_file(py_file)

        # Print results
        self._print_results()

        # Generate markdown report
        self._generate_report()

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            relative_path = file_path.relative_to(self.root_dir)

            # Find upsert calls
            self._find_upsert_calls(relative_path, content, lines)

            # Find append calls
            self._find_append_calls(relative_path, content, lines)

            # Find remove calls
            self._find_remove_calls(relative_path, content, lines)

            # Find handler registrations
            self._find_handler_registrations(relative_path, content, lines)

        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")

    def _find_upsert_calls(self, file_path: Path, content: str, lines: List[str]):
        """Find all dom.data.upsert() calls."""
        # Pattern: module.dom.data.upsert( or self.dom.data.upsert(
        pattern = r'(module|self)\.dom\.data\.upsert\('

        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1

            # Try to extract callback levels
            min_level, max_level = self._extract_callback_levels(lines, line_num)

            # Try to determine data depth
            depth = self._estimate_data_depth(lines, line_num)

            self.results["upsert_calls"].append({
                "file": str(file_path),
                "line": line_num,
                "min_callback_level": min_level,
                "max_callback_level": max_level,
                "estimated_depth": depth
            })

    def _find_append_calls(self, file_path: Path, content: str, lines: List[str]):
        """Find all dom.data.append() calls."""
        pattern = r'(module|self)\.dom\.data\.append\('

        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1

            self.results["append_calls"].append({
                "file": str(file_path),
                "line": line_num
            })

    def _find_remove_calls(self, file_path: Path, content: str, lines: List[str]):
        """Find all dom.data.remove_key_by_path() calls."""
        pattern = r'(module|self)\.dom\.data\.remove_key_by_path\('

        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1

            self.results["remove_calls"].append({
                "file": str(file_path),
                "line": line_num
            })

    def _find_handler_registrations(self, file_path: Path, content: str, lines: List[str]):
        """Find all widget_meta handler registrations."""
        # Look for widget_meta = { ... "handlers": { ... } ... }

        if 'widget_meta' not in content:
            return

        if '"handlers"' not in content and "'handlers'" not in content:
            return

        # Find line with handlers dict
        in_handlers = False
        handlers_start = None

        for i, line in enumerate(lines):
            if '"handlers"' in line or "'handlers'" in line:
                in_handlers = True
                handlers_start = i + 1
                continue

            if in_handlers:
                # Look for path patterns
                # Pattern: "path/pattern": handler_function,
                path_match = re.search(r'["\']([^"\']+)["\']:\s*(\w+)', line)

                if path_match:
                    path_pattern = path_match.group(1)
                    handler_name = path_match.group(2)

                    # Calculate depth
                    depth = path_pattern.count('/')

                    self.results["handler_registrations"].append({
                        "file": str(file_path),
                        "line": i + 1,
                        "path_pattern": path_pattern,
                        "handler_function": handler_name,
                        "depth": depth
                    })

                # Check if we've left the handlers dict
                if '}' in line and ',' not in line:
                    in_handlers = False

    def _extract_callback_levels(self, lines: List[str], start_line: int) -> Tuple[str, str]:
        """Try to extract min_callback_level and max_callback_level from upsert call."""
        min_level = "None"
        max_level = "None"

        # Look at next ~10 lines for callback level params
        for i in range(start_line - 1, min(start_line + 10, len(lines))):
            line = lines[i]

            if 'min_callback_level' in line:
                match = re.search(r'min_callback_level\s*=\s*(\d+|None)', line)
                if match:
                    min_level = match.group(1)

            if 'max_callback_level' in line:
                match = re.search(r'max_callback_level\s*=\s*(\d+|None)', line)
                if match:
                    max_level = match.group(1)

            # Stop at closing paren
            if ')' in line:
                break

        return min_level, max_level

    def _estimate_data_depth(self, lines: List[str], start_line: int) -> int:
        """Estimate the depth of data being upserted by counting dict nesting."""
        depth = 0
        brace_count = 0

        # Look backwards for opening brace
        for i in range(start_line - 1, max(0, start_line - 30), -1):
            line = lines[i]

            if 'upsert({' in line or 'upsert( {' in line:
                # Count colons/keys in following lines until we reach reasonable depth
                for j in range(i, min(i + 50, len(lines))):
                    check_line = lines[j]

                    # Count dictionary depth by tracking braces
                    brace_count += check_line.count('{')
                    brace_count -= check_line.count('}')

                    if brace_count < 0:
                        break

                    # Rough estimate: each key-value pair increases depth
                    if '":' in check_line or "\':" in check_line:
                        depth += 1

                break

        # Depth is usually around 4-6 for locations/players
        return min(depth, 10)  # Cap at reasonable number

    def _print_results(self):
        """Print analysis results to console."""
        print("\n" + "=" * 70)
        print("📊 ANALYSIS RESULTS")
        print("=" * 70 + "\n")

        print(f"🔹 Upsert Calls: {len(self.results['upsert_calls'])}")
        print(f"🔹 Append Calls: {len(self.results['append_calls'])}")
        print(f"🔹 Remove Calls: {len(self.results['remove_calls'])}")
        print(f"🔹 Handler Registrations: {len(self.results['handler_registrations'])}")

        print("\n" + "-" * 70)
        print("UPSERT CALLS BY CALLBACK LEVELS:")
        print("-" * 70)

        # Group by callback levels
        level_groups = {}
        for call in self.results["upsert_calls"]:
            key = f"min={call['min_callback_level']}, max={call['max_callback_level']}"
            if key not in level_groups:
                level_groups[key] = []
            level_groups[key].append(call)

        for levels, calls in sorted(level_groups.items()):
            print(f"\n{levels}: {len(calls)} calls")
            for call in calls:
                print(f"  📄 {call['file']}:{call['line']}")

        print("\n" + "-" * 70)
        print("HANDLER REGISTRATIONS BY DEPTH:")
        print("-" * 70)

        # Group by depth
        depth_groups = {}
        for handler in self.results["handler_registrations"]:
            depth = handler['depth']
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(handler)

        for depth in sorted(depth_groups.keys()):
            handlers = depth_groups[depth]
            print(f"\nDepth {depth}: {len(handlers)} handlers")
            for h in handlers:
                print(f"  📄 {h['file']}:{h['line']}")
                print(f"     Pattern: {h['path_pattern']}")
                print(f"     Handler: {h['handler_function']}")

    def _generate_report(self):
        """Generate markdown report."""
        report_path = self.root_dir / "CALLBACK_DICT_INVENTORY.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Callback Dict Usage Inventory\n\n")
            f.write("Generated by analyze_callback_usage.py\n\n")

            f.write("## Summary\n\n")
            f.write(f"- **Upsert Calls:** {len(self.results['upsert_calls'])}\n")
            f.write(f"- **Append Calls:** {len(self.results['append_calls'])}\n")
            f.write(f"- **Remove Calls:** {len(self.results['remove_calls'])}\n")
            f.write(f"- **Handler Registrations:** {len(self.results['handler_registrations'])}\n\n")

            f.write("---\n\n")

            f.write("## Upsert Calls\n\n")
            f.write("| File | Line | Min Level | Max Level | Est. Depth |\n")
            f.write("|------|------|-----------|-----------|------------|\n")
            for call in self.results["upsert_calls"]:
                f.write(f"| {call['file']} | {call['line']} | "
                       f"{call['min_callback_level']} | {call['max_callback_level']} | "
                       f"{call['estimated_depth']} |\n")

            f.write("\n---\n\n")

            f.write("## Append Calls\n\n")
            f.write("| File | Line |\n")
            f.write("|------|------|\n")
            for call in self.results["append_calls"]:
                f.write(f"| {call['file']} | {call['line']} |\n")

            f.write("\n---\n\n")

            f.write("## Remove Calls\n\n")
            f.write("| File | Line |\n")
            f.write("|------|------|\n")
            for call in self.results["remove_calls"]:
                f.write(f"| {call['file']} | {call['line']} |\n")

            f.write("\n---\n\n")

            f.write("## Handler Registrations\n\n")
            f.write("| File | Line | Depth | Path Pattern | Handler Function |\n")
            f.write("|------|------|-------|--------------|------------------|\n")
            for handler in self.results["handler_registrations"]:
                f.write(f"| {handler['file']} | {handler['line']} | "
                       f"{handler['depth']} | `{handler['path_pattern']}` | "
                       f"`{handler['handler_function']}` |\n")

            f.write("\n---\n\n")
            f.write("## Next Steps\n\n")
            f.write("1. Review each upsert call - does it send complete or partial data?\n")
            f.write("2. Review each handler - does it expect complete or partial data?\n")
            f.write("3. Identify mismatches that will benefit from enrichment\n")
            f.write("4. Plan which files need updating in Phase 2 and Phase 3\n")

        print(f"\n✅ Report generated: {report_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        # Assume we're in the scripts directory
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    analyzer = CallbackAnalyzer(root)
    analyzer.analyze()

    print("\n✨ Analysis complete!")
    print("📋 Review CALLBACK_DICT_INVENTORY.md for detailed results")
    print("📖 See CALLBACK_DICT_REFACTOR_PLAN.md for next steps\n")
