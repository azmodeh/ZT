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
from mcp.types import CallToolResult, TextContent, Tool, Argument


logger = logging.getLogger(__name__)
server = Server()


def load_contract_rules() -> Dict[str, Any]:
    """Load contract rules from YAML configuration"""
    from enforcement.utils import load_contract_rules as _load_rules
    return _load_rules()


def run_validation(base_path: str) -> Dict[str, Any]:
    """Run contract validation over codebase"""
    from enforcement.validator import Validator
    rules = load_contract_rules()
    from enforcement.utils import ProjectPaths
    paths = ProjectPaths(Path(base_path), rules.get("include_globs", []), rules.get("exclude_globs", []))
    validator = Validator(rules, paths)
    report = validator.run()
    return report.to_dict()


def run_fixer(base_path: str) -> Dict[str, Any]:
    """Run auto-fixer on codebase"""
    from enforcement.rewriter import AutoRewriter
    from enforcement.utils import ProjectPaths
    rules = load_contract_rules()
    paths = ProjectPaths(Path(base_path), rules.get("include_globs", []), rules.get("exclude_globs", []))
    rewriter = AutoRewriter(paths)
    outcomes = rewriter.execute()
    
    results = []
    for outcome in outcomes:
        results.append({
            "path": str(outcome.path),
            "replaced_prints": outcome.replaced_prints,
            "wrapped_lines": outcome.wrapped_lines,
            "added_logger": outcome.added_logger
        })
    
    return {"fixed_files": results, "total_files": len(outcomes)}


def generate_self_assessment(base_path: str) -> Dict[str, Any]:
    """Generate self-assessment report"""
    from enforcement.report_generator import store_report
    report = run_validation(base_path)
    assessment = {
        "total_files": report.get("files_scanned", 0),
        "total_rules": report.get("rules_evaluated", 0),
        "total_violations": report.get("violations_total", 0),
        "compliance_score": report.get("compliance_score", 0),
        "violations_by_file": report.get("violations_by_file", {}),
        "status": "PASS" if report.get("violations_total", 0) == 0 else "FAIL"
    }
    store_report(assessment)
    return assessment


# MCP Tools
@server.tool(
    name="validate_code",
    description="Validate Python codebase against Zero Tolerance contract rules",
    arguments=[
        Argument(name="base_path", type="string", description="Path to the codebase to validate")
    ]
)
def handle_validate_code(base_path: str) -> CallToolResult:
    """Handle validate_code tool call"""
    try:
        result = run_validation(base_path)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        )
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        )


@server.tool(
    name="fix_violations",
    description="Auto-fix contract violations in Python codebase",
    arguments=[
        Argument(name="base_path", type="string", description="Path to the codebase to fix")
    ]
)
def handle_fix_violations(base_path: str) -> CallToolResult:
    """Handle fix_violations tool call"""
    try:
        result = run_fixer(base_path)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        )
    except Exception as e:
        logger.error(f"Fixer error: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        )


@server.tool(
    name="generate_self_assessment",
    description="Generate self-assessment report for contract compliance",
    arguments=[
        Argument(name="base_path", type="string", description="Path to the codebase to assess")
    ]
)
def handle_generate_self_assessment(base_path: str) -> CallToolResult:
    """Handle generate_self_assessment tool call"""
    try:
        result = generate_self_assessment(base_path)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        )
    except Exception as e:
        logger.error(f"Assessment error: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        )


@server.tool(
    name="check_compliance",
    description="Check overall compliance status of a codebase",
    arguments=[
        Argument(name="base_path", type="string", description="Path to the codebase to check")
    ]
)
def handle_check_compliance(base_path: str) -> CallToolResult:
    """Handle check_compliance tool call"""
    try:
        result = run_validation(base_path)
        score = result.get("compliance_score", 0)
        status = "PASS" if result.get("violations_total", 0) == 0 else "FAIL"
        
        compliance_report = {
            "status": status,
            "compliance_score": score,
            "total_violations": result.get("violations_total", 0),
            "files_scanned": result.get("files_scanned", 0)
        }
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(compliance_report, indent=2)
            )]
        )
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        )


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, None)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
