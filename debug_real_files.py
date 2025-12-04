from comparator import compare_specs, load_yaml
import os

file1 = 'data/complex_31_v1.yaml'
file2 = 'data/complex_31_v2.yaml'

if not os.path.exists(file1) or not os.path.exists(file2):
    print(f"Files not found: {file1}, {file2}")
else:
    spec1 = load_yaml(file1)
    spec2 = load_yaml(file2)
    
    diff = compare_specs(spec1, spec2)
    
    print(f"Info Changes: {len(diff.info_changes)}")
    print(f"New Paths: {len(diff.new_paths)}")
    print(f"Modified Paths: {len(diff.modified_paths)}")
    print(f"New Schemas: {len(diff.new_components.get('schemas', []))}")
    print(f"Removed Schemas: {len(diff.removed_components.get('schemas', []))}")
    print(f"Modified Schemas: {len(diff.modified_components.get('schemas', {}))}")
    print(f"Renamed Schemas: {len(diff.renamed_components.get('schemas', {}))}")
    
    if 'schemas' in diff.modified_components:
        print("\nModified Schemas Details:")
        for name, d in diff.modified_components['schemas'].items():
            print(f"Schema: {name}")
            print(f"Diff: {d}")
