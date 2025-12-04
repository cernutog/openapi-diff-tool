from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'paths': {
        '/users': {
            'get': {
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/UserOld'}
                            }
                        }
                    }
                }
            }
        }
    },
    'components': {
        'schemas': {
            'UserOld': {'type': 'object', 'properties': {'id': {'type': 'integer'}}}
        }
    }
}

spec2 = {
    'openapi': '3.0.0',
    'paths': {
        '/users': {
            'get': {
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/UserNew'} # Changed Ref
                            }
                        }
                    }
                }
            }
        }
    },
    'components': {
        'schemas': {
            'UserNew': {'type': 'object', 'properties': {'id': {'type': 'integer'}}} # New Name
        }
    }
}

diff = compare_specs(spec1, spec2)

print("New Schemas:", diff.new_components.get('schemas'))
print("Removed Schemas:", diff.removed_components.get('schemas'))
print("Renamed Schemas:", diff.renamed_components.get('schemas'))
