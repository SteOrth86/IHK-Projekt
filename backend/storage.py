# storage.py
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from config import INSTANCES_FILE


class Instance(BaseModel):
    id: str                    # z.B. "wp-demo1"
    type: str                  # "wordpress" oder später "odoo"
    namespace: str             # z.B. "wp-demo1"
    domain: str                # z.B. "demo1.local"
    created_at: datetime
    updated_at: datetime
    status: str = "unknown"    # wird später mit kubectl aktualisiert


class InstanceStore:
    """Einfache JSON-basierte Persistenz für Instanzen."""

    def __init__(self, path: Path):
        self.path = path
        self._instances: List[Instance] = []
        self.load()

    def load(self) -> None:
        """Instanzen aus JSON lesen (falls Datei existiert)."""
        if self.path.exists():
            raw = self.path.read_text(encoding="utf-8")
            if raw.strip():
                data = json.loads(raw)
                self._instances = [Instance(**item) for item in data]
            else:
                self._instances = []
        else:
            self._instances = []

    def save(self) -> None:
        """Instanzen in JSON schreiben."""
        data = [inst.model_dump(mode="json") for inst in self._instances]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_instances(self, type_filter: Optional[str] = None) -> List[Instance]:
        if type_filter:
            return [i for i in self._instances if i.type == type_filter]
        return list(self._instances)

    def get_instance(self, instance_id: str) -> Optional[Instance]:
        for inst in self._instances:
            if inst.id == instance_id:
                return inst
        return None

    def add_instance(self, instance: Instance) -> None:
        # einfache Duplikats-Prüfung
        if self.get_instance(instance.id) is not None:
            raise ValueError(f"Instance with id '{instance.id}' already exists.")
        self._instances.append(instance)
        self.save()

    def remove_instance(self, instance_id: str) -> bool:
        before = len(self._instances)
        self._instances = [i for i in self._instances if i.id != instance_id]
        changed = len(self._instances) != before
        if changed:
            self.save()
        return changed

    def update_instance(self, instance: Instance) -> None:
        """Instanz ersetzen (z.B. wenn sich der Status geändert hat)."""
        for idx, inst in enumerate(self._instances):
            if inst.id == instance.id:
                self._instances[idx] = instance
                self.save()
                return
        # wenn nicht gefunden, neu anlegen
        self._instances.append(instance)
        self.save()

# Globaler Store, den alle Module (main + Router) benutzen
store = InstanceStore(INSTANCES_FILE)
