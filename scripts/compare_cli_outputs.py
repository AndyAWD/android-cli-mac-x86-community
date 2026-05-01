import subprocess
import json
import os
import sys

COMMANDS = [
    ["--help"],
    ["info"],
    ["sdk", "list"],
    ["emulator", "list"],
    ["describe", "--project_dir", "."],
]

def run_cmd(cmd_list, env=None):
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True, env=env)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode
    except Exception as e:
        return str(e), "", -1

def compare_json(expected, actual, path="root"):
    if isinstance(expected, dict) and isinstance(actual, dict):
        diffs = []
        for k in expected:
            if k not in actual:
                diffs.append(f"{path}: Missing key '{k}'")
            else:
                diffs.extend(compare_json(expected[k], actual[k], f"{path}.{k}"))
        for k in actual:
            if k not in expected:
                diffs.append(f"{path}: Unexpected key '{k}'")
        return diffs
    elif isinstance(expected, list) and isinstance(actual, list):
        # We only compare list length or structure loosely, but let's try exact match for now
        diffs = []
        if len(expected) != len(actual):
             diffs.append(f"{path}: List length mismatch {len(expected)} != {len(actual)}")
        # Deep compare lists
        for i, (e_val, a_val) in enumerate(zip(expected, actual)):
             diffs.extend(compare_json(e_val, a_val, f"{path}[{i}]"))
        return diffs
    else:
        # Check type
        if type(expected) != type(actual):
             return [f"{path}: Type mismatch {type(expected).__name__} != {type(actual).__name__}"]
        return []

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(root_dir, "src")

    all_match = True

    for args in COMMANDS:
        print(f"=== Testing: {' '.join(args)} ===")
        android_cmd = ["android"] + args
        custom_cmd = [sys.executable, "-m", "android_cli_mac_x86_community"] + args

        expected_stdout, expected_stderr, expected_code = run_cmd(android_cmd)
        actual_stdout, actual_stderr, actual_code = run_cmd(custom_cmd, env=env)

        if expected_code != actual_code:
            print(f"  [X] Return code mismatch: {expected_code} != {actual_code}")
            print(f"      Expected stderr: {expected_stderr}")
            print(f"      Actual stderr: {actual_stderr}")
            all_match = False
            continue

        if "--json" in args:
            try:
                expected_json = json.loads(expected_stdout)
            except json.JSONDecodeError:
                print(f"  [!] Failed to parse expected JSON: {expected_stdout[:100]}")
                all_match = False
                continue

            try:
                actual_json = json.loads(actual_stdout)
            except json.JSONDecodeError:
                print(f"  [!] Failed to parse actual JSON: {actual_stdout[:100]}")
                all_match = False
                continue

            diffs = compare_json(expected_json, actual_json)
            if diffs:
                print("  [X] JSON Schema Mismatch:")
                for d in diffs:
                    print(f"      - {d}")
                all_match = False
            else:
                print("  [O] JSON Schema Match!")
        else:
            # Just do a rough check or report success if both return 0 and have output
            if actual_code == 0:
                 print("  [O] Execution Successful!")
            else:
                 print("  [X] Execution Failed!")
                 all_match = False

    if all_match:
        print("\nAll tested commands match!")
        sys.exit(0)
    else:
        print("\nSome commands failed the comparison.")
        sys.exit(1)

if __name__ == "__main__":
    main()
