"""
Basic tests for Zero Tolerance System
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from enforcement.validator_engine import ValidatorEngine
from enforcement.utils import get_logger


def test_validator_engine_initialization():
    """Test that ValidatorEngine can be initialized."""
    validator = ValidatorEngine()
    assert validator is not None
    assert hasattr(validator, 'rules')
    assert hasattr(validator, 'patterns')


def test_logger_creation():
    """Test that logger can be created."""
    logger = get_logger("test")
    assert logger is not None
    assert logger.name == "test"


def test_validator_engine_rules_loading():
    """Test that rules are loaded properly."""
    validator = ValidatorEngine()
    assert isinstance(validator.rules, dict)
    assert len(validator.rules) > 0


def test_basic_validation():
    """Test basic file validation."""
    validator = ValidatorEngine()
    
    # Test with simple valid Python code
    test_code = '''def hello_world() -> str:
    """A simple function."""
    return "Hello, World!"
'''
    
    result = validator.validate_content(test_code, "test.py", "python")
    assert result is not None
    assert hasattr(result, 'violations')
    assert hasattr(result, 'execution_time')


def test_contract_rules_detection():
    """Test that contract rules can detect violations."""
    validator = ValidatorEngine()
    
    # Code with print statement (should violate rules)
    bad_code = '''def bad_function():
    print("This should be detected")
    return None
'''
    
    result = validator.validate_content(bad_code, "bad.py", "python")
    # Should detect print statement violation
    has_print_violation = any(v.rule_id == "no_print" for v in result.violations)
    assert has_print_violation, "Should detect print statement violation"


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running Zero Tolerance Basic Tests...")
    
    try:
        test_validator_engine_initialization()
        print("✅ ValidatorEngine initialization - PASS")
        
        test_logger_creation()
        print("✅ Logger creation - PASS")
        
        test_validator_engine_rules_loading()
        print("✅ Rules loading - PASS")
        
        test_basic_validation()
        print("✅ Basic validation - PASS")
        
        test_contract_rules_detection()
        print("✅ Contract rules detection - PASS")
        
        print("\n🎉 All basic tests PASSED!")
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        sys.exit(1)
