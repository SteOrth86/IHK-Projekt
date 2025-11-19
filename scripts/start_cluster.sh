#!/usr/bin/env bash

set -euo pipefail

echo ">>> Starte Minikube-Cluster für das IHK-Projekt..."

# Minikube starten (Parameter wie im Projekt benutzt)
minikube start --cpus=4 --memory=3072 --disk-size=40g

echo
echo ">>> Cluster-Status:"
kubectl get nodes

echo
echo ">>> Ingress-Addon sicherstellen..."
minikube addons enable ingress

echo
echo ">>> Ingress-Controller:"
kubectl get pods -n ingress-nginx

echo
echo ">>> Helm-Repos aktualisieren..."
helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
helm repo update

echo
echo ">>> Speicherklassen:"
kubectl get storageclass

echo
echo ">>> Fertig. Cluster ist bereit für Provisionierung."
