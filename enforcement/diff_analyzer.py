"""
Zero Tolerance Python Contract Enforcer
Smart Diff Analyzer Module

هدف: تحلیل هوشمند تفاوت کد قبل از اعمال پچ و ارزیابی ریسک تغییرات
"""

import ast
import difflib
import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib

from .utils import get_logger

logger = get_logger(__name__)

class SmartDiffAnalyzer:
    """تحلیل‌گر هوشمند تفاوت کد"""
    
    def __init__(self, cache_dir: str = "data/cache/diff_reports"):
        """مقداردهی تحلیل‌گر
        
        Args:
            cache_dir: مسیر ذخیره گزارش‌های diff
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # آستانه‌های ریسک
        self.risk_thresholds = {
            "low": 30,
            "medium": 50, 
            "high": 70,
            "critical": 90
        }
        
        # وزن‌های مختلف تغییرات
        self.change_weights = {
            "function_deletion": 25,
            "class_deletion": 30,
            "import_changes": 10,
            "logic_structure": 20,
            "line_changes": 5,
            "complexity_increase": 15
        }
        
        logger.info("Smart Diff Analyzer initialized")
    
    def analyze_diff(self, old_code: str, new_code: str, 
                    file_path: str = None) -> Dict[str, Any]:
        """تحلیل کامل تفاوت بین دو نسخه کد
        
        Args:
            old_code: کد قبلی
            new_code: کد جدید  
            file_path: مسیر فایل (اختیاری)
            
        Returns:
            گزارش کامل تحلیل شامل risk_score و جزئیات
        """
        
        analysis_start = datetime.now()
        
        try:
            # تحلیل پایه
            basic_diff = self._analyze_basic_diff(old_code, new_code)
            
            # تحلیل ساختاری
            structural_diff = self._analyze_structural_changes(old_code, new_code)
            
            # تحلیل پیچیدگی
            complexity_diff = self._analyze_complexity_changes(old_code, new_code)
            
            # تحلیل امنیتی
            security_diff = self._analyze_security_changes(old_code, new_code)
            
            # محاسبه امتیاز ریسک کلی
            risk_score = self._calculate_risk_score(
                basic_diff, structural_diff, complexity_diff, security_diff
            )
            
            # تعیین سطح ریسک
            risk_level = self._determine_risk_level(risk_score)
            
            # تولید گزارش نهایی
            report = {
                "timestamp": analysis_start.isoformat(),
                "file_path": file_path or "unknown",
                "risk_score": risk_score,
                "risk_level": risk_level,
                "changed_lines": basic_diff["changed_lines"],
                "added_lines": basic_diff["added_lines"],
                "deleted_lines": basic_diff["deleted_lines"],
                "deleted_blocks": structural_diff["deleted_blocks"],
                "added_blocks": structural_diff["added_blocks"],
                "modified_functions": structural_diff["modified_functions"],
                "modified_classes": structural_diff["modified_classes"],
                "import_changes": structural_diff["import_changes"],
                "complexity_delta": complexity_diff["complexity_delta"],
                "security_issues": security_diff["issues"],
                "recommendations": self._generate_recommendations(
                    risk_score, structural_diff, security_diff
                ),
                "analysis_time": (datetime.now() - analysis_start).total_seconds()
            }
            
            # ذخیره گزارش
            if file_path:
                self._save_report(report, file_path)
            
            logger.info(f"Diff analysis completed: risk_score={risk_score}, "
                       f"level={risk_level}")
            
            return report
            
        except Exception as e:
            logger.error(f"Diff analysis failed: {e}")
            return {
                "timestamp": analysis_start.isoformat(),
                "file_path": file_path or "unknown",
                "risk_score": 100,  # حداکثر ریسک در صورت خطا
                "risk_level": "critical",
                "error": str(e),
                "analysis_time": (datetime.now() - analysis_start).total_seconds()
            }
    
    def _analyze_basic_diff(self, old_code: str, new_code: str) -> Dict[str, Any]:
        """تحلیل پایه تفاوت خطوط"""
        
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()
        
        differ = difflib.unified_diff(old_lines, new_lines, lineterm='')
        diff_lines = list(differ)
        
        added_lines = sum(1 for line in diff_lines if line.startswith('+'))
        deleted_lines = sum(1 for line in diff_lines if line.startswith('-'))
        changed_lines = added_lines + deleted_lines
        
        # محاسبه درصد تغییر
        total_lines = max(len(old_lines), len(new_lines), 1)
        change_percentage = (changed_lines / total_lines) * 100
        
        return {
            "added_lines": added_lines,
            "deleted_lines": deleted_lines, 
            "changed_lines": changed_lines,
            "total_old_lines": len(old_lines),
            "total_new_lines": len(new_lines),
            "change_percentage": change_percentage,
            "diff_lines": diff_lines
        }
    
    def _analyze_structural_changes(self, old_code: str, 
                                  new_code: str) -> Dict[str, Any]:
        """تحلیل تغییرات ساختاری"""
        
        try:
            old_ast = ast.parse(old_code)
            new_ast = ast.parse(new_code)
        except SyntaxError as e:
            logger.warning(f"AST parsing failed: {e}")
            return {
                "deleted_blocks": 0,
                "added_blocks": 0,
                "modified_functions": [],
                "modified_classes": [],
                "import_changes": [],
                "syntax_errors": [str(e)]
            }
        
        # استخراج عناصر ساختاری
        old_elements = self._extract_structural_elements(old_ast)
        new_elements = self._extract_structural_elements(new_ast)
        
        # تحلیل تغییرات
        deleted_functions = old_elements["functions"] - new_elements["functions"]
        added_functions = new_elements["functions"] - old_elements["functions"]
        
        deleted_classes = old_elements["classes"] - new_elements["classes"]
        added_classes = new_elements["classes"] - old_elements["classes"]
        
        import_changes = self._analyze_import_changes(
            old_elements["imports"], new_elements["imports"]
        )
        
        return {
            "deleted_blocks": len(deleted_functions) + len(deleted_classes),
            "added_blocks": len(added_functions) + len(added_classes),
            "modified_functions": list(deleted_functions | added_functions),
            "modified_classes": list(deleted_classes | added_classes),
            "deleted_functions": list(deleted_functions),
            "added_functions": list(added_functions),
            "deleted_classes": list(deleted_classes),
            "added_classes": list(added_classes),
            "import_changes": import_changes
        }
    
    def _extract_structural_elements(self, tree: ast.AST) -> Dict[str, set]:
        """استخراج عناصر ساختاری از AST"""
        
        functions = set()
        classes = set()
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.add(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.add(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.add(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.add(f"{module}.{alias.name}")
        
        return {
            "functions": functions,
            "classes": classes,
            "imports": imports
        }
    
    def _analyze_import_changes(self, old_imports: set, 
                              new_imports: set) -> List[Dict[str, str]]:
        """تحلیل تغییرات import ها"""
        
        changes = []
        
        added_imports = new_imports - old_imports
        removed_imports = old_imports - new_imports
        
        for imp in added_imports:
            changes.append({"type": "added", "import": imp})
        
        for imp in removed_imports:
            changes.append({"type": "removed", "import": imp})
        
        return changes
    
    def _analyze_complexity_changes(self, old_code: str, 
                                  new_code: str) -> Dict[str, Any]:
        """تحلیل تغییرات پیچیدگی"""
        
        old_complexity = self._calculate_cyclomatic_complexity(old_code)
        new_complexity = self._calculate_cyclomatic_complexity(new_code)
        
        complexity_delta = new_complexity - old_complexity
        complexity_change_percent = (
            (complexity_delta / max(old_complexity, 1)) * 100
        )
        
        return {
            "old_complexity": old_complexity,
            "new_complexity": new_complexity,
            "complexity_delta": complexity_delta,
            "complexity_change_percent": complexity_change_percent
        }
    
    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """محاسبه پیچیدگی cyclomatic"""
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 1  # پیچیدگی پایه
        
        complexity = 1  # پیچیدگی پایه
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)  # هر except بلاک
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1  # list/dict comprehensions
        
        return complexity
    
    def _analyze_security_changes(self, old_code: str, 
                                 new_code: str) -> Dict[str, Any]:
        """تحلیل تغییرات امنیتی"""
        
        security_patterns = {
            "hardcoded_password": r'password\s*=\s*["\'][^"\']+["\']',
            "hardcoded_key": r'(api_key|secret|token)\s*=\s*["\'][^"\']+["\']',
            "sql_injection": r'(execute|query)\s*\([^)]*%[sf]',
            "eval_usage": r'\beval\s*\(',
            "exec_usage": r'\bexec\s*\(',
            "shell_injection": r'(os\.system|subprocess\.call|popen)\s*\([^)]*\+',
        }
        
        old_issues = self._find_security_issues(old_code, security_patterns)
        new_issues = self._find_security_issues(new_code, security_patterns)
        
        added_issues = []
        resolved_issues = []
        
        for pattern, matches in new_issues.items():
            old_matches = old_issues.get(pattern, [])
            for match in matches:
                if match not in old_matches:
                    added_issues.append({"pattern": pattern, "match": match})
        
        for pattern, matches in old_issues.items():
            new_matches = new_issues.get(pattern, [])
            for match in matches:
                if match not in new_matches:
                    resolved_issues.append({"pattern": pattern, "match": match})
        
        return {
            "issues": {
                "added": added_issues,
                "resolved": resolved_issues
            },
            "total_old_issues": sum(len(matches) for matches in old_issues.values()),
            "total_new_issues": sum(len(matches) for matches in new_issues.values())
        }
    
    def _find_security_issues(self, code: str, 
                             patterns: Dict[str, str]) -> Dict[str, List[str]]:
        """جستجوی مشکلات امنیتی در کد"""
        
        issues = {}
        
        for pattern_name, regex in patterns.items():
            matches = re.findall(regex, code, re.IGNORECASE | re.MULTILINE)
            if matches:
                issues[pattern_name] = matches
        
        return issues
    
    def _calculate_risk_score(self, basic_diff: Dict, structural_diff: Dict,
                             complexity_diff: Dict, security_diff: Dict) -> int:
        """محاسبه امتیاز ریسک کلی (0-100)"""
        
        risk_score = 0
        
        # ریسک تغییرات خط
        line_risk = min(
            (basic_diff["change_percentage"] / 100) * 
            self.change_weights["line_changes"], 
            self.change_weights["line_changes"]
        )
        risk_score += line_risk
        
        # ریسک حذف توابع/کلاس‌ها
        deletion_risk = (
            len(structural_diff.get("deleted_functions", [])) * 
            self.change_weights["function_deletion"] +
            len(structural_diff.get("deleted_classes", [])) * 
            self.change_weights["class_deletion"]
        )
        risk_score += min(deletion_risk, 40)  # حداکثر 40 امتیاز
        
        # ریسک تغییرات import
        import_risk = (
            len(structural_diff["import_changes"]) * 
            self.change_weights["import_changes"]
        )
        risk_score += min(import_risk, 15)  # حداکثر 15 امتیاز
        
        # ریسک افزایش پیچیدگی
        if complexity_diff["complexity_delta"] > 0:
            complexity_risk = min(
                complexity_diff["complexity_delta"] * 
                self.change_weights["complexity_increase"],
                self.change_weights["complexity_increase"]
            )
            risk_score += complexity_risk
        
        # ریسک امنیتی
        security_issues_added = len(security_diff["issues"]["added"])
        if security_issues_added > 0:
            security_risk = min(security_issues_added * 20, 30)
            risk_score += security_risk
        
        # کاهش ریسک برای رفع مسائل امنیتی
        security_issues_resolved = len(security_diff["issues"]["resolved"])
        if security_issues_resolved > 0:
            risk_score = max(0, risk_score - (security_issues_resolved * 5))
        
        return min(100, int(risk_score))
    
    def _determine_risk_level(self, risk_score: int) -> str:
        """تعیین سطح ریسک بر اساس امتیاز"""
        
        if risk_score >= self.risk_thresholds["critical"]:
            return "critical"
        elif risk_score >= self.risk_thresholds["high"]:
            return "high"
        elif risk_score >= self.risk_thresholds["medium"]:
            return "medium"
        elif risk_score >= self.risk_thresholds["low"]:
            return "low"
        else:
            return "minimal"
    
    def _generate_recommendations(self, risk_score: int, 
                                structural_diff: Dict, 
                                security_diff: Dict) -> List[str]:
        """تولید پیشنهادات بر اساس تحلیل"""
        
        recommendations = []
        
        if risk_score >= self.risk_thresholds["high"]:
            recommendations.append(
                "High risk changes detected - thorough testing recommended"
            )
        
        if len(structural_diff.get("deleted_functions", [])) > 0:
            recommendations.append(
                f"Functions deleted: {structural_diff['deleted_functions']} - "
                "verify no breaking changes"
            )
        
        if len(structural_diff.get("deleted_classes", [])) > 0:
            recommendations.append(
                f"Classes deleted: {structural_diff['deleted_classes']} - "
                "check for dependent code"
            )
        
        if len(security_diff["issues"]["added"]) > 0:
            recommendations.append(
                f"New security issues detected: "
                f"{len(security_diff['issues']['added'])} - "
                "security review required"
            )
        
        if len(structural_diff["import_changes"]) > 5:
            recommendations.append(
                "Significant import changes - verify all dependencies"
            )
        
        if not recommendations:
            if risk_score < self.risk_thresholds["low"]:
                recommendations.append("Changes appear safe to apply")
            else:
                recommendations.append("Moderate risk - standard review recommended")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any], file_path: str) -> None:
        """ذخیره گزارش در cache"""
        
        try:
            # ایجاد نام فایل بر اساس path و timestamp
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{safe_filename}_{timestamp}.json"
            
            report_path = self.cache_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Diff report saved to: {report_path}")
            
        except Exception as e:
            logger.error(f"Error saving diff report: {e}")
    
    def is_safe_to_apply(self, risk_score: int, manual_mode: bool = False) -> bool:
        """تعیین امنیت اعمال پچ
        
        Args:
            risk_score: امتیاز ریسک
            manual_mode: آیا در حالت دستی هستیم
            
        Returns:
            True اگر امن برای اعمال باشد
        """
        
        if manual_mode:
            # در حالت دستی، فقط critical را رد کن
            return risk_score < self.risk_thresholds["critical"]
        else:
            # در حالت خودکار، محافظه‌کارانه باش
            return risk_score <= self.risk_thresholds["high"]
    
    def get_cached_reports(self, file_path: str = None) -> List[Dict[str, Any]]:
        """دریافت گزارش‌های ذخیره شده
        
        Args:
            file_path: مسیر فایل برای فیلتر (اختیاری)
            
        Returns:
            لیست گزارش‌های موجود
        """
        
        reports = []
        
        try:
            pattern = "*"
            if file_path:
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', file_path)
                pattern = f"{safe_filename}_*.json"
            else:
                pattern = "*.json"
            
            for report_file in self.cache_dir.glob(pattern):
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        report["report_file"] = str(report_file)
                        reports.append(report)
                except Exception as e:
                    logger.warning(f"Error reading report {report_file}: {e}")
            
            # مرتب‌سازی بر اساس timestamp
            reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
        except Exception as e:
            logger.error(f"Error reading cached reports: {e}")
        
        return reports


# تابع کمکی برای استفاده آسان
def create_diff_analyzer(cache_dir: str = None) -> SmartDiffAnalyzer:
    """ایجاد instance جدید از SmartDiffAnalyzer
    
    Args:
        cache_dir: مسیر دایرکتوری cache
        
    Returns:
        SmartDiffAnalyzer instance
    """
    if not cache_dir:
        cache_dir = "data/cache/diff_reports"
    
    return SmartDiffAnalyzer(cache_dir)


# تابع سریع برای تحلیل
def quick_analyze(old_code: str, new_code: str, file_path: str = None) -> Dict[str, Any]:
    """تحلیل سریع تفاوت کد
    
    Args:
        old_code: کد قبلی
        new_code: کد جدید
        file_path: مسیر فایل
        
    Returns:
        گزارش تحلیل
    """
    analyzer = create_diff_analyzer()
    return analyzer.analyze_diff(old_code, new_code, file_path)


if __name__ == "__main__":
    # تست سریع
    old_code = '''
def hello():
    print("Hello World")
    
class MyClass:
    def __init__(self):
        self.password = "secret123"
'''
    
    new_code = '''
import logging
logger = logging.getLogger(__name__)

def hello():
    logger.info("Hello World")
    
def new_function():
    return "New functionality"
'''
    
    analyzer = create_diff_analyzer()
    result = analyzer.analyze_diff(old_code, new_code, "test.py")
    
    print(f"Risk Score: {result['risk_score']}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Recommendations: {result['recommendations']}")
    print(f"Safe to apply: {analyzer.is_safe_to_apply(result['risk_score'])}")