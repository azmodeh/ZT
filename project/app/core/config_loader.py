from typing import Dict, Any
import yaml
import os

class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path

    def load_config(self) -> Dict[str, Any]:
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)

    def get_env_var(self, var_name: str) -> str:
        return os.getenv(var_name, "")

    def save_config(self, config: Dict[str, Any]) -> None:
        with open(self.config_path, 'w') as file:
            yaml.safe_dump(config, file)
