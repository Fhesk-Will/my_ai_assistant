import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LifeLedger:
    """人生经历账本 - append-only .jsonl 格式存储"""

    def __init__(self, memory_dir: str):
        self.file_path = os.path.join(memory_dir, "life_ledger.jsonl")
        os.makedirs(memory_dir, exist_ok=True)

    def append(self, event_type: str, content: str, metadata: dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "content": content,
            "metadata": metadata or {},
        }
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def query(self, start_date: str = None, end_date: str = None,
              event_type: str = None, limit: int = 50) -> list[dict]:
        if not os.path.exists(self.file_path):
            return []

        results = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event_type and entry.get("type") != event_type:
                    continue
                if start_date and entry.get("timestamp", "") < start_date:
                    continue
                if end_date and entry.get("timestamp", "") > end_date:
                    continue

                results.append(entry)

        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]

    def get_recent(self, limit: int = 20) -> list[dict]:
        return self.query(limit=limit)

    def get_stats(self) -> dict:
        if not os.path.exists(self.file_path):
            return {"total_entries": 0, "types": {}}

        total = 0
        types = {}
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    total += 1
                    t = entry.get("type", "unknown")
                    types[t] = types.get(t, 0) + 1
                except json.JSONDecodeError:
                    continue

        return {"total_entries": total, "types": types}
