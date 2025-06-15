# Glasgow GitOps Learning Journey 🚀

## What We Built Today

A complete **GitOps-managed microservices stack** with:
- ✅ **PostgreSQL** (with persistent storage)
- ✅ **MinIO** (object storage)  
- ✅ **FastAPI** (from separate repo via Docker Hub)
- ✅ **Ingress** (Traefik-based external access)
- ✅ **ArgoCD** (GitOps deployment automation)
- ✅ **Cluster Management** (automated shutdown/startup scripts)

## 📁 Repository Structure

```
glasgow-gitops/                    # Infrastructure definitions
├── admin-scripts/                # Cluster management tools
│   ├── galactica_on_and_off.py  # Automated cluster control
│   ├── verify-cluster.sh         # Health verification
│   ├── quick_check.py            # Node status checker
│   └── restart.md                # Quick restart guide
├── argocd/
│   ├── install.yaml              # ArgoCD installation
│   └── apps/                     # Application definitions
│       ├── root.yaml             # Root application (deploys others)
│       ├── postgres-prod.yaml    # PostgreSQL app
│       ├── minio.yaml            # MinIO app  
│       ├── fastapi.yaml          # FastAPI app
│       └── ingress.yaml          # Ingress app
├── components/                   # Kubernetes manifests
│   ├── postgres/
│   │   ├── base/                 # Base configuration
│   │   └── overlays/prod/        # Production overrides
│   ├── minio/
│   │   ├── base/
│   │   └── overlays/prod/
│   ├── fastapi/
│   │   ├── base/
│   │   └── overlays/prod/
│   └── ingress/
│       ├── base/
│       └── overlays/prod/

glasgow-fastapi/                   # Application code (separate repo)
├── app/
│   └── main.py                   # FastAPI application
├── Dockerfile                    # Container build instructions
└── requirements.txt              # Python dependencies
```

## 🔧 Key Concepts Learned

### **Persistent Storage**
- **PVCs**: Persistent Volume Claims that survive pod restarts
- **local-path**: K3s default storage class for persistent data
- **Data Persistence**: Verified through full cluster restarts

### **Cluster Operations**
- **Graceful Shutdown**: Drain nodes before shutdown to protect workloads
- **Recovery Process**: Uncordon nodes after restart to enable scheduling
- **Automation**: Python scripts handle complex multi-node operations

### **Kustomize**
- **Purpose**: Template-free Kubernetes configuration management
- **Base**: Common configuration shared across environments
- **Overlays**: Environment-specific modifications (dev, staging, prod)
- **Patches**: Targeted changes to base resources

```yaml
# Example kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base        # Include base resources

patches:
  - path: config-patch.yaml  # Apply environment-specific changes
```

### **ArgoCD Applications**
- **Root App Pattern**: One app that deploys other apps
- **App of Apps**: Manages multiple applications declaratively
- **Sync Policies**: Automated vs manual deployment control

### **GitOps Workflow**
1. **Developer** pushes code to application repo (glasgow-fastapi)
2. **CI/CD** builds Docker image and pushes to registry
3. **Developer** updates infrastructure repo (glasgow-gitops)
4. **ArgoCD** detects changes and deploys to cluster
5. **Cluster** pulls new images and applies configurations

## 💻 Essential CLI Commands

### **Cluster Management**
```bash
# Automated cluster control
python3 admin-scripts/galactica_on_and_off.py off --force    # Shutdown
python3 admin-scripts/galactica_on_and_off.py on             # Startup
python3 admin-scripts/galactica_on_and_off.py status         # Check status


# Manual node management
kubectl drain boomer apollo starbuck --ignore-daemonsets --delete-emptydir-data
kubectl uncordon boomer apollo starbuck
```

### **kubectl (Kubernetes)**
```bash
# Check cluster status
kubectl get nodes
kubectl get pods -A
kubectl get namespaces

# Check persistent storage
kubectl get pvc -A
kubectl get pv

# Application debugging
kubectl get pods -n <namespace>
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>

# Service and ingress
kubectl get svc -n <namespace>
kubectl get ingress -n <namespace>
kubectl get endpoints -n <namespace>

# Force restart deployment
kubectl rollout restart deployment/<name> -n <namespace>

# Port forwarding for testing
kubectl port-forward svc/<service-name> -n <namespace> 8080:8000
```

### **ArgoCD**
```bash
# Setup port-forward in tmux
tmux new-session -d -s argocd-pf 'kubectl port-forward svc/argocd-server -n argocd 8080:443'

# Login to ArgoCD
argocd login localhost:8080 --insecure

# List applications
argocd app list

# Sync applications
argocd app sync <app-name>
argocd app sync glasgow-gitops  # Sync root app
argocd app sync --all           # Sync all apps

# Get application status
argocd app get <app-name>
```

### **Kustomize**
```bash
# Preview what will be deployed
kubectl kustomize components/<service>/overlays/prod

# Apply directly (for testing)
kubectl apply -k components/<service>/overlays/prod
```

### **Docker**
```bash
# Build and push images
docker build -t <username>/<image>:latest .
docker push <username>/<image>:latest

# Tag for different registries
docker tag <image> <registry>/<image>:tag
```

## 🔍 Debugging Commands

### **Check Application Health**
```bash
# ArgoCD applications status
kubectl get applications -n argocd

# Pod status across all namespaces
kubectl get pods -A | grep -E "(postgres|minio|fastapi)"

# Service endpoints
kubectl get endpoints -A

# Check persistent storage
kubectl get pvc -A
kubectl describe pvc <pvc-name> -n <namespace>
```

### **Troubleshooting Common Issues**
```bash
# Pods stuck in Pending after restart
kubectl uncordon boomer apollo starbuck

# Image pull issues
kubectl describe pod <pod-name> -n <namespace>

# Service connectivity
kubectl get svc -n <namespace>
kubectl get endpoints -n <namespace>

# Ingress issues
kubectl get ingress -A
kubectl describe ingress <ingress-name> -n <namespace>

# ArgoCD sync issues
argocd app sync --all
```

## 🚀 Production Readiness Achievements

### **Data Persistence** ✅
- PostgreSQL and MinIO data survives cluster restarts
- PVCs remain bound with same volume IDs
- Zero data loss during maintenance operations

### **Cluster Resilience** ✅
- Full cluster shutdown/startup automation
- Graceful node draining and recovery
- ~10 minute recovery time from power-off to fully operational

### **GitOps Automation** ✅
- Declarative infrastructure management
- Automatic application sync via ArgoCD
- No configuration drift after restarts

### **Enterprise Operations** ✅
- Automated health verification
- Comprehensive documentation
- Reproducible deployment procedures

## 📚 Useful Resources

- **ArgoCD Docs**: https://argo-cd.readthedocs.io/
- **Kustomize Docs**: https://kustomize.io/
- **k3s Docs**: https://k3s.io/
- **Kubernetes Docs**: https://kubernetes.io/docs/
- **GitOps Guide**: https://www.gitops.tech/