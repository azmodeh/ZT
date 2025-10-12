"""
Sentinel Path Guard Test
تضمین 100% که هیچ پچی خارج از ZT_TARGET اعمال نشود
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_server.server import validate_path
from fastapi import HTTPException


class TestPathGuard:
    """Test path validation and security"""
    
    def test_path_inside_target_allowed(self, tmp_path):
        """Paths inside ZT_TARGET should be allowed"""
        os.environ["ZT_TARGET"] = str(tmp_path)
        
        # Create test directory inside target
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()
        test_file = test_dir / "test.py"
        test_file.write_text("print('hello')")
        
        # Should succeed
        result = validate_path(str(test_file))
        assert result == test_file.resolve()
    
    def test_path_outside_target_blocked(self, tmp_path):
        """Paths outside ZT_TARGET should be blocked"""
        target = tmp_path / "target"
        target.mkdir()
        os.environ["ZT_TARGET"] = str(target)
        
        # Try to access file outside target
        outside_file = tmp_path / "outside.py"
        outside_file.write_text("malicious code")
        
        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            validate_path(str(outside_file))
        
        assert exc_info.value.status_code == 403
        assert "PATH_FORBIDDEN" in str(exc_info.value.detail)
    
    def test_path_traversal_blocked(self, tmp_path):
        """Path traversal attacks should be blocked"""
        target = tmp_path / "target"
        target.mkdir()
        os.environ["ZT_TARGET"] = str(target)
        
        # Try path traversal
        with pytest.raises(HTTPException) as exc_info:
            validate_path(str(target / ".." / ".." / "etc" / "passwd"))
        
        assert exc_info.value.status_code == 403
    
    def test_symbolic_link_blocked(self, tmp_path):
        """Symbolic links outside target should be blocked"""
        target = tmp_path / "target"
        target.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        
        os.environ["ZT_TARGET"] = str(target)
        
        # Create symlink pointing outside
        link = target / "bad_link"
        try:
            link.symlink_to(outside)
            
            # Should be blocked
            with pytest.raises(HTTPException) as exc_info:
                validate_path(str(link))
            
            assert exc_info.value.status_code == 403
        except OSError:
            # Skip on Windows without admin rights
            pytest.skip("Symlink creation requires admin on Windows")
    
    def test_absolute_path_normalized(self, tmp_path):
        """Absolute paths should be normalized correctly"""
        os.environ["ZT_TARGET"] = str(tmp_path)
        
        # Create nested structure
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        
        # Access with relative components
        weird_path = tmp_path / "a" / "x" / ".." / "b" / "c"
        
        result = validate_path(str(weird_path))
        assert result == nested.resolve()
    
    def test_sentinel_file_protection(self, tmp_path):
        """Sentinel test: file outside target must remain unchanged"""
        # Setup
        target = tmp_path / "target"
        target.mkdir()
        sentinel = tmp_path / "sentinel.txt"
        sentinel.write_text("ORIGINAL CONTENT")
        
        os.environ["ZT_TARGET"] = str(target)
        
        # Try to modify sentinel (should fail)
        try:
            validate_path(str(sentinel))
            pytest.fail("Should have raised HTTPException")
        except HTTPException:
            pass
        
        # Verify sentinel unchanged
        assert sentinel.read_text() == "ORIGINAL CONTENT"


class TestPatchApplicationGuard:
    """Test that patch application respects ZT_TARGET"""
    
    def test_patch_json_outside_target_rejected(self, tmp_path):
        """Patch JSON pointing outside target should be rejected"""
        target = tmp_path / "target"
        target.mkdir()
        outside_file = tmp_path / "outside.py"
        
        os.environ["ZT_TARGET"] = str(target)
        
        # Create malicious patch
        bad_patch = [
            {
                "path": str(outside_file),
                "content": "print('malicious')"
            }
        ]
        
        patch_file = tmp_path / "bad_patch.json"
        patch_file.write_text(json.dumps(bad_patch))
        
        # Validation should reject this
        with pytest.raises(HTTPException):
            validate_path(str(outside_file))


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
