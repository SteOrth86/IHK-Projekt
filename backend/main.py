from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict
from pathlib import Path
import re
import subprocess

app = FastAPI(
    title="IHK Provisioning Backend",
    description="Backend zum Provisionieren von WordPress-Instanzen auf dem Minikube-Cluster.",
    version="0.2.0",
)


# ---------- Modelle ----------

class WPInstance(BaseModel):
    slug: str
    namespace: str
    hostname: str
    status: str = "unknown"


class WPInstanceCreate(BaseModel):
    slug: str = Field(..., description="Kurzname des Kunden, z.B. 'kunde1'")

    def normalized_slug(self) -> str:
        s = self.slug.strip().lower()
        # erlauben: buchstaben, zahlen, bindestrich
        if not re.fullmatch(r"[a-z0-9-]+", s):
            raise ValueError(
                "Slug darf nur Kleinbuchstaben, Ziffern und '-' enthalten, z.B. 'kunde1'"
            )
        if len(s) < 3:
            raise ValueError("Slug muss mindestens 3 Zeichen lang sein.")
        return s


# einfache In-Memory-Ablage für Instanzen (für IHK völlig OK)
instances: Dict[str, WPInstance] = {}


# Projekt-Wurzel: backend/ -> eine Ebene hoch
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


# ---------- Hilfsfunktionen ----------

def run_script(script_name: str, slug: str) -> None:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise RuntimeError(f"Skript {script_path} nicht gefunden.")

    # Skript aufrufen, Fehler durchreichen
    result = subprocess.run(
        [str(script_path), slug],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Skript {script_name} fehlgeschlagen (Exit {result.returncode}):\n"
            f"{result.stderr}"
        )


def build_instance(slug: str) -> WPInstance:
    ns = f"wp-{slug}"
    host = f"{slug}.local"
    return WPInstance(
        slug=slug,
        namespace=ns,
        hostname=host,
        status="provisioning",  # Anfangsstatus
    )

def get_instance_status(namespace: str) -> str:
    """
    Liest den Status der Pods in einem Namespace aus und gibt einen einfachen
    Gesamtstatus zurück: 'running', 'pending' oder 'error'.
    """
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "jsonpath={.items[*].status.phase}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            # z.B. Namespace existiert nicht (mehr)
            return "unknown"

        phases = result.stdout.strip().split()
        if not phases:
            return "unknown"

        phases_set = set(phases)
        # Wenn irgendein Pod 'Failed' ist → error
        if "Failed" in phases_set or "CrashLoopBackOff" in result.stdout:
            return "error"
        # Wenn alle 'Running' → running
        if phases_set == {"Running"}:
            return "running"
        # Sonst z.B. Pending/ContainerCreating → pending
        if "Pending" in phases_set:
            return "pending"

        # Fallback
        return "unknown"
    except Exception:
        return "unknown"
# ---------- Endpoints ----------

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/instances/wp", response_model=List[WPInstance])
def list_wp_instances():
    # Status für jede Instanz aus Kubernetes nachziehen
    for inst in instances.values():
        inst.status = get_instance_status(inst.namespace)
    return list(instances.values())


@app.post(
    "/instances/wp",
    response_model=WPInstance,
    status_code=status.HTTP_201_CREATED,
)
def create_wp_instance(data: WPInstanceCreate):
    # Slug validieren und normalisieren
    try:
        slug = data.normalized_slug()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Doppelten Slug verhindern
    if slug in instances:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Instanz mit Slug '{slug}' existiert bereits.",
        )

    # Instanzmodell aufbauen
    instance = build_instance(slug)

    # Provisionierung im Cluster auslösen
    try:
        run_script("provision_wp.sh", slug)
    except RuntimeError as e:
        # Hier bewusst HTTP 500, weil das ein technischer Fehler im Cluster ist
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # Anfangsstatus setzen – genauerer Status kommt später über kubectl
    instance.status = "provisioning"
    instances[slug] = instance

    # WICHTIG: Instanz wirklich zurückgeben
    return instance


@app.get("/instances/wp", response_model=List[WPInstance])
def list_wp_instances():
    # Status für jede Instanz aus Kubernetes nachziehen
    for inst in instances.values():
        inst.status = get_instance_status(inst.namespace)
    return list(instances.values())
    if slug in instances:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Instanz mit Slug '{slug}' existiert bereits.",
        )

    instance = build_instance(slug)

    # Provisionierung auslösen
    try:
        run_script("provision_wp.sh", slug)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # Status erstmal 'provisioning' – später könnte man kubectl/helm fragen
    instance.status = "provisioning"
    instances[slug] = instance
    return instance


@app.get("/instances/wp/{slug}", response_model=WPInstance)
def get_wp_instance(slug: str):
    slug = slug.lower()
    if slug not in instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keine Instanz mit Slug '{slug}' gefunden.",
        )
    inst = instances[slug]
    inst.status = get_instance_status(inst.namespace)
    return inst



@app.delete(
    "/instances/wp/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_wp_instance(slug: str):
    slug = slug.lower()
    if slug not in instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keine Instanz mit Slug '{slug}' gefunden.",
        )

    # Löschen im Cluster
    try:
        run_script("delete_wp.sh", slug)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # Aus lokaler Ablage entfernen
    del instances[slug]
    return

