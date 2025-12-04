from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'paths': {
        '/a': {
            'get': {
                'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Old'}}}}}
            }
        },
        '/b': {
            'get': {
                'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Old'}}}}}
            }
        }
    },
    'components': {
        'schemas': {
            'Old': {'type': 'string'}
        }
    }
}

spec2 = {
    'openapi': '3.0.0',
    'paths': {
        '/a': {
            'get': {
                'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/New1'}}}}}
            }
        },
        '/b': {
            'get': {
                'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/New2'}}}}}
            }
        }
    },
    'components': {
        'schemas': {
            'New1': {'type': 'string'},
            'New2': {'type': 'string'}
        }
    }
}

diff = compare_specs(spec1, spec2)

print("Renamed Schemas:", diff.renamed_components.get('schemas'))
print("Removed Schemas:", diff.removed_components.get('schemas'))
