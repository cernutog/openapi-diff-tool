from comparator import compare_specs

spec1 = {
    'openapi': '3.0.0',
    'info': {'title': 'Old', 'version': '1.0'},
    'paths': {},
    'components': {}
}

spec2 = {
    'openapi': '3.0.0',
    'info': {'title': 'New', 'version': '1.0'},
    'paths': {},
    'components': {}
}

diff = compare_specs(spec1, spec2)

print("Info Changes:", diff.info_changes)
