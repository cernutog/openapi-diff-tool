import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_variables(self):
        return self.config.get('variables', {})

    def set_variable(self, key, value):
        if 'variables' not in self.config:
            self.config['variables'] = {}
        self.config['variables'][key] = value
        self.save_config()

    def delete_variable(self, key):
        if 'variables' in self.config and key in self.config['variables']:
            del self.config['variables'][key]
            self.save_config()

    def get_debug_mode(self):
        return self.config.get('debug_mode', False)

    def set_debug_mode(self, enabled):
        self.config['debug_mode'] = enabled
        self.save_config()

    def get_all_variables(self):
        return self.config.get('variables', {})
