#!/usr/bin/env python3
"""
Zero Tolerance Python Contract Enforcer MCP Server
Provides validation tools as MCP services
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from mcp.server import Server
from mcp.types import (
    CallToolResult,
    TextContent,
    ReadResourceResult,
    TextResourceContents,
)


logger = logging.getLogger(__name__)
server = Server("zero-tolerance-contract-enforcer")


def load_contract_rules() -> Dict[str, Any]:
    """Load contract rules from YAML configuration"""
    from enforcement.utils import load_contract_rules as _load_rules

    return _load_rules()


def run_validation(base_path: str) -> Dict[str, Any]:
    """Run contract validation over codebase"""
    from enforcement.validator import Validator

    rules = load_contract_rules()
    from enforcement.utils import ProjectPaths

    paths = ProjectPaths(
        Path(base_path), rules.get("include_globs", []), rules.get("exclude_globs", [])
    )
    validator = Validator(rules, paths)
    report = validator.run()
    return report.to_dict()


def run_fixer(base_path: str) -> Dict[str, Any]:
    """Run auto-fixer on codebase"""
    from enforcement.rewriter import AutoRewriter
    from enforcement.utils import ProjectPaths

    rules = load_contract_rules()
    paths = ProjectPaths(
        Path(base_path), rules.get("include_globs", []), rules.get("exclude_globs", [])
    )
    rewriter = AutoRewriter(paths)
    outcomes = rewriter.execute()

    results = []
    for outcome in outcomes:
        results.append(
            {
                "path": str(outcome.path),
                "replaced_prints": outcome.replaced_prints,
                "wrapped_lines": outcome.wrapped_lines,
                "added_logger": outcome.added_logger,
            }
        )

    return {"fixed_files": results, "total_files": len(outcomes)}


def generate_self_assessment_report(base_path: str) -> Dict[str, Any]:
    """Generate self-assessment report"""
    from enforcement.report_generator import store_report

    report = run_validation(base_path)
    assessment = {
        "total_files": report.get("files_scanned", 0),
        "total_rules": report.get("rules_evaluated", 0),
        "total_violations": report.get("violations_total", 0),
        "compliance_score": report.get("compliance_score", 0),
        "violations_by_file": report.get("violations_by_file", {}),
        "status": "PASS" if report.get("violations_total", 0) == 0 else "FAIL",
    }
    store_report(assessment)
    return assessment


def get_latest_validation_report() -> Dict[str, Any]:
    """Get the latest validation report from logs."""
    from enforcement.report_generator import load_latest_report

    try:
        report = load_latest_report()
        return report if report is not None else {}
    except Exception as e:
        logger.error(f"Error loading latest report: {e}")
        return {}


def get_validation_history() -> List[Dict[str, Any]]:
    """Get validation history from logs."""
    import json
    from pathlib import Path

    logs_dir = Path("logs")
    history = []

    for log_file in logs_dir.glob("validation_*.json"):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                report = json.load(f)
                history.append(report)
        except Exception:
            continue

    return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)


# MCP Tools - Register using the standard decorator pattern if available
# Otherwise, we'll register them in the main function
async def validate_code(base_path: str) -> CallToolResult:
    """Validate Python codebase against Zero Tolerance contract rules"""
    try:
        result = run_validation(base_path)
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def fix_violations(base_path: str) -> CallToolResult:
    """Auto-fix contract violations in Python codebase"""
    try:
        result = run_fixer(base_path)
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    except Exception as e:
        logger.error(f"Fixer error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def generate_self_assessment(base_path: str) -> CallToolResult:
    """Generate self-assessment report for contract compliance"""
    try:
        result = generate_self_assessment_report(base_path)
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    except Exception as e:
        logger.error(f"Assessment error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def check_compliance(base_path: str) -> CallToolResult:
    """Check overall compliance status of a codebase"""
    try:
        result = run_validation(base_path)
        score = result.get("compliance_score", 0)
        status = "PASS" if result.get("violations_total", 0) == 0 else "FAIL"

        compliance_report = {
            "status": status,
            "compliance_score": score,
            "total_violations": result.get("violations_total", 0),
            "files_scanned": result.get("files_scanned", 0),
        }

        return CallToolResult(
            content=[
                TextContent(type="text", text=json.dumps(compliance_report, indent=2))
            ]
        )
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


# MCP Resources
async def read_resource(uri: str) -> ReadResourceResult:
    """Handle reading resources."""
    try:
        if uri == "validation://latest-report":
            report = get_latest_validation_report()
            content = json.dumps(report, indent=2)
        elif uri == "validation://history":
            history = get_validation_history()
            content = json.dumps(history, indent=2)
        elif uri == "validation://compliance-status":
            from enforcement.validator import Validator
            from enforcement.utils import load_contract_rules, ProjectPaths

            rules = load_contract_rules()
            paths = ProjectPaths(
                Path("."),
                rules.get("include_globs", []),
                rules.get("exclude_globs", []),
            )
            validator = Validator(rules, paths)
            report = validator.run()
            status = {
                "status": "PASS" if report.total_violations == 0 else "FAIL",
                "compliance_score": report.compliance_score(),
                "total_violations": report.total_violations,
                "files_scanned": report.files_scanned,
            }
            content = json.dumps(status, indent=2)
        else:
            content = json.dumps({"error": f"Unknown resource: {uri}"})

        from pydantic import AnyUrl, ValidationError
        from pydantic.type_adapter import TypeAdapter

        try:
            uri_anyurl = TypeAdapter(AnyUrl).validate_python(uri)
        except ValidationError:
            # fallback to HttpUrl if AnyUrl fails, or set to a default valid URL
            uri_anyurl = TypeAdapter(AnyUrl).validate_python("file://" + uri)
        return ReadResourceResult(
            contents=[TextResourceContents(uri=uri_anyurl, text=content)]
        )
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        from pydantic import AnyUrl, ValidationError
        from pydantic.type_adapter import TypeAdapter

        try:
            error_uri = TypeAdapter(AnyUrl).validate_python("file://error")
        except ValidationError:
            error_uri = TypeAdapter(AnyUrl).validate_python("file:///error")
        return ReadResourceResult(
            contents=[TextResourceContents(uri=error_uri, text=f"Error: {str(e)}")]
        )


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    from mcp.types import ServerCapabilities
    from mcp.server import InitializationOptions


    # Set up the server's internal state for tools and resources
    # Since we can't access the internal attributes, we'll use the server's public API
    # The tools and resources should be registered during server initialization
    # by decorating the functions or using the server's registration methods

    async with stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="zero-tolerance-contract-enforcer",
            server_version="1.0",
            capabilities=ServerCapabilities()
        )
        await server.run(read_stream, write_stream, initialization_options=init_options)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
