"""
Zero Tolerance Python Contract Enforcer
Main Application Runner
"""

import sys
from pathlib import Path

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config_loader import ConfigLoader
from app.core.logger import get_logger


def run_application():
    """
    Main entry point for the Zero Tolerance Python Contract Enforcer application.
    """
    logger = get_logger(__name__)
    
    try:
        # Initialize configuration
        config_loader = ConfigLoader()
        logger.info("messages.app_started")
        
        # Load application settings
        settings = config_loader.load_yaml("settings.yml")
        
        # Validate configuration
        required_keys = ["main_max_lines", "no_print", "type_hints_required", "max_file_lines"]
        for key in required_keys:
            if key not in settings:
                logger.error(f"messages.missing_config_key", extra={"key": key})
                raise ValueError(f"Missing required configuration key: {key}")
        
        logger.info("messages.config_loaded_successfully")
        
        # Run the enforcement system
        run_enforcement_system()
        
        logger.info("messages.app_completed_successfully")
        
    except Exception as e:
        logger.error("messages.app_error_occurred", extra={"error": str(e)})
        raise


def run_enforcement_system():
    """
    Execute the main enforcement logic.
    """
    from enforcement.validator import Validator
    from enforcement.utils import ProjectPaths, load_contract_rules
    
    logger = get_logger(__name__)
    
    try:
        # Load contract rules
        rules = load_contract_rules()
        logger.info("messages.rules_loaded")
        
        # Setup project paths
        project_paths = ProjectPaths(
            base=Path(PROJECT_ROOT) / "project",
            includes=rules.get("include_globs", ["**/*.py"]),
            excludes=rules.get("exclude_globs", ["enforcement/**", "data/**", "logs/**"])
        )
        
        # Create and run validator
        validator = Validator(rules, project_paths)
        report = validator.run()
        
        logger.info("messages.validation_completed", extra={
            "files_scanned": report.files_scanned,
            "total_violations": report.total_violations,
            "compliance_score": report.compliance_score()
        })
        
        # Check if we need to run auto-fixer
        if report.total_violations > 0:
            from enforcement.rewriter import AutoRewriter
            rewriter = AutoRewriter(project_paths)
            outcomes = rewriter.execute()
            
            logger.info("messages.auto_fix_completed", extra={
                "files_changed": len(outcomes)
            })
            
            # Run validation again to confirm fixes
            report_after_fix = validator.run()
            logger.info("messages.validation_after_fix", extra={
                "files_scanned": report_after_fix.files_scanned,
                "total_violations": report_after_fix.total_violations,
                "compliance_score": report_after_fix.compliance_score()
            })
        
        # Generate self-assessment report
        from enforcement.report_generator import store_report
        report_data = report.to_dict()
        store_report(report_data)
        logger.info("messages.report_stored")
        
    except Exception as e:
        logger.error("messages.enforcement_error", extra={"error": str(e)})
        raise


if __name__ == "__main__":
    run_application()
