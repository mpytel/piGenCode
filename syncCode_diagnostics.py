# Enhanced error handling and diagnostics for syncCode

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class SyncDiagnostics:
    """Class to handle diagnostics and error reporting for syncCode operations"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'changes_made': 0,
            'errors_encountered': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        self.detailed_changes = {}
    
    def add_error(self, file_path: str, error_type: str, message: str, exception: Exception = None):
        """Add an error to the diagnostics"""
        error_info = {
            'file': file_path,
            'type': error_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'exception': str(exception) if exception else None
        }
        self.errors.append(error_info)
        self.stats['errors_encountered'] += 1
        
        # Log immediately
        printIt(f"ERROR [{error_type}] {file_path}: {message}", lable.ERROR)
        if exception:
            printIt(f"  Exception: {exception}", lable.DEBUG)
    
    def add_warning(self, file_path: str, warning_type: str, message: str):
        """Add a warning to the diagnostics"""
        warning_info = {
            'file': file_path,
            'type': warning_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.warnings.append(warning_info)
        
        # Log immediately
        printIt(f"WARNING [{warning_type}] {file_path}: {message}", lable.WARN)
    
    def record_file_processed(self, file_path: str, changes: List[str]):
        """Record that a file was successfully processed"""
        self.stats['files_processed'] += 1
        self.stats['changes_made'] += len(changes)
        
        if changes:
            self.detailed_changes[file_path] = changes
    
    def record_file_skipped(self, file_path: str, reason: str):
        """Record that a file was skipped"""
        self.stats['files_skipped'] += 1
        self.add_warning(file_path, "SKIPPED", reason)
    
    def finalize(self):
        """Finalize diagnostics and generate summary"""
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        
        # Print summary
        printIt("=" * 60, lable.INFO)
        printIt("SYNC DIAGNOSTICS SUMMARY", lable.INFO)
        printIt("=" * 60, lable.INFO)
        printIt(f"Duration: {duration.total_seconds():.2f} seconds", lable.INFO)
        printIt(f"Files processed: {self.stats['files_processed']}", lable.INFO)
        printIt(f"Files skipped: {self.stats['files_skipped']}", lable.INFO)
        printIt(f"Total changes: {self.stats['changes_made']}", lable.INFO)
        printIt(f"Errors: {len(self.errors)}", lable.INFO)
        printIt(f"Warnings: {len(self.warnings)}", lable.INFO)
        
        # Show error summary
        if self.errors:
            printIt("\nERROR SUMMARY:", lable.ERROR)
            error_types = {}
            for error in self.errors:
                error_type = error['type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                printIt(f"  {error_type}: {count} occurrences", lable.ERROR)
        
        # Show warning summary
        if self.warnings:
            printIt("\nWARNING SUMMARY:", lable.WARN)
            warning_types = {}
            for warning in self.warnings:
                warning_type = warning['type']
                warning_types[warning_type] = warning_types.get(warning_type, 0) + 1
            
            for warning_type, count in warning_types.items():
                printIt(f"  {warning_type}: {count} occurrences", lable.WARN)
    
    def save_report(self, output_path: Path = None):
        """Save detailed diagnostics report to file"""
        if not output_path:
            output_path = Path("syncCode_diagnostics.json")
        
        report = {
            'summary': self.stats,
            'errors': self.errors,
            'warnings': self.warnings,
            'detailed_changes': self.detailed_changes
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            printIt(f"Diagnostics report saved to: {output_path}", lable.INFO)
        except Exception as e:
            printIt(f"Failed to save diagnostics report: {e}", lable.ERROR)

def enhanced_error_handling(func):
    """Decorator to add enhanced error handling to sync functions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SyntaxError as e:
            # Handle Python syntax errors specifically
            file_path = args[0] if args else "unknown"
            printIt(f"Python syntax error in {file_path}:", lable.ERROR)
            printIt(f"  Line {e.lineno}: {e.text}", lable.ERROR)
            printIt(f"  {e.msg}", lable.ERROR)
            return []
        except FileNotFoundError as e:
            file_path = args[0] if args else "unknown"
            printIt(f"File not found: {file_path}", lable.ERROR)
            printIt("  Check file paths and permissions", lable.INFO)
            return []
        except PermissionError as e:
            file_path = args[0] if args else "unknown"
            printIt(f"Permission denied: {file_path}", lable.ERROR)
            printIt("  Check file permissions and ownership", lable.INFO)
            return []
        except Exception as e:
            file_path = args[0] if args else "unknown"
            printIt(f"Unexpected error processing {file_path}: {e}", lable.ERROR)
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            printIt(f"Stack trace:\n{tb_str}", lable.DEBUG)
            return []
    return wrapper

def validate_python_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a Python file for common issues that might cause sync problems.
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        # Check file exists and is readable
        if not file_path.exists():
            issues.append("File does not exist")
            return False, issues
        
        if not file_path.is_file():
            issues.append("Path is not a file")
            return False, issues
        
        # Check file size (warn if too large)
        file_size = file_path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB
            issues.append(f"Large file size ({file_size // 1024}KB) may cause performance issues")
        
        # Try to read the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            issues.append("File contains non-UTF-8 characters")
            return False, issues
        
        # Try to parse as Python
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Python syntax error at line {e.lineno}: {e.msg}")
            return False, issues
        
        # Check for common problematic patterns
        if 'exec(' in content or 'eval(' in content:
            issues.append("File contains exec() or eval() - may cause parsing issues")
        
        if content.count('"""') % 2 != 0 or content.count("'''") % 2 != 0:
            issues.append("Unmatched triple quotes detected")
        
        # Check for very long lines that might cause issues
        lines = content.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 500]
        if long_lines:
            issues.append(f"Very long lines detected: {long_lines[:5]}")
        
        return len(issues) == 0 or all('may cause' in issue for issue in issues), issues
        
    except Exception as e:
        issues.append(f"Validation error: {e}")
        return False, issues

def validate_piseed_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a piSeed file for common issues.
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        # Check file exists and is readable
        if not file_path.exists():
            issues.append("piSeed file does not exist")
            return False, issues
        
        # Try to read the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            issues.append("piSeed file contains non-UTF-8 characters")
            return False, issues
        
        # Check for basic piSeed structure
        lines = content.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        if not non_empty_lines:
            issues.append("piSeed file is empty or contains only comments")
            return False, issues
        
        # Check first line for piClassGC or piDefGC declaration
        first_line = non_empty_lines[0]
        if not (first_line.startswith('piClassGC ') or first_line.startswith('piDefGC ')):
            issues.append("piSeed file does not start with piClassGC or piDefGC declaration")
        
        # Check for common syntax issues
        for i, line in enumerate(non_empty_lines, 1):
            if line.count('"') % 2 != 0 and line.count("'") % 2 != 0:
                issues.append(f"Unmatched quotes on line {i}: {line[:50]}...")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        issues.append(f"piSeed validation error: {e}")
        return False, issues

def recovery_suggestions(error_type: str, file_path: str) -> List[str]:
    """Provide recovery suggestions based on error type"""
    suggestions = []
    
    if error_type == "SYNTAX_ERROR":
        suggestions.extend([
            "Check Python syntax in the file",
            "Look for unmatched parentheses, brackets, or quotes",
            "Verify indentation is consistent",
            "Try running 'python -m py_compile <filename>' to check syntax"
        ])
    
    elif error_type == "FILE_NOT_FOUND":
        suggestions.extend([
            "Verify the file path is correct",
            "Check if the file was moved or renamed",
            "Ensure you're running from the correct directory",
            "Use 'find . -name \"<filename>\"' to locate the file"
        ])
    
    elif error_type == "PERMISSION_ERROR":
        suggestions.extend([
            "Check file permissions with 'ls -la <filename>'",
            "Ensure you have read/write access to the file",
            "Try running with appropriate permissions",
            "Check if the file is locked by another process"
        ])
    
    elif error_type == "PISEED_NOT_FOUND":
        suggestions.extend([
            "Use --create-missing to auto-create piSeed file",
            "Check if the piSeed file was moved or renamed",
            "Verify the piSeeds directory path in configuration",
            "Look for similar piSeed files that might match"
        ])
    
    elif error_type == "AST_PARSE_ERROR":
        suggestions.extend([
            "Check for complex Python constructs that AST can't handle",
            "Look for dynamic code generation or exec() statements",
            "Verify all imports are available",
            "Try simplifying complex expressions"
        ])
    
    return suggestions

# Usage example for enhanced diagnostics
def syncCodeWithDiagnostics(argParse: ArgParse):
    """syncCode with comprehensive diagnostics and error handling"""
    diagnostics = SyncDiagnostics()
    
    try:
        # Your existing syncCode logic here, but with diagnostics
        args = argParse.parser.parse_args()
        theArgs = args.arguments
        
        if len(theArgs) > 0:
            # Single file sync with diagnostics
            fileName = theArgs[0]
            
            # Validate file first
            filePath = enhanced_file_discovery(fileName)
            if filePath:
                is_valid, issues = validate_python_file(filePath)
                if not is_valid:
                    for issue in issues:
                        diagnostics.add_error(str(filePath), "VALIDATION_ERROR", issue)
                    return
                
                # Proceed with sync
                changes = syncSingleFile(fileName)  # Your existing function
                diagnostics.record_file_processed(str(filePath), changes or [])
            else:
                diagnostics.add_error(fileName, "FILE_NOT_FOUND", "Could not locate file")
        else:
            # All files sync with diagnostics
            syncAllChangedFilesWithDiagnostics(diagnostics)
    
    finally:
        diagnostics.finalize()
        
        # Save detailed report if there were errors
        if diagnostics.errors or diagnostics.warnings:
            diagnostics.save_report()
