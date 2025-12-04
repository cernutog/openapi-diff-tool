import sys
import os
import yaml
from comparator import load_yaml, _compare_schema

def _get_schema(spec, name):
    return spec.get('components', {}).get('schemas', {}).get(name)

def debug_diff():
    old_path = "debug_old_spec.yaml"
    new_path = "debug_new_spec.yaml"
    
    if not os.path.exists(old_path) or not os.path.exists(new_path):
        print("Debug specs not found.")
        return

    print(f"Loading {old_path}...")
    old_spec = load_yaml(old_path)
    print(f"Loading {new_path}...")
    new_spec = load_yaml(new_path)

    target_name = "ExternalStatusReason1Code"
    
    # Try to find it in old spec
    old_def = _get_schema(old_spec, target_name)
    if not old_def:
        print(f"Schema {target_name} not found in old spec.")
        return

    # Try to find it in new spec (assuming same name or renamed)
    # In the report it appeared as modified, so it must exist.
    # Let's check candidates or just look for same name
    new_def = _get_schema(new_spec, target_name)
    
    if not new_def:
        print(f"Schema {target_name} not found in new spec (might be renamed).")
        # Try to find if it was renamed? 
        # For this debug, let's assume it kept the name or we can find it.
        return

    print(f"Comparing {target_name}...")
    diff = _compare_schema(old_def, new_def)
    print("Diff result:")
    import json
    print(json.dumps(diff, indent=2, default=str))

if __name__ == "__main__":
    debug_diff()
