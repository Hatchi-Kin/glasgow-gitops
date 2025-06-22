# Glasgow GitOps

A concise GitOps setup for a multi-node K3s homelab with ArgoCD, FastAPI, MinIO, and PostgreSQL.

## 🚀 Quick Start

- [Install K3s](./admin/01_install_k3s.md)
- [Install ArgoCD](./admin/02_install_argocd.md)
- [Restart Guide](./admin/README-restart.md)
- [Troubleshooting](./DOCS.md)

## Cluster Nodes

| Hostname   | Role           | Specs           | IP              |
|------------|----------------|-----------------|-----------------|
| adama      | control plane  | i5-7200U, 8GB   | 192.168.1.20    |
| boomer     | worker         | N150, 16GB      | 192.168.1.21    |
| apollo     | worker         | N150, 16GB      | 192.168.1.22    |
| starbuck   | worker         | N150, 16GB      | 192.168.1.23    |

## 📱 Web UIs & Access

| Service   | How to Access                        | Description         |
|-----------|--------------------------------------|---------------------|
| ArgoCD    | `kubectl port-forward svc/argocd-server -n argocd 8080:443` → [localhost:8080](http://localhost:8080) | GitOps dashboard    |
| FastAPI   | [api.glasgow.local/docs](http://api.glasgow.local/docs) | API docs            |
| MinIO     | `kubectl port-forward svc/minio -n minio 9001:9001` → [localhost:9001](http://localhost:9001) | Object storage UI   |

## 📂 Docs

- [`argocd/README.md`](./argocd/README.md): ArgoCD usage & port-forwarding
- [`admin/README-secrets.md`](./admin/README-secrets.md): Secrets management
- [`admin/README-kubectl.md`](./admin/README-kubectl.md): kubectl quick reference
- [`components/minio/README.md`](./components/minio/README.md): MinIO UI access

---