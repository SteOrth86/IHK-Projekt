from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

import config
from models import Order

class Instance(BaseModel):
    id: str
    type: str          # "wordpress" oder "odoo"
    namespace: str
    domain: str
    created_at: str
    updated_at: str
    status: str        # z.B. "creating", "running", "error", "deleting"


class InstanceStore:
    """
    Verwaltet die Instanzen in einer JSON-Datei (instances.json).

    – Datei liegt unter config.INSTANCES_FILE
    – Jede Operation lädt/schreibt die Datei komplett (für dein Projekt vollkommen ok).
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        # Ordner sicherstellen
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Datei anlegen, falls sie nicht existiert
        if not self.path.exists():
            self._save_raw([])

    # ---------- interne Helpers für Rohdaten ----------

    def _load_raw(self) -> list[dict]:
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

        if isinstance(data, list):
            return data
        return []

    def _save_raw(self, data: list[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---------- öffentliche API ----------

    def list(self) -> List[Instance]:
        """Gibt alle Instanzen als Liste von Instance-Objekten zurück."""
        return [Instance(**item) for item in self._load_raw()]

    # optionaler Alias, falls du ihn später brauchen solltest
    def list_instances(self) -> List[Instance]:
        return self.list()

    def get(self, instance_id: str) -> Optional[Instance]:
        """Gibt eine Instanz mit der ID zurück oder None."""
        for inst in self.list():
            if inst.id == instance_id:
                return inst
        return None

    def add(self, instance: Instance) -> None:
        """
        Fügt eine neue Instanz hinzu.
        Wenn die ID bereits existiert, wird ein Fehler geworfen.
        """
        instances = self.list()
        if any(i.id == instance.id for i in instances):
            raise ValueError(f"Instance with id {instance.id!r} already exists")
        instances.append(instance)
        self._save(instances)

    def update(self, instance: Instance) -> None:
        """
        Aktualisiert eine bestehende Instanz (matcht über id).
        Wirft KeyError, wenn die Instanz nicht existiert.
        """
        instances = self.list()
        for idx, inst in enumerate(instances):
            if inst.id == instance.id:
                instances[idx] = instance
                self._save(instances)
                return
        raise KeyError(f"Instance {instance.id!r} not found")

    def remove(self, instance_id: str) -> None:
        """
        Entfernt eine Instanz mit der gegebenen ID.
        Wenn keine gefunden wird, passiert einfach nichts.
        """
        instances = self.list()
        new_instances = [inst for inst in instances if inst.id != instance_id]
        if len(new_instances) == len(instances):
            # nichts geändert
            return
        self._save(new_instances)

    # ---------- Helper zum Speichern von Instance-Listen ----------

    def _save(self, instances: List[Instance]) -> None:
        self._save_raw([inst.model_dump() for inst in instances])

class OrderStore:
    """
    Verwaltet die Bestellungen in einer JSON-Datei (orders.json).

    – Datei liegt unter config.ORDERS_FILE
    – Jede Operation lädt/schreibt die Datei komplett (für dein Projekt ok).
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        # Ordner sicherstellen
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Datei anlegen, falls sie nicht existiert
        if not self.path.exists():
            self._save_raw([])

    # ---------- interne Helpers für Rohdaten ----------

    def _load_raw(self) -> list[dict]:
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

        if isinstance(data, list):
            return data
        return []

    def _save_raw(self, data: list[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ---------- öffentliche API ----------

    def list(self) -> List[Order]:
        """Gibt alle Bestellungen als Liste von Order-Objekten zurück."""
        return [Order(**item) for item in self._load_raw()]

    def get(self, order_id: str) -> Optional[Order]:
        """Gibt eine Bestellung mit der ID zurück oder None."""
        for order in self.list():
            if order.id == order_id:
                return order
        return None

    def add(self, order: Order) -> None:
        """
        Fügt eine neue Bestellung hinzu.
        Wenn die ID bereits existiert, wird ein Fehler geworfen.
        """
        orders = self.list()
        if any(o.id == order.id for o in orders):
            raise ValueError(f"Order with id {order.id!r} already exists")
        orders.append(order)
        self._save(orders)

    def update(self, order: Order) -> None:
        """
        Aktualisiert eine bestehende Bestellung (matcht über id).
        Wirft KeyError, wenn die Bestellung nicht existiert.
        """
        orders = self.list()
        for idx, existing in enumerate(orders):
            if existing.id == order.id:
                orders[idx] = order
                self._save(orders)
                return
        raise KeyError(f"Order {order.id!r} not found")

    # ---------- Helper zum Speichern von Order-Listen ----------

    def _save(self, orders: List[Order]) -> None:
        data = [order.model_dump(mode="json") for order in orders]
        self._save_raw(data)


# Globaler Store, wie von dir beschrieben
store = InstanceStore(config.INSTANCES_FILE)
orders_store = OrderStore(config.ORDERS_FILE)
