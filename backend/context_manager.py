"""上下文窗口管理器 - 维护最近 N 句识别和翻译结果"""
from collections import deque
from dataclasses import dataclass, field


@dataclass
class SubtitleSegment:
    id: str
    start_time: float
    end_time: float
    source_text: str
    translated_text: str
    status: str = "final"        # interim | final | corrected
    version: int = 1


class ContextManager:
    def __init__(self, max_context: int = 5):
        self.max_context = max_context
        self.recent_source: deque[str] = deque(maxlen=max_context)
        self.recent_translated: deque[str] = deque(maxlen=max_context)
        self.segments: dict[str, SubtitleSegment] = {}
        self.topic: str = ""
        self.glossary: dict[str, str] = {}
        self._seg_counter: int = 0

    def add_segment(self, source_text: str, translated_text: str,
                    start_time: float = 0.0, end_time: float = 0.0) -> SubtitleSegment:
        self._seg_counter += 1
        seg = SubtitleSegment(
            id=f"seg_{self._seg_counter:04d}",
            start_time=start_time,
            end_time=end_time,
            source_text=source_text,
            translated_text=translated_text,
            status="final",
            version=1,
        )
        self.segments[seg.id] = seg
        self.recent_source.append(source_text)
        self.recent_translated.append(translated_text)
        return seg

    def update_segment(self, seg_id: str, new_translation: str) -> SubtitleSegment | None:
        seg = self.segments.get(seg_id)
        if seg is None:
            return None
        seg.translated_text = new_translation
        seg.status = "corrected"
        seg.version += 1
        return seg

    def get_recent_for_prompt(self) -> dict:
        return {
            "source": list(self.recent_source),
            "translated": list(self.recent_translated),
            "topic": self.topic,
            "glossary": self.glossary,
        }

    def set_config(self, topic: str = "", glossary: dict[str, str] | None = None):
        if topic:
            self.topic = topic
        if glossary is not None:
            self.glossary = glossary

    @property
    def last_segment(self) -> SubtitleSegment | None:
        if self._seg_counter == 0:
            return None
        return self.segments.get(f"seg_{self._seg_counter:04d}")
