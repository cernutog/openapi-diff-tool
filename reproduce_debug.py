import yaml
import sys
import os
import json

# Add current directory to path to import comparator
sys.path.append(os.getcwd())

from comparator import compare_specs

def load_yaml(path):
    print(f"Loading {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run_debug():
    try:
        old_spec = load_yaml('debug_old_spec.yaml')
        new_spec = load_yaml('debug_new_spec.yaml')
        
        print("Running comparison...")
        result = compare_specs(old_spec, new_spec)
        
        print("\n--- Comparison Result ---")
        
        # Check diff for AccountIdentification4Choice
        s_name = 'AccountIdentification4Choice_EPC259-22_V3.0_DS08N'
        if s_name in result.modified_components.get('schemas', {}):
            print(f"Diff for {s_name}:")
            print(json.dumps(result.modified_components['schemas'][s_name], indent=2))
        else:
            print(f"{s_name} not found in modified components.")

        # Check specific schemas in renames
        target_schemas = [
            'GenericAccountIdentification1_EPC259-22_V3.0_DS02_Wrapper',
            'AccountSchemeName1Choice_EPC259-22_V3.0_DS02',
            'ExternalPersonIdentification1Code_EPC259-22_V3.0_DS02_Wrapper'
        ]
        
        renames = result.renamed_components.get('schemas', {})
        
        print("\n--- Rename Check ---")
        for s in target_schemas:
            if s in renames:
                print(f"[YES] {s} -> {renames[s]}")
            else:
                print(f"[NO] {s} NOT in renames")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()
