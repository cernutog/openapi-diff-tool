
from comparator import compare_specs
import json

spec1 = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {},
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "description": "Old description",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Old prop description"
                    }
                }
            }
        }
    }
}

spec2 = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {},
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "description": "New description",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "New prop description"
                    }
                }
            }
        }
    }
}

diff = compare_specs(spec1, spec2)
print("Modified Components:")
print(json.dumps(diff.modified_components, indent=2))
