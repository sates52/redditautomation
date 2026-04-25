import time
from datetime import datetime, timedelta
from typing import Dict


class RateLimiter:
    def __init__(self, min_hours_between_posts: int = 6):
        self.min_hours = min_hours_between_posts
        self.last_post_time = None
        self.post_count = 0
        self.reset_time = None
    
    def can_post(self) -> tuple:
        now = datetime.now()
        
        if self.last_post_time is None:
            return True, "OK"
        
        time_since_last = now - self.last_post_time
        min_interval = timedelta(hours=self.min_hours)
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            wait_minutes = int(wait_time.total_seconds() / 60)
            return False, f"Wait {wait_minutes} more minutes"
        
        return True, "OK"
    
    def record_post(self):
        self.last_post_time = datetime.now()
        self.post_count += 1


class CircuitBreaker:
    def __init__(self, max_failures: int = 3, reset_timeout: int = 300):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self) -> bool:
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.max_failures:
            self.is_open = True
            return True
        
        return False
    
    def can_proceed(self) -> tuple:
        if not self.is_open:
            return True, "OK"
        
        if self.last_failure_time:
            time_since_failure = datetime.now() - self.last_failure_time
            if time_since_failure.total_seconds() >= self.reset_timeout:
                self.is_open = False
                self.failure_count = 0
                return True, "Reset after timeout"
        
        return False, "Circuit breaker open"


class ContentSafety:
    @staticmethod
    def check_content_safety(content: str) -> tuple:
        issues = []
        
        if len(content) > 40000:
            issues.append("Content too long (max 40k chars)")
        
        if len(content.strip()) < 10:
            issues.append("Content too short (min 10 chars)")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def check_title_safety(title: str) -> tuple:
        issues = []
        
        if len(title) > 300:
            issues.append("Title too long (max 300 chars)")
        
        if len(title.strip()) < 5:
            issues.append("Title too short (min 5 chars)")
        
        return len(issues) == 0, issues
