from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'paths': {},
    'components': {
        'schemas': {
            'Parent': {
                'type': 'object',
                'properties': {
                    'child': {'$ref': '#/components/schemas/OldChild'}
                }
            },
            'OldChild': {'type': 'string'}
        }
    }
}

spec2 = {
    'openapi': '3.0.0',
    'paths': {},
    'components': {
        'schemas': {
            'Parent': {
                'type': 'object',
                'properties': {
                    'child': {'$ref': '#/components/schemas/NewChild'} # Ref changed
                }
            },
            'NewChild': {'type': 'string'} # Renamed
        }
    }
}

diff = compare_specs(spec1, spec2)

print("New Schemas:", diff.new_components.get('schemas'))
print("Removed Schemas:", diff.removed_components.get('schemas'))
print("Renamed Schemas:", diff.renamed_components.get('schemas'))
