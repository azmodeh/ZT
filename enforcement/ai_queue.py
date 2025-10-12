"""
Zero Tolerance Python Contract Enforcer
Enhanced AI Queue with Multi-Agent and Learning Integration

یکپارچه‌سازی با:
- Auto-Learning Loop 
- Multi-Agent Mode
- Smart Diff Analyzer
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import yaml

from enforcement.utils import ProjectPaths, emit_ui_message, get_logger, load_contract_rules, load_project_paths
from enforcement.auto_learning import LearningManager
from enforcement.agent_manager import AgentManager
from enforcement.diff_analyzer import SmartDiffAnalyzer
from enforcement.cost_optimizer import CostOptimizer, get_optimizer

QUEUE_LOG_PATH = Path("logs/ai_actions/queue_run.log")
PATCH_CACHE = Path("data/cache/patches")
LOGGER = get_logger("zero_tolerance.queue")


def _attach_queue_handler() -> None:
    for handler in LOGGER.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == QUEUE_LOG_PATH:
            return
    handler = logging.FileHandler(QUEUE_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.propagate = False


@dataclass
class Task:
    task_id: str
    description: str
    task_type: str  # نوع وظیفه برای انتخاب ایجنت
    agent_prompt: Optional[str] = None
    action: Optional[str] = None
    target_file: Optional[str] = None
    violations: Optional[List[str]] = None
    priority: int = 1  # اولویت وظیفه


@dataclass 
class TaskResult:
    task: Task
    success: bool
    agent_name: Optional[str]
    execution_time: float
    score: int
    diff_analysis: Optional[Dict[str, Any]]
    patches_applied: int
    error: Optional[str] = None


class EnhancedChangeTracker:
    """ردیاب پیشرفته تغییرات با قابلیت diff analysis"""
    
    def __init__(self, project_paths: ProjectPaths):
        self.project_paths = project_paths
        self.diff_analyzer = SmartDiffAnalyzer()
        self.file_contents: Dict[Path, str] = {}
        self.patch_snapshot = self._snapshot_patches()
        self.file_snapshot = self._snapshot_files()
        self._capture_file_contents()

    def _snapshot_patches(self) -> Dict[Path, float]:
        if not PATCH_CACHE.exists():
            return {}
        return {path: path.stat().st_mtime for path in PATCH_CACHE.glob("*.json")}

    def _snapshot_files(self) -> Dict[Path, float]:
        snapshot: Dict[Path, float] = {}
        for path in self.project_paths.iter_python_files():
            try:
                snapshot[path] = path.stat().st_mtime
            except FileNotFoundError:
                continue
        return snapshot
    
    def _capture_file_contents(self) -> None:
        """ضبط محتوای فایل‌ها برای diff analysis"""
        self.file_contents.clear()
        for path in self.project_paths.iter_python_files():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.file_contents[path] = f.read()
            except Exception as e:
                LOGGER.warning(f"Could not read {path}: {e}")

    def refresh(self) -> None:
        self.patch_snapshot = self._snapshot_patches()
        self.file_snapshot = self._snapshot_files()
        self._capture_file_contents()

    def has_changes(self) -> bool:
        current_patches = self._snapshot_patches()
        current_files = self._snapshot_files()

        if set(current_patches) - set(self.patch_snapshot):
            return True

        for path, mtime in current_files.items():
            baseline = self.file_snapshot.get(path)
            if baseline is None or abs(baseline - mtime) > 1e-6:
                return True
        return False
    
    def analyze_changes(self) -> List[Dict[str, Any]]:
        """تحلیل تغییرات انجام شده"""
        analyses = []
        
        for path in self.project_paths.iter_python_files():
            try:
                # بررسی آیا فایل تغییر کرده
                current_mtime = path.stat().st_mtime
                baseline_mtime = self.file_snapshot.get(path)
                
                if baseline_mtime and abs(current_mtime - baseline_mtime) > 1e-6:
                    # خواندن محتوای جدید
                    with open(path, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    
                    old_content = self.file_contents.get(path, "")
                    
                    # تحلیل diff
                    diff_result = self.diff_analyzer.analyze_diff(
                        old_content, new_content, str(path)
                    )
                    
                    analyses.append(diff_result)
                    
            except Exception as e:
                LOGGER.warning(f"Error analyzing changes in {path}: {e}")
        
        return analyses


class IntelligentQueue:
    """صف هوشمند با یکپارچگی AI و Learning"""
    
    def __init__(self):
        self.learning_manager = LearningManager()
        self.agent_manager = AgentManager()
        self.diff_analyzer = SmartDiffAnalyzer()
        self.results_history: List[TaskResult] = []
        
        LOGGER.info("Intelligent Queue initialized with AI agents and learning")
    
    async def execute_task(self, task: Task, tracker: EnhancedChangeTracker) -> TaskResult:
        """اجرای هوشمند وظیفه با ایجنت‌ها"""
        
        start_time = time.time()
        emit_ui_message(f"در حال اجرا: {task.description}")
        
        try:
            # انتخاب بهترین ایجنت از سیستم یادگیری
            suggested_agent = self.learning_manager.get_best_agent_for_task(task.task_type)
            LOGGER.info(f"Learning system suggests agent: {suggested_agent}")
            
            # اگر فایل مشخص است، از agent manager استفاده کن
            if task.target_file and Path(task.target_file).exists():
                result = await self._execute_with_agents(task, tracker)
            else:
                # fallback به روش سنتی
                result = await self._execute_traditional(task, tracker)
            
            execution_time = time.time() - start_time
            
            # ثبت نتیجه در سیستم یادگیری
            self.learning_manager.record_result(
                task_name=task.task_type,
                success=result.success,
                score=result.score,
                agent_name=result.agent_name,
                execution_time=execution_time,
                violations=task.violations
            )
            
            self.results_history.append(result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            LOGGER.error(f"Task execution failed: {e}")
            
            result = TaskResult(
                task=task,
                success=False,
                agent_name=None,
                execution_time=execution_time,
                score=0,
                diff_analysis=None,
                patches_applied=0,
                error=str(e)
            )
            
            # ثبت شکست در یادگیری
            self.learning_manager.record_result(
                task_name=task.task_type,
                success=False,
                score=0,
                execution_time=execution_time
            )
            
            return result
    
    async def _execute_with_agents(self, task: Task, 
                                  tracker: EnhancedChangeTracker) -> TaskResult:
        """اجرا با استفاده از agent manager"""
        
        # خواندن فایل هدف
        target_path = Path(task.target_file)
        with open(target_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # dispatch به agent manager
        agent_result = await self.agent_manager.dispatch_task(
            task_type=task.task_type,
            file_path=str(target_path),
            content=original_content,
            context={
                "violations": task.violations,
                "description": task.description
            }
        )
        
        if not agent_result["success"]:
            return TaskResult(
                task=task,
                success=False,
                agent_name=agent_result.get("agent_name"),
                execution_time=agent_result.get("execution_time", 0),
                score=0,
                diff_analysis=None,
                patches_applied=0,
                error=agent_result.get("error")
            )
        
        # اعمال patches
        patches_applied = 0
        diff_analyses = []
        
        try:
            result_data = agent_result["result"]
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
            
            for patch in result_data:
                patch_path = Path(patch["path"])
                new_content = patch["content"]
                
                # تحلیل diff قبل از اعمال
                diff_analysis = self.diff_analyzer.analyze_diff(
                    original_content, new_content, str(patch_path)
                )
                diff_analyses.append(diff_analysis)
                
                # بررسی امنیت
                if self.diff_analyzer.is_safe_to_apply(diff_analysis["risk_score"]):
                    # اعمال پچ
                    with open(patch_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    patches_applied += 1
                    LOGGER.info(f"Applied patch to {patch_path} (risk: {diff_analysis['risk_score']})")
                else:
                    LOGGER.warning(f"Patch for {patch_path} rejected due to high risk: {diff_analysis['risk_score']}")
                    emit_ui_message(f"پچ {patch_path.name} به دلیل ریسک بالا رد شد")
                    
        except Exception as e:
            LOGGER.error(f"Error applying patches: {e}")
        
        tracker.refresh()
        
        # محاسبه امتیاز
        score = agent_result.get("score", 0)
        if patches_applied == 0 and agent_result["success"]:
            score = max(score - 20, 0)  # کسر امتیاز برای عدم اعمال
        
        return TaskResult(
            task=task,
            success=patches_applied > 0,
            agent_name=agent_result.get("agent_name"),
            execution_time=agent_result.get("execution_time", 0),
            score=score,
            diff_analysis=diff_analyses[0] if diff_analyses else None,
            patches_applied=patches_applied
        )
    
    async def _execute_traditional(self, task: Task, 
                                  tracker: EnhancedChangeTracker) -> TaskResult:
        """اجرای سنتی برای backward compatibility"""
        
        tracker.refresh()
        
        if task.agent_prompt:
            code = run_command([sys.executable, "enforcement/ai_agent.py", task.agent_prompt])
        elif task.action == "validate":
            code = run_command([sys.executable, "enforcement/validator.py"])
        elif task.action == "rewrite":
            code = run_command([sys.executable, "enforcement/rewriter.py"])
        else:
            raise ValueError(f"Unsupported task configuration: {task}")
        
        success = code == 0
        
        if task.agent_prompt and not tracker.has_changes():
            await self._handle_noop(tracker)
            success = tracker.has_changes()
        
        # تحلیل تغییرات
        diff_analyses = tracker.analyze_changes()
        
        return TaskResult(
            task=task,
            success=success,
            agent_name="traditional",
            execution_time=0,  # محاسبه دقیق در execute_task
            score=80 if success else 0,
            diff_analysis=diff_analyses[0] if diff_analyses else None,
            patches_applied=len(diff_analyses)
        )
    
    async def _handle_noop(self, tracker: EnhancedChangeTracker) -> None:
        """مدیریت وضعیت عدم تغییر"""
        LOGGER.warning("Task produced no observable changes; running auto rewriter as fallback.")
        emit_ui_message("هیچ تغییری ثبت نشد؛ بازنویس خودکار در حال اجرا است.")
        run_command([sys.executable, "enforcement/rewriter.py"])
        tracker.refresh()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """خلاصه عملکرد صف"""
        
        if not self.results_history:
            return {"message": "No tasks executed yet"}
        
        total_tasks = len(self.results_history)
        successful_tasks = sum(1 for r in self.results_history if r.success)
        total_patches = sum(r.patches_applied for r in self.results_history)
        avg_score = sum(r.score for r in self.results_history) / total_tasks
        
        agent_stats = {}
        for result in self.results_history:
            if result.agent_name:
                if result.agent_name not in agent_stats:
                    agent_stats[result.agent_name] = {"tasks": 0, "success": 0}
                agent_stats[result.agent_name]["tasks"] += 1
                if result.success:
                    agent_stats[result.agent_name]["success"] += 1
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "success_rate": successful_tasks / total_tasks,
            "total_patches_applied": total_patches,
            "average_score": avg_score,
            "agent_performance": agent_stats,
            "learning_suggestions": self.learning_manager.suggest_actions()
        }


def load_tasks() -> List[Task]:
    """بارگذاری وظایف با پشتیبانی از فیلدهای جدید"""
    config_path = Path("enforcement/tasks.yml")
    if not config_path.exists():
        raise FileNotFoundError("tasks.yml not found in enforcement directory.")
    
    with config_path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    
    tasks: List[Task] = []
    for entry in raw.get("tasks", []):
        tasks.append(
            Task(
                task_id=str(entry.get("id")),
                description=str(entry.get("description", "")),
                task_type=entry.get("task_type", "general"),
                agent_prompt=entry.get("agent_prompt"),
                action=entry.get("action"),
                target_file=entry.get("target_file"),
                violations=entry.get("violations"),
                priority=entry.get("priority", 1)
            )
        )
    
    # مرتب‌سازی بر اساس اولویت
    tasks.sort(key=lambda t: t.priority, reverse=True)
    return tasks


def run_command(command: List[str]) -> int:
    """اجرای فرمان سیستم"""
    LOGGER.info("Executing command: %s", " ".join(command))
    result = subprocess.run(command, check=False)
    return result.returncode


async def main() -> None:
    """تابع اصلی با قابلیت‌های جدید"""
    _attach_queue_handler()
    load_contract_rules()  # ensures rules file exists
    project_paths = load_project_paths()
    
    # مقداردهی Cost Optimizer
    optimizer = get_optimizer()
    optimizer.reset_run_budget()
    
    # نمایش بودجه اولیه
    budget_status = optimizer.get_budget_status()
    LOGGER.info(f"💰 Budget: Daily {budget_status['daily_remaining']} remaining, Run {budget_status['run_remaining']} remaining")
    
    # مقداردهی اجزای هوشمند
    intelligent_queue = IntelligentQueue()
    tracker = EnhancedChangeTracker(project_paths)
    tasks = load_tasks()

    emit_ui_message("صف هوشمند هوش مصنوعی آغاز شد.")
    LOGGER.info(f"Starting intelligent queue with {len(tasks)} tasks")
    
    results = []
    
    for i, task in enumerate(tasks, 1):
        emit_ui_message(f"وظیفه {i}/{len(tasks)}: {task.description}")
        
        # بررسی بودجه قبل از اجرای task
        if not optimizer.check_budget():
            LOGGER.warning(f"⚠️ Budget exceeded, stopping queue at task {i}/{len(tasks)}")
            emit_ui_message("⚠️ بودجه تمام شد - صف متوقف شد")
            break
        
        try:
            result = await intelligent_queue.execute_task(task, tracker)
            results.append(result)
            
            if result.success:
                emit_ui_message(f"✅ وظیفه '{task.description}' موفقیت‌آمیز بود")
                if result.patches_applied > 0:
                    emit_ui_message(f"📝 {result.patches_applied} پچ اعمال شد")
            else:
                emit_ui_message(f"❌ وظیفه '{task.description}' ناموفق: {result.error or 'نامشخص'}")
                
        except Exception as e:
            LOGGER.error(f"Critical error in task {task.task_id}: {e}")
            emit_ui_message(f"خطای حادّ در وظیفه {task.description}")
    
    # گزارش نهایی
    summary = intelligent_queue.get_performance_summary()
    
    emit_ui_message("📊 خلاصه عملکرد:")
    emit_ui_message(f"   وظایف موفق: {summary['successful_tasks']}/{summary['total_tasks']}")
    emit_ui_message(f"   نرخ موفقیت: {summary['success_rate']:.1%}")
    emit_ui_message(f"   پچ‌های اعمال شده: {summary['total_patches_applied']}")
    emit_ui_message(f"   میانگین امتیاز: {summary['average_score']:.1f}")
    
    # نمایش پیشنهادات یادگیری
    suggestions = summary.get("learning_suggestions", [])
    if suggestions:
        emit_ui_message("💡 پیشنهادات سیستم یادگیری:")
        for suggestion in suggestions[:3]:
            emit_ui_message(f"   • {suggestion}")
    
    # نمایش وضعیت بودجه نهایی
    final_budget = optimizer.get_budget_status()
    emit_ui_message("💰 وضعیت بودجه:")
    emit_ui_message(f"   هزینه این اجرا: {final_budget['run_spent']}")
    emit_ui_message(f"   باقی‌مانده روزانه: {final_budget['daily_remaining']}")
    LOGGER.info(f"Final budget: Daily spent {final_budget['daily_spent']}, Run spent {final_budget['run_spent']}")
    
    emit_ui_message("اجرای صف کامل شد. گزارش‌ها در پوشه logs موجود است.")
    
    # ذخیره گزارش تفصیلی
    report_path = Path("logs/ai_actions") / f"queue_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    detailed_report = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "task_results": [
            {
                "task_id": r.task.task_id,
                "description": r.task.description,
                "success": r.success,
                "agent": r.agent_name,
                "score": r.score,
                "patches": r.patches_applied,
                "execution_time": r.execution_time
            }
            for r in results
        ]
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(detailed_report, f, indent=2, ensure_ascii=False)
    
    LOGGER.info(f"Detailed report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())