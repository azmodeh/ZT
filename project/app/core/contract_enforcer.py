import logging
logger = logging.getLogger(__name__)
from app.core.policy_manager import PolicyManager
from app.classes.violation_detector import ViolationDetector
from app.classes.enforcement_actions import EnforcementActions
from app.classes.report_generator import ReportGenerator
from app.core.config_loader import ConfigLoader
from enforcement.ai_agent import main as ai_agent_main
from enforcement.utils import get_logger, emit_ui_message
import asyncio

logger = get_logger(__name__)


class ContractEnforcer:
    def __init__(self, config_path: str):
        self.config_loader = ConfigLoader(config_path)
        self.policy_manager = PolicyManager(config_path)
        self.violation_detector = ViolationDetector(self.policy_manager)
        self.enforcement_actions = EnforcementActions()
        self.report_generator = ReportGenerator()


def run(self) -> None:
    config = self.config_loader.load_config()
    logger.info("Starting contract enforcement")

    # Example code to test
    code = """
    def example_function():
        logger.info("This is an example function")
    """

    # Detect violations
    violations = self.violation_detector.detect_violations(code)

    # Handle large codebases efficiently
    if len(violations) > 100:
        logger.warning("Large number of violations detected: %d", \
        len(violations))

    # Execute enforcement actions
    for violation in violations.values():
        self.enforcement_actions.execute_action(violation)

    # Generate report
    report = self.report_generator.generate_report(violations)
    logger.info("Contract enforcement report: %s", report)

    # Run AI agent
    asyncio.run(self.run_ai_agent())

async def run_ai_agent(self) -> None:
    try:
        await ai_agent_main()
    except Exception as e:
        logger.error("AI agent encountered an error: %s", e)
        emit_ui_message(f"خطا در اجرای عامل هوش مصنوعی: {e}")


if __name__ == "__main__":
    enforcer = ContractEnforcer("data/config/settings.yml")
    asyncio.run(enforcer.run())
