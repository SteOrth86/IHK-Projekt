from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="IHK Provisioning Backend",
    description="Backend zum Provisionieren von WordPress-Instanzen auf dem Minikube-Cluster.",
    version="0.1.0",
)


class WPInstance(BaseModel):
    slug: str
    namespace: str
    hostname: str
    status: str = "unknown"


# vorerst Dummy-Liste für Testzwecke
DUMMY_INSTANCES = [
    WPInstance(slug="kunde1", namespace="wp-kunde1", hostname="kunde1.local", status="running"),
    WPInstance(slug="kunde2", namespace="wp-kunde2", hostname="kunde2.local", status="running"),
]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/instances/wp", response_model=List[WPInstance])
def list_wp_instances():
    # später holen wir echte Daten (helm/kubectl/json-file)
    return DUMMY_INSTANCES
