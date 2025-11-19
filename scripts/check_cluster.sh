#!/usr/bin/env bash

set -euo pipefail

echo ">>> Node-Status:"
kubectl get nodes

echo
echo ">>> Ingress-Controller:"
kubectl get pods -n ingress-nginx

echo
echo ">>> StorageClasses:"
kubectl get storageclass

echo
echo ">>> Helm-Releases:"
helm list -A

echo
echo ">>> Namespaces:"
kubectl get ns
