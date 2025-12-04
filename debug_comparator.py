from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'components': {
        'schemas': {
            'OldSchema': {'type': 'string'},
            'ModifiedSchema': {'type': 'integer'}
        }
    }
}

spec2 = {
    'openapi': '3.0.0',
    'components': {
        'schemas': {
            'NewSchema': {'type': 'string'},
            'ModifiedSchema': {'type': 'string'} # Changed type
        }
    }
}

diff = compare_specs(spec1, spec2)

print("New Schemas:", diff.new_components.get('schemas'))
print("Removed Schemas:", diff.removed_components.get('schemas'))
print("Modified Schemas:", diff.modified_components.get('schemas'))
