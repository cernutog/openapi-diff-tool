from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'paths': {},
    'components': {
        'schemas': {
            'PaymentTransaction_V3': {'type': 'object'},
            'Unrelated': {'type': 'string'}
        }
    }
}

spec2 = {
    'openapi': '3.0.0',
    'paths': {},
    'components': {
        'schemas': {
            'PaymentTransaction_V4': {'type': 'object'}, # Should match V3
            'UnrelatedNew': {'type': 'integer'}
        }
    }
}

diff = compare_specs(spec1, spec2)

print("Renamed Schemas:", diff.renamed_components.get('schemas'))
print("New Schemas:", diff.new_components.get('schemas'))
print("Removed Schemas:", diff.removed_components.get('schemas'))
