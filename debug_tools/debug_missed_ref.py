from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'paths': {},
    'components': {
        'schemas': {
            'ParentArray': {
                'type': 'array',
                'items': {'$ref': '#/components/schemas/OldItem'}
            },
            'ParentAllOf': {
                'allOf': [
                    {'$ref': '#/components/schemas/OldMixin'}
                ]
            },
            'OldItem': {'type': 'string'},
            'OldMixin': {'type': 'object'}
        }
    }
}

spec2 = {
    'openapi': '3.0.0',
    'paths': {},
    'components': {
        'schemas': {
            'ParentArray': {
                'type': 'array',
                'items': {'$ref': '#/components/schemas/NewItem'} # Changed in items
            },
            'ParentAllOf': {
                'allOf': [
                    {'$ref': '#/components/schemas/NewMixin'} # Changed in allOf
                ]
            },
            'NewItem': {'type': 'string'},
            'NewMixin': {'type': 'object'}
        }
    }
}

diff = compare_specs(spec1, spec2)

print("Renamed Schemas:", diff.renamed_components.get('schemas'))
