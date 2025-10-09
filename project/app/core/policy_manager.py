from typing import Dict, Any
import yaml
import logging

class PolicyManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.policies = self.load_policies()

    def load_policies(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"Policy file not found: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            logging.error(f"Error parsing policy file: {e}")
            return {}

    def get_policy(self, policy_name: str) -> Dict[str, Any]:
        return self.policies.get(policy_name, {})

    def add_policy(self, policy_name: str, policy: Dict[str, Any]):
        self.policies[policy_name] = policy
        self.save_policies()

    def save_policies(self):
        try:
            with open(self.config_path, 'w') as file:
                yaml.safe_dump(self.policies, file)
        except IOError as e:
            logging.error(f"Error saving policies: {e}")
