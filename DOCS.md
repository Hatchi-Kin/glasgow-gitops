## 🚀 Glasgow GitOps - Quick Reference

### 📱 Web UIs

| Service | URL | Description |
|---------|-----|-------------|
| **ArgoCD** | `http://localhost:8080` | GitOps dashboard |
| **FastAPI** | `http://api.glasgow.local/docs` | API documentation |
| **Docker Hub** | `https://hub.docker.com/r/hatchikin/glasgow-fastapi` | Container registry |

### 🔑 Access ArgoCD UI
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Username: admin
# Password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```
### 🖥️ Tmux Workflow for ArgoCD

```bash
# Start new tmux session for port-forwarding
tmux new-session -d -s argocd-pf 'kubectl port-forward svc/argocd-server -n argocd 8080:443'

# Check if session is running
tmux list-sessions

# Access ArgoCD UI (in browser)
# http://localhost:8080

# Attach to session (see logs/status)
tmux attach-session -t argocd-pf

# Detach from session (Ctrl+B, then D)
# Session keeps running in background

# Kill session when done
tmux kill-session -t argocd-pf
```

**Benefits:**
- ✅ Port-forward runs in background
- ✅ Can close terminal, port-forward continues
- ✅ Easy to monitor connection status
- ✅ Quick attach/detach workflow

### 🔧 Essential Commands

```bash
# Check all pods status
kubectl get pods -A

# Sync ArgoCD applications
argocd app sync glasgow-gitops

# Restart FastAPI deployment
kubectl rollout restart deployment/fastapi -n fastapi-prod

# Port forward to FastAPI
kubectl port-forward svc/fastapi-service -n fastapi-prod 8081:8000

# Check application logs
kubectl logs -n fastapi-prod deployment/fastapi

# Update /etc/hosts for ingress
echo "192.168.1.20 api.glasgow.local" | sudo tee -a /etc/hosts
```

### 🎯 Quick Access URLs
- **FastAPI Root**: `http://api.glasgow.local/`
- **Health Check**: `http://api.glasgow.local/health`
- **Local FastAPI**: `http://localhost:8081/` (with port-forward)