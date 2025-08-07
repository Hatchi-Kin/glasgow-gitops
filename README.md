# Glasgow GitOps Homelab 🏠

A complete K3s homelab setup with GitOps management using ArgoCD, persistent storage with Longhorn, and secure secret management with Sealed Secrets.

## �️ Architecture Overview

- **Kubernetes**: K3s v1.32.6+k3s1
- **GitOps**: ArgoCD for automated deployments
- **Storage**: Longhorn for persistent volumes
- **Ingress**: Traefik with nip.io for external access
- **Secrets**: Sealed Secrets for secure credential management
- **Applications**: Postgres, MinIO, FastAPI, n8n

## 🔐 Standardized Credentials

All services use consistent credentials for easier management:
- **Username**: `adama`
- **Password**: `commander`

## 🌐 Service Access

All services are accessible via your local network IP with nip.io:

| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI** | http://fastapi.192.168.1.20.nip.io | - |
| **MinIO Console** | http://minio.192.168.1.20.nip.io | `adama` / `commander` |
| **n8n Workflow** | http://n8n.192.168.1.20.nip.io | `Glasgow` / `Coloc` |
| **ArgoCD** | http://argocd.192.168.1.20.nip.io| `admin` / see admin password |

*Note: Replace `192.168.1.20` with your actual K3s node IP*

## 🚀 Quick Start

### Prerequisites
```bash
# K3s should be installed and running
sudo systemctl status k3s

# kubectl should be configured
kubectl get nodes
```

### Get ArgoCD Admin Password
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### Port Forward ArgoCD (if needed)

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## 📁 Repository Structure

```
glasgow-gitops/
├── admin/                      # Administrative scripts and docs
├── argocd/
│   ├── apps/                   # ArgoCD Application manifests
│   │   ├── fastapi.yaml
│   │   ├── glasgow-sealed-secrets.yaml
│   │   ├── longhorn.yaml
│   │   ├── minio.yaml
│   │   ├── n8n.yaml
│   │   ├── postgres.yaml
│   │   └── sealed-secrets.yaml
│   └── root-app.yaml          # Root Application (App of Apps pattern)
├── components/                 # Individual component manifests
│   ├── fastapi/
│   ├── longhorn/
│   ├── minio/
│   ├── n8n/
│   ├── postgres/
│   └── sealed-secrets/
└── sealed-secrets/            # Sealed Secret manifests
    ├── postgres-sealed-secret.yaml
    ├── minio-sealed-secret.yaml
    └── n8n-sealed-secret.yaml
```

## 🔧 What We Built

### 1. Core Infrastructure
- **K3s cluster** with 4 nodes for high availability
- **Longhorn storage** for persistent volumes with replication
- **Traefik ingress** for external access with automatic certificates

### 2. GitOps Setup
- **ArgoCD** for continuous deployment from Git
- **App of Apps pattern** for managing multiple applications
- **Automatic sync** with pruning and self-healing enabled

### 3. Applications Deployed
- **PostgreSQL**: Database server with persistent storage
- **MinIO**: S3-compatible object storage with web console
- **FastAPI**: Python web application
- **n8n**: Workflow automation platform

### 4. Security Implementation
- **Sealed Secrets** for encrypting sensitive data in Git
- **Standardized credentials** across all services
- **Namespace isolation** (all apps in `glasgow-prod`)

## 🛠️ Management Commands

### Check All Applications
```bash
kubectl get applications -n argocd
```

### Check All Pods
```bash
kubectl get pods -n glasgow-prod
```

### Check Persistent Volumes
```bash
kubectl get pv
kubectl get pvc -n glasgow-prod
```

### Check Sealed Secrets
```bash
kubectl get sealedsecrets -n glasgow-prod
kubectl get secrets -n glasgow-prod
```

### Force Sync an Application

```bash
kubectl patch application <app-name> -n argocd --type merge -p='{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}'
```

## 🔄 Adding New Applications

1. Create component manifests in `components/<app-name>/`
2. Create ArgoCD Application in `argocd/apps/<app-name>.yaml`
3. If secrets needed, create sealed secrets in `sealed-secrets/`
4. Commit and push - ArgoCD will automatically deploy

## 🔐 Managing Secrets

### Generate New Sealed Secrets
```bash
# Create regular secret (dry-run)
kubectl create secret generic <secret-name> \
  --from-literal=key=value \
  --namespace=glasgow-prod \
  --dry-run=client -o yaml | kubeseal -o yaml > sealed-secrets/<secret-name>-sealed-secret.yaml
```

### Update Existing Secrets
1. Generate new sealed secret with updated values
2. Commit to Git
3. ArgoCD will automatically apply changes

## 🏠 Network Configuration

- **Cluster IP Range**: Configured by K3s
- **External Access**: Via Traefik ingress
- **DNS**: Uses nip.io for development (no DNS server needed)
- **Load Balancer**: MetalLB for external service IPs

## 📊 Monitoring

Check application health via:
- ArgoCD UI: Application sync status and health
- Kubernetes: Pod status and logs
- Longhorn UI: Storage health and backups
- Service UIs: Application-specific monitoring

## 🔧 Troubleshooting

### Pod Not Starting
```bash
kubectl describe pod <pod-name> -n glasgow-prod
kubectl logs <pod-name> -n glasgow-prod
```

### Storage Issues
```bash
kubectl get pv,pvc -n glasgow-prod
# Check Longhorn UI for volume status
```

### Secret Issues
```bash
kubectl get sealedsecrets -n glasgow-prod
kubectl describe sealedsecret <secret-name> -n glasgow-prod
```

### ArgoCD Sync Issues
```bash
kubectl get application <app-name> -n argocd -o yaml
# Check status.conditions for error details
```

## 🎯 Next Steps

Potential improvements and additions:
- [ ] Add monitoring stack (Prometheus + Grafana)
- [ ] Set up automated backups via Longhorn
- [ ] Add SSL certificates via cert-manager
- [ ] Implement network policies for security
- [ ] Add more applications (databases, tools, etc.)
- [ ] Set up GitLab/GitHub Actions for CI/CD pipelines

## 📝 Notes

- All data is persistent and survives pod restarts
- Secrets are encrypted in Git via Sealed Secrets
- Applications auto-heal if manually modified
- Cluster can be reset/rebuilt while preserving GitOps config
- Use `adama`/`commander` for consistent service access

---

**Happy HomeLab-ing!** 🚀

*This setup provides a production-like environment for learning Kubernetes, GitOps, and cloud-native technologies.*

## ✅ Verification

**Check everything is running:**
```bash
# All applications should be Synced and Healthy
kubectl get applications -n argocd

# All nodes should be Ready
kubectl get nodes

# Test persistent storage works
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: longhorn
  resources:
    requests:
      storage: 1Gi
EOF

kubectl get pvc  # Should show Bound
kubectl delete pvc test-pvc  # Clean up
```

## 🔧 Key Features

- **GitOps**: All changes via Git commits, ArgoCD handles deployment
- **Persistent Storage**: Longhorn provides distributed storage across 3 worker nodes
- **High Availability**: Data replicated across multiple nodes
- **Web Access**: No port forwarding needed, access UIs from any device on network
- **Auto-Sync**: ArgoCD automatically deploys changes when you push to main branch

## 📚 Next Steps

Now you have a solid foundation! You can add applications with persistent storage:
- Postgres databases
- MinIO object storage  
- n8n workflow automation
- Any application needing persistent data

The backup of your previous working setup (without Longhorn) is preserved in the `backup-working-without-longhorn` branch.

---

**Network Info:**
- Control Plane: `adama` (192.168.1.20)
- Workers: `boomer` (192.168.1.21), `apollo` (192.168.1.22), `starbuck` (192.168.1.23)
