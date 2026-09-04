"""
QA Database Module
Lightweight SQLite persistence layer for logging QA engineer review decisions and audit histories.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    from config import QA_DB_PATH
except ImportError:
    QA_DB_PATH = Path("qa/qa_decisions.db")

from qa.decision import QADecision


class QADatabase:
    """Manages SQLite-based storage for QA inspection records and engineer decisions."""

    def __init__(self, db_path: Path = QA_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initializes QA decision schema if not exists."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS qa_decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        component_id TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        engineer_id TEXT NOT NULL,
                        notes TEXT,
                        timestamp TEXT NOT NULL,
                        UNIQUE(component_id, timestamp)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_component_id 
                    ON qa_decisions(component_id)
                    """
                )
        finally:
            conn.close()

    def record_decision(self, decision: QADecision) -> None:
        """Saves a QA decision record to the database."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO qa_decisions (component_id, decision, engineer_id, notes, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        decision.component_id,
                        decision.decision,
                        decision.engineer_id,
                        decision.notes,
                        decision.timestamp,
                    ),
                )
        finally:
            conn.close()

    def get_latest_decision(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent decision for a component."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT component_id, decision, engineer_id, notes, timestamp
                FROM qa_decisions
                WHERE component_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (component_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_decisions(self) -> List[Dict[str, Any]]:
        """Retrieves all QA decisions logged in the database."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT component_id, decision, engineer_id, notes, timestamp
                FROM qa_decisions
                ORDER BY timestamp DESC
                """
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

