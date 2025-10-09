import yaml
from pathlib import Path


class ConfigLoader:
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent.parent / "data" / "config"
    
    def load_yaml(self, filename: str) -> dict:
        """Load YAML configuration file."""
        file_path = self.config_dir / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_env_var(self, key: str, default: str = "") -> str:
        """Get environment variable."""
        import os
        return os.getenv(key, default)
