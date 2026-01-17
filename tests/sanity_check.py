import sys
import os
import importlib
import traceback

# Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
parent_root = os.path.dirname(project_root)
sys.path.insert(0, parent_root)

print(f"Checking files in: {parent_root}")

modules_to_test = [
    "gui_app_multi_sut",
    "main",
    "workflow_builder",
    "omniparser_queue_service",
    "modules.annotator",
    "modules.config_parser",
    "modules.decision_engine",
    "modules.game_launcher",
    "modules.gemma_client",
    "modules.network",
    "modules.omniparser_client",
    "modules.qwen_client",
    "modules.screenshot",
    "modules.simple_automation",
    "modules.simple_config_parser",
    # "sut_service_installer.gemma_service_0.2" # Might fail due to pywinauto dependency on host
]

failed_modules = []

print("\n--- Starting Import Sanity Check ---\n")

for module_name in modules_to_test:
    try:
        print(f"Testing import: {module_name}...", end=" ")
        importlib.import_module(module_name)
        print("OK")
    except Exception as e:
        print("FAIL")
        print(f"  Error: {e}")
        # traceback.print_exc()
        failed_modules.append(module_name)

print("\n--- Summary ---\n")
if failed_modules:
    print(f"Found {len(failed_modules)} broken modules:")
    for m in failed_modules:
        print(f" - {m}")
    sys.exit(1)
else:
    print("All checks passed!")
    sys.exit(0)
