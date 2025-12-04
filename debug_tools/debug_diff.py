from comparator import compare_specs, load_yaml
import json

spec1 = load_yaml('data/complex_31_v1.yaml')
spec2 = load_yaml('data/complex_31_v2.yaml')
diff = compare_specs(spec1, spec2)

# Helper to serialize sets
class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

print(json.dumps(diff.__dict__, indent=2, cls=SetEncoder))
