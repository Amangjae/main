"""성능 측정 유틸리티"""
import time
import streamlit as st
from functools import wraps
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PerformanceTracker:
    """성능 측정 및 로깅"""
    
    def __init__(self):
        self.timings = {}
    
    def record(self, name: str, duration: float) -> None:
        """측정 시간 기록"""
        if name not in self.timings:
            self.timings[name] = []
        self.timings[name].append(duration)
        logger.info(f"⏱️  {name}: {duration:.2f}ms")
    
    def summary(self) -> None:
        """성능 요약 출력"""
        total = sum(sum(times) for times in self.timings.values())
        st.write("### ⏱️ 성능 측정 (개발 모드)")
        for name, times in sorted(self.timings.items()):
            avg_time = sum(times) / len(times)
            st.write(f"- {name}: {avg_time:.2f}ms (실행 {len(times)}회)")
        st.write(f"**총 소요 시간: {total:.2f}ms**")


_tracker = PerformanceTracker()


def measure_performance(name: str):
    """성능 측정 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = (time.time() - start) * 1000  # ms로 변환
            _tracker.record(name, duration)
            return result
        return wrapper
    return decorator


def get_tracker() -> PerformanceTracker:
    """성능 추적기 반환"""
    return _tracker
