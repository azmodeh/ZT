from typing import Dict, Any
import json

class ReportGenerator:
    def __init__(self):
        pass

    def generate_report(self, violations: Dict[str, Any]) -> str:
        report = {
            "violations": violations,
            "summary": self.generate_summary(violations)
        }
        return json.dumps(report, indent=4)

    def generate_summary(self, violations: Dict[str, Any]) -> Dict[str, Any]:
        summary = {
            "total_violations": len(violations),
            "violation_types": list(violations.keys())
        }
        return summary
