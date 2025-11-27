from __future__ import annotations

import json
from pathlib import Path
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

from kube_app_provisioner.core import config
from kube_app_provisioner.core.models import Order

ModelT = TypeVar("ModelT", bound=BaseModel)


class Instance(BaseModel):
    id: str
    type: str  # "wordpress" oder "odoo"
    namespace: str
    domain: str
    created_at: str
    updated_at: str
    status: str  # z.B. "creating", "running", "error", "deleting"

    suspended: bool = False
    suspend_reason: Optional[str] = None


class JsonStore(Generic[ModelT]):
    """
    Generischer JSON-Store fuer Pydantic-Modelle.

    - laedt/schreibt die komplette Liste pro Operation
    - stellt CRUD-Operationen bereit
    """

    item_label: str = "Item"

    def __init__(self, path: str | Path, model_cls: type[ModelT]) -> None:
        self.path = Path(path)
        self.model_cls = model_cls
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save_raw([])

    # ---------- interne Helpers fuer Rohdaten ----------

    def _load_raw(self) -> list[dict]:
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        if isinstance(data, list):
            return data
        return []

    def _save_raw(self, data: list[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _serialize(self, item: ModelT) -> dict:
        return item.model_dump()

    def _validate_before_add(self, item: ModelT, existing: List[ModelT]) -> None:
        """
        Hook fuer spezifische Validierungen (z. B. Domain-Eindeutigkeit).
        Default: keine zusaetzliche Validierung.
        """
        return None

    # ---------- oeffentliche API ----------

    def list(self) -> List[ModelT]:
        return [self.model_cls(**item) for item in self._load_raw()]

    def get(self, item_id: str) -> Optional[ModelT]:
        for item in self.list():
            if getattr(item, "id", None) == item_id:
                return item
        return None

    def id_exists(self, item_id: str) -> bool:
        return self.get(item_id) is not None

    def add(self, item: ModelT) -> None:
        items = self.list()
        item_id = getattr(item, "id", None)
        if any(getattr(i, "id", None) == item_id for i in items):
            raise ValueError(f"{self.item_label} '{item_id}' already exists")

        self._validate_before_add(item, items)
        items.append(item)
        self._save(items)

    def update(self, item: ModelT) -> None:
        items = self.list()
        item_id = getattr(item, "id", None)
        for idx, existing in enumerate(items):
            if getattr(existing, "id", None) == item_id:
                items[idx] = item
                self._save(items)
                return
        raise KeyError(f"{self.item_label} {item_id!r} not found")

    def remove(self, item_id: str) -> None:
        items = self.list()
        new_items = [item for item in items if getattr(item, "id", None) != item_id]
        if len(new_items) == len(items):
            return
        self._save(new_items)

    # ---------- Helper zum Speichern ----------

    def _save(self, items: List[ModelT]) -> None:
        self._save_raw([self._serialize(item) for item in items])


class InstanceStore(JsonStore[Instance]):
    item_label = "Instance"

    def __init__(self, path: str | Path) -> None:
        super().__init__(path, model_cls=Instance)

    def _validate_before_add(self, item: Instance, existing: List[Instance]) -> None:
        normalized_domain = item.domain.strip().lower()
        if any(inst.domain.strip().lower() == normalized_domain for inst in existing):
            raise ValueError(
                f"Domain '{item.domain}' wird bereits von einer anderen Instanz verwendet"
            )

    def domain_exists(self, domain: str) -> bool:
        normalized = domain.strip().lower()
        return any(inst.domain.strip().lower() == normalized for inst in self.list())


class OrderStore(JsonStore[Order]):
    item_label = "Order"

    def __init__(self, path: str | Path) -> None:
        super().__init__(path, model_cls=Order)

    def _serialize(self, item: Order) -> dict:
        return item.model_dump(mode="json")


# Globale Stores, wie von dir beschrieben
store = InstanceStore(config.INSTANCES_FILE)
orders_store = OrderStore(config.ORDERS_FILE)
