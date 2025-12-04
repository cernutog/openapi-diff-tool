
def filter_diff(diff, renamed_schemas):
    """
    Simulates the filtering logic for the report.
    Removes changes that are just $ref updates matching a rename.
    """
    import copy
    filtered_diff = copy.deepcopy(diff)
    
    modified_schemas = filtered_diff.get('modified_components', {}).get('schemas', {})
    schemas_to_remove = []

    for s_name, changes in modified_schemas.items():
        # We only care about filtering 'properties' for now, or direct $ref changes
        if 'properties' in changes and 'modified' in changes['properties']:
            props_mod = changes['properties']['modified']
            props_to_remove = []
            
            for prop, p_diff in props_mod.items():
                # Check for $ref change
                # Structure could be: {'$ref': {'old': '#/components/schemas/Old', 'new': '#/components/schemas/New'}}
                # Or inside items, etc.
                
                ref_change = None
                if '$ref' in p_diff:
                    ref_change = p_diff['$ref']
                elif 'items' in p_diff and '$ref' in p_diff['items']: # Array of refs
                     ref_change = p_diff['items']['$ref']
                
                if ref_change:
                    old_ref = ref_change.get('old', '')
                    new_ref = ref_change.get('new', '')
                    
                    # Extract simple names
                    old_simple = old_ref.split('/')[-1]
                    new_simple = new_ref.split('/')[-1]
                    
                    # Check if this is a known rename
                    if old_simple in renamed_schemas and renamed_schemas[old_simple] == new_simple:
                        # This is a rename-induced change. Filter it out.
                        props_to_remove.append(prop)
            
            # Remove filtered properties
            for p in props_to_remove:
                del props_mod[p]
            
            # If 'modified' is now empty, remove it
            if not props_mod:
                del changes['properties']['modified']
                if not changes['properties']: # If properties is empty
                    del changes['properties']

        # Check if there are any changes left
        if not changes:
            schemas_to_remove.append(s_name)
    
    # Remove schemas that are now empty
    for s in schemas_to_remove:
        del modified_schemas[s]
        
    return filtered_diff

# Mock Data
mock_renames = {
    'OldSchemaA': 'NewSchemaA',
    'OldSchemaB': 'NewSchemaB'
}

mock_diff = {
    'modified_components': {
        'schemas': {
            'ContainerSchema': {
                'properties': {
                    'modified': {
                        'prop1': {
                            '$ref': {'old': '#/components/schemas/OldSchemaA', 'new': '#/components/schemas/NewSchemaA'}
                        },
                        'prop2': {
                            'type': {'old': 'string', 'new': 'integer'} # Real change
                        }
                    }
                }
            },
            'PureRefChangeSchema': {
                'properties': {
                    'modified': {
                        'prop1': {
                            '$ref': {'old': '#/components/schemas/OldSchemaB', 'new': '#/components/schemas/NewSchemaB'}
                        }
                    }
                }
            }
        }
    }
}

print("Original Diff:")
import json
print(json.dumps(mock_diff, indent=2))

filtered = filter_diff(mock_diff, mock_renames)

print("\nFiltered Diff:")
print(json.dumps(filtered, indent=2))
