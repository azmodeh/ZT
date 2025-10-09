import yaml
from pathlib import Path


class ConfigLoader:
    def __init__(self):
        # The config directory is relative to the project root (2 levels up from core)
        # Project structure: project/app/core/config_loader.py -> project/data/config/
        project_root = Path(__file__).parent.parent.parent
        self.config_dir = project_root.parent / "data" / "config"
        if not self.config_dir.exists():
            # Fallback to relative path from current working directory
            self.config_dir = Path("data") / "config"
    
    def load_yaml(self, filename: str) -> dict:
        """Load YAML configuration file."""
        file_path = self.config_dir / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_env_var(self, key: str, default: str = "") -> str:
        """Get environment variable."""
        import os
        return os.getenv(key, default)
