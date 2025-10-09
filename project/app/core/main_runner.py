from app.core.policy_manager import PolicyManager
from app.classes.violation_detector import ViolationDetector
from app.classes.enforcement_actions import EnforcementActions
from app.classes.report_generator import ReportGenerator

def run_application():
    config_path = "data/config/settings.yml"
    policy_manager = PolicyManager(config_path)
    violation_detector = ViolationDetector(policy_manager)
    enforcement_actions = EnforcementActions()
    report_generator = ReportGenerator()

    # Example code to test
    code = """
    def example_function():
        print("This is an example function")
    """

    # Detect violations
    violations = violation_detector.detect_violations(code)

    # Execute enforcement actions
    for violation in violations.values():
        enforcement_actions.execute_action(violation)

    # Generate report
    report = report_generator.generate_report(violations)
    print(report)

if __name__ == "__main__":
    run_application()
