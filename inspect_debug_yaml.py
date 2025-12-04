import yaml
import json
import sys

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def inspect_wrappers():
    try:
        old_spec = load_yaml('debug_old_spec.yaml')
        new_spec = load_yaml('debug_new_spec.yaml')
        
        old_name = 'AccountIdentification4Choice_EPC259-22_V3.0_DS08N'
        new_name = 'AccountIdentification4Choice_EPC259-22_V4.0_DS08N'
        
        print(f"--- {old_name} (OLD) ---")
        old_schema = old_spec['components']['schemas'].get(old_name)
        if old_schema:
            print(json.dumps(old_schema, indent=2))
        else:
            print("NOT FOUND")
        
        print(f"\n--- {new_name} (NEW) ---")
        new_schema = new_spec['components']['schemas'].get(new_name)
        if new_schema:
            print(json.dumps(new_schema, indent=2))
        else:
            print("NOT FOUND")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    inspect_wrappers()
