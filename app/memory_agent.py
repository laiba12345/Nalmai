from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TeacherMemoryAgent:
    """Retrieval boundary for model-assisted, cross-session teaching memory."""

    memory: object
    teacher_id: str | None
    student_ids: list[str]

    def context(self, concept: str) -> dict:
        if not self.memory:
            return {"available": False, "concept": concept, "students": [], "teacher": {}}
        return self.memory.teaching_memory_context(self.teacher_id, self.student_ids, concept)
