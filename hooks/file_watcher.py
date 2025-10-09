#!/usr/bin/env python3
"""
Zero Tolerance Python Contract Enforcer File Watcher
Real-time validation for Python files
"""

import os
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ContractValidationHandler(FileSystemEventHandler):
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.validator_path = self.base_path / "enforcement" / "validator.py"
        self.rewriter_path = self.base_path / "enforcement" / "rewriter.py"
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only process Python files
        if event.src_path.endswith('.py'):
            file_path = Path(event.src_path).resolve()
            
            # Skip validation files to prevent infinite loops
            if any(skip in str(file_path) for skip in ['enforcement', 'logs', 'data']):
                return
                
            print(f"🔍 File changed: {file_path.name}")
            self.run_validation(file_path)
    
    def on_created(self, event):
        if event.is_directory:
            return
            
        # Only process Python files
        if event.src_path.endswith('.py'):
            file_path = Path(event.src_path).resolve()
            
            # Skip validation files to prevent infinite loops
            if any(skip in str(file_path) for skip in ['enforcement', 'logs', 'data']):
                return
                
            print(f"🆕 New file: {file_path.name}")
            self.run_validation(file_path)
    
    def run_validation(self, file_path: Path):
        """Run validation on the specific file"""
        try:
            # Run the validator on the specific file
            result = subprocess.run([
                'python', str(self.validator_path)
            ], capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode != 0:
                print(f"❌ Contract violations found in {file_path.name}")
                print(result.stdout)
                
                # Optionally auto-fix
                auto_fix = input("Auto-fix violations? (y/N): ").lower().strip()
                if auto_fix == 'y':
                    self.run_fixer()
            else:
                print(f"✅ {file_path.name} passed contract validation")
                
        except Exception as e:
            print(f"❌ Error validating {file_path.name}: {e}")
    
    def run_fixer(self):
        """Run the auto-fixer"""
        try:
            result = subprocess.run([
                'python', str(self.rewriter_path)
            ], capture_output=True, text=True, cwd=self.base_path)
            
            if result.returncode == 0:
                print("✅ Auto-fix completed successfully")
            else:
                print(f"❌ Auto-fix failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error running auto-fixer: {e}")


def main():
    """Main function to start the file watcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Zero Tolerance Contract File Watcher')
    parser.add_argument('--path', default='.', help='Path to watch (default: current directory)')
    parser.add_argument('--exclude', nargs='*', default=['enforcement', 'logs', 'data', '.git', 'node_modules', '__pycache__'], 
                       help='Directories to exclude from watching')
    
    args = parser.parse_args()
    
    print(f"👀 Starting Zero Tolerance Contract File Watcher...")
    print(f"📁 Watching path: {args.path}")
    print(f"🚫 Excluding: {', '.join(args.exclude)}")
    
    event_handler = ContractValidationHandler(args.path)
    observer = Observer()
    
    # Add event handlers for each directory to watch
    watch_path = Path(args.path).resolve()
    for root, dirs, files in os.walk(watch_path):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in args.exclude]
        
        # Only watch directories that contain Python files
        has_py_files = any(file.endswith('.py') for file in files)
        has_py_dirs = any(d for d in dirs if d != '__pycache__')
        
        if has_py_files or has_py_dirs:
            observer.schedule(event_handler, root, recursive=False)
            print(f"🔍 Added watch for: {root}")
    
    observer.start()
    
    try:
        print("✅ File watcher started. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping file watcher...")
        observer.stop()
    
    observer.join()
    print("👋 File watcher stopped.")


if __name__ == "__main__":
    main()
