from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'paths': {
        '/api': {
            'get': {
                'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ParentV3'}}}}}
            }
        }
    },
    'components': {
        'schemas': {
            'ParentV3': {
                'type': 'object',
                'properties': {
                    'child': {'$ref': '#/components/schemas/ChildV3'}
                }
            },
            'ChildV3': {'type': 'string'}
        }
    }
}

spec2 = {
    'openapi': '3.0.0',
    'paths': {
        '/api': {
            'get': {
                'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ParentV4'}}}}}
            }
        }
    },
    'components': {
        'schemas': {
            'ParentV4': {
                'type': 'object',
                'properties': {
                    'child': {'$ref': '#/components/schemas/ChildV4'}
                }
            },
            'ChildV4': {'type': 'string'}
        }
    }
}

diff = compare_specs(spec1, spec2)

print("Renamed Schemas:", diff.renamed_components.get('schemas'))
