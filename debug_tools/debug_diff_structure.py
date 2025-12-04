from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'components': {
        'schemas': {
            'Parent': {
                'type': 'object',
                'properties': {
                    'child': {'$ref': '#/components/schemas/ChildV1'}
                }
            },
            'ChildV1': {'type': 'string'}
        }
    }
}

spec2 = {
    'openapi': '3.0.0',
    'components': {
        'schemas': {
            'Parent': {
                'type': 'object',
                'properties': {
                    'child': {'$ref': '#/components/schemas/ChildV2'}
                }
            },
            'ChildV2': {'type': 'string'}
        }
    }
}

diff = compare_specs(spec1, spec2)

print("Modified Components Keys:", diff.modified_components.keys())
if 'schemas' in diff.modified_components:
    parent_diff = diff.modified_components['schemas']['Parent']
    print("Parent Diff:", parent_diff)
