"""
Zero Tolerance Python Contract Enforcer
Auto-Learning Loop Module

هدف: یادگیری از گزارش‌های اعتبارسنجی و بهبود مستمر عملکرد ایجنت‌ها
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import os

logger = logging.getLogger(__name__)

class LearningManager:
    """مدیریت سیستم یادگیری خودکار Zero Tolerance"""
    
    def __init__(self, cache_dir: str = None):
        """مقداردهی مدیر یادگیری
        
        Args:
            cache_dir: مسیر دایرکتوری کش (پیش‌فرض: data/cache)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.profile_path = self.cache_dir / "learning_profile.json"
        self.learning_data = self._load_learning_profile()
        
        # آستانه‌های یادگیری
        self.pattern_threshold = 3  # حداقل تکرار برای شناخت pattern
        self.success_threshold = 0.7  # حداقل نرخ موفقیت
        self.max_suggestions = 10  # حداکثر پیشنهادات
        
        logger.info("Learning Manager initialized successfully")
    
    def _load_learning_profile(self) -> Dict[str, Any]:
        """بارگذاری پروفایل یادگیری از فایل"""
        default_profile = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_tasks": 0,
            "successful_tasks": 0,
            "patterns": {},  # الگوهای تخلفات
            "agent_performance": {},  # عملکرد هر ایجنت
            "task_history": [],  # تاریخچه وظایف
            "heuristics": {  # وزن‌دهی الگوها
                "print_removal_weight": 0.8,
                "type_hint_weight": 0.6,
                "hardcode_removal_weight": 0.9,
                "import_fix_weight": 0.5,
                "complexity_weight": 0.7
            },
            "learning_insights": []
        }
        
        try:
            if self.profile_path.exists():
                with open(self.profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    # ادغام با تنظیمات پیش‌فرض
                    for key, value in default_profile.items():
                        if key not in profile:
                            profile[key] = value
                    return profile
            else:
                return default_profile
        except Exception as e:
            logger.error(f"Error loading learning profile: {e}")
            return default_profile
    
    def _save_learning_profile(self) -> None:
        """ذخیره پروفایل یادگیری در فایل"""
        try:
            self.learning_data["last_updated"] = datetime.now().isoformat()
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2, ensure_ascii=False)
            logger.debug("Learning profile saved successfully")
        except Exception as e:
            logger.error(f"Error saving learning profile: {e}")
    
    def record_result(self, task_name: str, success: bool, score: int, 
                     agent_name: str = None, execution_time: float = None,
                     violations: List[str] = None) -> None:
        """ثبت نتیجه یک وظیفه برای یادگیری
        
        Args:
            task_name: نام وظیفه (مثل 'print_removal', 'type_hint_addition')
            success: موفق بودن وظیفه
            score: امتیاز نهایی (0-100)
            agent_name: نام ایجنت اجراکننده
            execution_time: زمان اجرا به ثانیه
            violations: لیست تخلفات پردازش شده
        """
        
        # به‌روزرسانی آمار کلی
        self.learning_data["total_tasks"] += 1
        if success:
            self.learning_data["successful_tasks"] += 1
        
        # ثبت در تاریخچه
        task_record = {
            "timestamp": datetime.now().isoformat(),
            "task_name": task_name,
            "success": success,
            "score": score,
            "agent_name": agent_name,
            "execution_time": execution_time,
            "violations": violations or []
        }
        
        self.learning_data["task_history"].append(task_record)
        
        # نگهداری فقط 1000 رکورد اخیر
        if len(self.learning_data["task_history"]) > 1000:
            self.learning_data["task_history"] = \
                self.learning_data["task_history"][-1000:]
        
        # به‌روزرسانی الگوهای تخلفات
        self._update_patterns(task_name, success, score, violations)
        
        # به‌روزرسانی عملکرد ایجنت
        if agent_name:
            self._update_agent_performance(agent_name, success, score, 
                                         execution_time, task_name)
        
        # تنظیم وزن‌های heuristic
        self._adjust_heuristics(task_name, success, score)
        
        # ذخیره تغییرات
        self._save_learning_profile()
        
        logger.info(f"Recorded task result: {task_name} = {success} " + 
                   f"(score: {score}, agent: {agent_name})")
    
    def _update_patterns(self, task_name: str, success: bool, score: int,
                        violations: List[str] = None) -> None:
        """به‌روزرسانی الگوهای یادگیری شده"""
        
        if task_name not in self.learning_data["patterns"]:
            self.learning_data["patterns"][task_name] = {
                "total_attempts": 0,
                "successful_attempts": 0,
                "average_score": 0,
                "common_violations": Counter(),
                "difficulty_score": 0.5,  # 0=آسان, 1=سخت
                "last_seen": datetime.now().isoformat()
            }
        
        pattern = self.learning_data["patterns"][task_name]
        pattern["total_attempts"] += 1
        pattern["last_seen"] = datetime.now().isoformat()
        
        if success:
            pattern["successful_attempts"] += 1
        
        # محاسبه میانگین امتیاز
        total_score = pattern["average_score"] * (pattern["total_attempts"] - 1)
        pattern["average_score"] = (total_score + score) / pattern["total_attempts"]
        
        # به‌روزرسانی تخلفات رایج
        if violations:
            pattern["common_violations"].update(violations)
        
        # محاسبه سختی بر اساس نرخ موفقیت
        success_rate = pattern["successful_attempts"] / pattern["total_attempts"]
        pattern["difficulty_score"] = 1.0 - success_rate
    
    def _update_agent_performance(self, agent_name: str, success: bool, 
                                score: int, execution_time: float = None,
                                task_name: str = None) -> None:
        """به‌روزرسانی عملکرد ایجنت"""
        
        if agent_name not in self.learning_data["agent_performance"]:
            self.learning_data["agent_performance"][agent_name] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "average_score": 0,
                "average_execution_time": 0,
                "specialties": Counter(),  # تخصص‌های ایجنت
                "strengths": [],  # نقاط قوت
                "weaknesses": []  # نقاط ضعف
            }
        
        agent_perf = self.learning_data["agent_performance"][agent_name]
        agent_perf["total_tasks"] += 1
        
        if success:
            agent_perf["successful_tasks"] += 1
            
            # اگر امتیاز بالاست، این task را به تخصص‌ها اضافه کن
            if score >= 85 and task_name:
                agent_perf["specialties"][task_name] += 1
        
        # به‌روزرسانی میانگین امتیاز
        total_score = agent_perf["average_score"] * (agent_perf["total_tasks"] - 1)
        agent_perf["average_score"] = (total_score + score) / agent_perf["total_tasks"]
        
        # به‌روزرسانی میانگین زمان اجرا
        if execution_time:
            if agent_perf["average_execution_time"] == 0:
                agent_perf["average_execution_time"] = execution_time
            else:
                total_time = agent_perf["average_execution_time"] * \
                           (agent_perf["total_tasks"] - 1)
                agent_perf["average_execution_time"] = \
                    (total_time + execution_time) / agent_perf["total_tasks"]
        
        # تشخیص نقاط قوت و ضعف
        success_rate = agent_perf["successful_tasks"] / agent_perf["total_tasks"]
        
        if success_rate >= 0.8 and task_name and task_name not in agent_perf["strengths"]:
            if len(agent_perf["strengths"]) < 5:  # حداکثر 5 نقطه قوت
                agent_perf["strengths"].append(task_name)
        elif success_rate < 0.5 and task_name and task_name not in agent_perf["weaknesses"]:
            if len(agent_perf["weaknesses"]) < 3:  # حداکثر 3 نقطه ضعف
                agent_perf["weaknesses"].append(task_name)
    
    def suggest_actions(self) -> List[str]:
        """پیشنهاد اقدامات بر اساس یادگیری‌های انجام شده
        
        Returns:
            لیست پیشنهادات برای بهبود
        """
        suggestions = []
        
        # تحلیل الگوهای پرتکرار
        frequent_patterns = []
        for pattern_name, pattern_data in self.learning_data["patterns"].items():
            if pattern_data["total_attempts"] >= self.pattern_threshold:
                success_rate = (pattern_data["successful_attempts"] / 
                              pattern_data["total_attempts"])
                
                if success_rate < self.success_threshold:
                    frequent_patterns.append({
                        "name": pattern_name,
                        "attempts": pattern_data["total_attempts"],
                        "success_rate": success_rate,
                        "avg_score": pattern_data["average_score"],
                        "difficulty": pattern_data["difficulty_score"]
                    })
        
        # مرتب‌سازی بر اساس اولویت (تکرار × سختی)
        frequent_patterns.sort(
            key=lambda x: x["attempts"] * x["difficulty"], 
            reverse=True
        )
        
        # تولید پیشنهادات
        for pattern in frequent_patterns[:5]:  # 5 pattern اول
            if pattern["success_rate"] < 0.5:
                suggestions.append(
                    f"Pattern '{pattern['name']}' needs attention: "
                    f"{pattern['attempts']} attempts with "
                    f"{pattern['success_rate']:.1%} success rate"
                )
            elif pattern["avg_score"] < 70:
                suggestions.append(
                    f"Improve quality for '{pattern['name']}': "
                    f"Average score is {pattern['avg_score']:.1f}"
                )
        
        # تحلیل عملکرد ایجنت‌ها
        for agent_name, agent_data in self.learning_data["agent_performance"].items():
            if agent_data["total_tasks"] >= 5:
                success_rate = (agent_data["successful_tasks"] / 
                              agent_data["total_tasks"])
                
                if success_rate < 0.6:
                    suggestions.append(
                        f"Agent '{agent_name}' underperforming: "
                        f"{success_rate:.1%} success rate"
                    )
                elif agent_data["average_execution_time"] > 30:  # بیش از 30 ثانیه
                    suggestions.append(
                        f"Agent '{agent_name}' is slow: "
                        f"{agent_data['average_execution_time']:.1f}s average"
                    )
        
        # اگر پیشنهادی نیست
        if not suggestions:
            if self.learning_data["total_tasks"] > 0:
                overall_success = (self.learning_data["successful_tasks"] / 
                                 self.learning_data["total_tasks"])
                if overall_success >= 0.8:
                    suggestions.append(
                        f"System performing well: {overall_success:.1%} success rate"
                    )
                else:
                    suggestions.append("General improvement needed across all areas")
            else:
                suggestions.append("No data available yet - run more validations")
        
        return suggestions[:self.max_suggestions]
    
    def get_best_agent_for_task(self, task_name: str) -> Optional[str]:
        """پیشنهاد بهترین ایجنت برای یک وظیفه خاص
        
        Args:
            task_name: نام وظیفه
            
        Returns:
            نام بهترین ایجنت یا None
        """
        best_agent = None
        best_score = 0
        
        for agent_name, agent_data in self.learning_data["agent_performance"].items():
            if agent_data["total_tasks"] >= 3:  # حداقل تجربه
                
                # بررسی تخصص در این نوع کار
                specialty_count = agent_data["specialties"].get(task_name, 0)
                success_rate = (agent_data["successful_tasks"] / 
                              agent_data["total_tasks"])
                
                # محاسبه امتیاز ترکیبی
                score = (success_rate * 0.6 + 
                        min(specialty_count / 5.0, 1.0) * 0.4) * \
                        agent_data["average_score"] / 100
                
                if score > best_score:
                    best_score = score
                    best_agent = agent_name
        
        return best_agent