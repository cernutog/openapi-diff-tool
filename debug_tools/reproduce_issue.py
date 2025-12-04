from comparator import compare_specs

old_spec = {
    'openapi': '3.0.0',
    'paths': {
        '/test': {
            'get': {
                'responses': {
                    '200': {
                        'description': 'OK',
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/Parent'}
                            }
                        }
                    }
                }
            }
        }
    },
    'components': {
        'schemas': {
            'Parent': {
                'allOf': [
                    {'$ref': '#/components/schemas/ChildV1'}
                ]
            },
            'ChildV1': {
                'type': 'object',
                'properties': {
                    'prop': {'$ref': '#/components/schemas/GrandChildV1'}
                }
            },
            'GrandChildV1': {'type': 'string'}
        }
    }
}

new_spec = {
    'openapi': '3.0.0',
    'paths': {
        '/test': {
            'get': {
                'responses': {
                    '200': {
                        'description': 'OK',
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/Parent'}
                            }
                        }
                    }
                }
            }
        }
    },
    'components': {
        'schemas': {
            'Parent': {
                'allOf': [
                    {'$ref': '#/components/schemas/ChildV2'}
                ]
            },
            'ChildV2': {
                'type': 'object',
                'properties': {
                    'prop': {'$ref': '#/components/schemas/GrandChildV2'}
                }
            },
            'GrandChildV2': {'type': 'string'}
        }
    }
}

diff = compare_specs(old_spec, new_spec)

print(f"Renamed Schemas: {diff.renamed_components.get('schemas', {})}")
if 'ChildV1' in diff.renamed_components.get('schemas', {}) and \
   diff.renamed_components['schemas']['ChildV1'] == 'ChildV2':
    print("SUCCESS: ChildV1 -> ChildV2 detected!")
else:
    print("FAILURE: ChildV1 -> ChildV2 NOT detected.")

if 'GrandChildV1' in diff.renamed_components.get('schemas', {}) and \
   diff.renamed_components['schemas']['GrandChildV1'] == 'GrandChildV2':
    print("SUCCESS: GrandChildV1 -> GrandChildV2 detected!")
else:
    print("FAILURE: GrandChildV1 -> GrandChildV2 NOT detected.")
