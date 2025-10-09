"""Zero Tolerance Python Contract Enforcer
Real-time File Watcher for Contract Validation
"""

import time
import threading
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from enforcement.validator import Validator
from enforcement.utils import load_contract_rules, ProjectPaths, get_logger


class ContractValidationHandler(FileSystemEventHandler):
    """File system event handler for contract validation."""
    
    def __init__(self, validator: Validator, callback: Optional[Callable] = None):
        """Initialize the handler.
        
        Args:
            validator: Validator instance to use for checking
            callback: Optional callback function to call after validation
        """
        self.validator = validator
        self.callback = callback
        self.logger = get_logger(__name__)
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only validate Python files
        if file_path.suffix.lower() == '.py':
            self.logger.info("messages.file_modified", extra={"file": str(file_path)})
            self._validate_file(file_path)
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only validate Python files
        if file_path.suffix.lower() == '.py':
            self.logger.info("messages.file_created", extra={"file": str(file_path)})
            self._validate_file(file_path)
    
    def _validate_file(self, file_path: Path):
        """Validate a single file for contract compliance."""
        try:
            # Create a temporary project path for single file validation
            rules = load_contract_rules()
            temp_paths = ProjectPaths(
                base=file_path.parent,
                includes=[str(file_path.relative_to(file_path.parent))],
                excludes=[]
            )
            
            temp_validator = Validator(rules, temp_paths)
            report = temp_validator.run()
            
            if report.total_violations > 0:
                self.logger.warning(
                    "messages.contract_violations_detected", 
                    extra={
                        "file": str(file_path),
                        "violations": report.total_violations
                    }
                )
                
                # Optionally run auto-fixer
                from enforcement.rewriter import AutoRewriter
                rewriter = AutoRewriter(temp_paths)
                outcomes = rewriter.execute()
                
                if outcomes:
                    self.logger.info(
                        "messages.auto_fix_applied", 
                        extra={
                            "file": str(file_path),
                            "fixes": len(outcomes)
                        }
                    )
            else:
                self.logger.info(
                    "messages.file_compliant", 
                    extra={"file": str(file_path)}
                )
                
            if self.callback:
                self.callback(report, file_path)
                
        except Exception as e:
            self.logger.error(
                "messages.validation_error", 
                extra={"file": str(file_path), "error": str(e)}
            )


class FileWatcher:
    """Real-time file watcher for contract validation."""
    
    def __init__(self, watch_path: str = ".", patterns: Optional[list] = None):
        """Initialize the file watcher.
        
        Args:
            watch_path: Path to watch for changes
            patterns: List of file patterns to watch (default: ['**/*.py'])
        """
        self.watch_path = Path(watch_path)
        self.patterns = patterns or ['**/*.py']
        self.observer = Observer()
        self.logger = get_logger(__name__)
        
        # Load rules and create validator
        rules = load_contract_rules()
        self.project_paths = ProjectPaths(
            base=self.watch_path,
            includes=self.patterns,
            excludes=rules.get("exclude_globs", [])
        )
        self.validator = Validator(rules, self.project_paths)
        
    def start(self, callback: Optional[Callable] = None):
        """Start watching for file changes.
        
        Args:
            callback: Optional callback function to call after validation
        """
        event_handler = ContractValidationHandler(self.validator, callback)
        
        self.observer.schedule(
            event_handler, 
            str(self.watch_path), 
            recursive=True
        )
        
        self.observer.start()
        self.logger.info(
            "messages.file_watcher_started", 
            extra={"path": str(self.watch_path)}
        )
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the file watcher."""
        self.observer.stop()
        self.observer.join()
        self.logger.info("messages.file_watcher_stopped")


def main():
    """Main function to run the file watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Zero Tolerance File Watcher')
    parser.add_argument('--path', default='.', help='Path to watch (default: current directory)')
    parser.add_argument('--patterns', nargs='+', default=['**/*.py'], 
                       help='File patterns to watch (default: **/*.py)')
    
    args = parser.parse_args()
    
    watcher = FileWatcher(watch_path=args.path, patterns=args.patterns)
    watcher.start()


if __name__ == "__main__":
    main()
