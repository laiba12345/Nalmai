from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

DEFAULT_DB = Path(__file__).parents[1] / "data" / "nalmai.db"


class MasteryMemory:
    """SQLite source of truth; model reasoning remains outside this repository."""

    def __init__(self, path: str | Path = DEFAULT_DB):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock(); self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                existed = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='mastery_states'").fetchone() is not None
                connection.execute("""
                CREATE TABLE IF NOT EXISTS mastery_states (
                    student_id TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    mastery REAL NOT NULL,
                    observations INTEGER NOT NULL,
                    correct INTEGER NOT NULL,
                    soft_updates INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (student_id, concept)
                )
                """)
                connection.execute("CREATE TABLE IF NOT EXISTS model_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                connection.execute("""CREATE TABLE IF NOT EXISTS participant_profiles (
                    subject_id TEXT NOT NULL, role TEXT NOT NULL, display_name TEXT NOT NULL,
                    updated_at TEXT NOT NULL, PRIMARY KEY (subject_id, role)
                )""")
                connection.execute("""CREATE TABLE IF NOT EXISTS teaching_outcomes (
                    teacher_id TEXT NOT NULL, session_id TEXT NOT NULL, nudge_id TEXT NOT NULL,
                    concept TEXT NOT NULL, strategy TEXT NOT NULL, implementation_status TEXT NOT NULL,
                    correctness_delta REAL, recorded_at TEXT NOT NULL,
                    PRIMARY KEY (teacher_id, session_id, nudge_id)
                )""")
                boundary = connection.execute("SELECT value FROM model_metadata WHERE key='individual_evidence_boundary'").fetchone()
                if existed and boundary is None:
                    # Legacy states mixed class-wide CCS into every learner and
                    # cannot be reconstructed faithfully from aggregates.
                    connection.execute("DELETE FROM mastery_states")
                connection.execute("INSERT OR REPLACE INTO model_metadata (key, value) VALUES ('individual_evidence_boundary', 'v2')")

    def load_states(self) -> dict[tuple[str, str], dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT * FROM mastery_states").fetchall()
        return {(row["student_id"], row["concept"]): dict(row) for row in rows}

    def save_state(self, student_id: str, concept: str, state) -> None:
        updated_at = datetime.now(timezone.utc).isoformat()
        with self._lock, closing(self._connect()) as connection:
            with connection:
                connection.execute("""
                INSERT INTO mastery_states (student_id, concept, mastery, observations, correct, soft_updates, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, concept) DO UPDATE SET
                    mastery=excluded.mastery, observations=excluded.observations,
                    correct=excluded.correct, soft_updates=excluded.soft_updates,
                    updated_at=excluded.updated_at
                """, (student_id, concept, state.mastery, state.observations, state.correct, state.soft_updates, updated_at))

    def save_profile(self, subject_id: str, role: str, display_name: str) -> None:
        if role not in {"teacher", "student"}:
            raise ValueError("role must be teacher or student")
        with self._lock, closing(self._connect()) as connection:
            with connection:
                connection.execute("""INSERT INTO participant_profiles VALUES (?, ?, ?, ?)
                    ON CONFLICT(subject_id, role) DO UPDATE SET display_name=excluded.display_name,
                    updated_at=excluded.updated_at""",
                    (subject_id, role, display_name, datetime.now(timezone.utc).isoformat()))

    def save_teaching_outcomes(self, teacher_id: str, session_id: str, outcomes: list[dict]) -> None:
        with self._lock, closing(self._connect()) as connection:
            with connection:
                for outcome in outcomes:
                    connection.execute("""INSERT OR REPLACE INTO teaching_outcomes VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
                        teacher_id, session_id, outcome["nudge_id"], outcome["concept"], outcome["strategy"],
                        outcome["implementation_status"], outcome["correctness_delta"], datetime.now(timezone.utc).isoformat(),
                    ))

    def performance_summary(self, subject_id: str, role: str) -> dict:
        with closing(self._connect()) as connection:
            profile = connection.execute(
                "SELECT display_name FROM participant_profiles WHERE subject_id=? AND role=?", (subject_id, role),
            ).fetchone()
            if role == "student":
                rows = connection.execute(
                    "SELECT concept, mastery, observations, correct, soft_updates, updated_at FROM mastery_states WHERE student_id=? ORDER BY concept",
                    (subject_id,),
                ).fetchall()
                return {"subject_id": subject_id, "role": role, "display_name": profile[0] if profile else subject_id,
                        "concepts": [dict(row) for row in rows]}
            rows = connection.execute(
                "SELECT session_id, strategy, implementation_status, correctness_delta FROM teaching_outcomes WHERE teacher_id=?", (subject_id,),
            ).fetchall()
        strategies = {}
        for row in rows:
            item = strategies.setdefault(row["strategy"], {"attempts": 0, "implemented": 0, "observed_deltas": []})
            item["attempts"] += 1
            item["implemented"] += row["implementation_status"] == "implemented"
            if row["correctness_delta"] is not None:
                item["observed_deltas"].append(row["correctness_delta"])
        for item in strategies.values():
            values = item.pop("observed_deltas")
            item["mean_observed_delta"] = round(sum(values) / len(values), 3) if values else None
        return {"subject_id": subject_id, "role": role, "display_name": profile[0] if profile else subject_id,
                "sessions_with_nudges": len({row["session_id"] for row in rows}),
                "strategies": strategies, "limitations": "Observed implementation and next-check changes are not causal proof of teaching improvement."}

    def teaching_memory_context(self, teacher_id: str | None, student_ids: list[str], concept: str) -> dict:
        students = []
        for student_id in student_ids:
            summary = self.performance_summary(student_id, "student")
            students.append({"student_id": student_id, "concept_history": [
                row for row in summary.get("concepts", []) if row["concept"] == concept
            ]})
        teacher = {"teacher_id": teacher_id, "strategies": {}}
        if teacher_id:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    "SELECT strategy, implementation_status, correctness_delta FROM teaching_outcomes WHERE teacher_id=? AND concept=?",
                    (teacher_id, concept),
                ).fetchall()
            for row in rows:
                item = teacher["strategies"].setdefault(row["strategy"], {"attempts": 0, "implemented": 0, "observed_deltas": []})
                item["attempts"] += 1
                item["implemented"] += row["implementation_status"] == "implemented"
                if row["correctness_delta"] is not None:
                    item["observed_deltas"].append(row["correctness_delta"])
            for item in teacher["strategies"].values():
                values = item.pop("observed_deltas")
                item["mean_observed_delta"] = round(sum(values) / len(values), 3) if values else None
        return {"available": bool(any(x["concept_history"] for x in students) or teacher["strategies"]),
                "concept": concept, "students": students, "teacher": teacher}


def build_memory() -> MasteryMemory | None:
    if os.getenv("NALMAI_MEMORY_MODE", "on").lower() == "off":
        return None
    return MasteryMemory(os.getenv("NALMAI_DB", str(DEFAULT_DB)))
