# Glasgow GitOps Learning Journey 🚀

## What We Built Today

A complete **GitOps-managed microservices stack** with:
- ✅ **PostgreSQL** (with persistent storage)
- ✅ **MinIO** (object storage)  
- ✅ **FastAPI** (from separate repo via Docker Hub)
- ✅ **Ingress** (Traefik-based external access)
- ✅ **ArgoCD** (GitOps deployment automation)

## 📁 Repository Structure

```
glasgow-gitops/                    # Infrastructure definitions
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

### **kubectl (Kubernetes)**
```bash
# Check cluster status
kubectl get nodes
kubectl get pods -A
kubectl get namespaces

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
# Login to ArgoCD
argocd login <argocd-server>

# List applications
argocd app list

# Sync applications
argocd app sync <app-name>
argocd app sync glasgow-gitops  # Sync root app

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
```

### **Troubleshooting Common Issues**
```bash
# Image pull issues
kubectl describe pod <pod-name> -n <namespace>

# Service connectivity
kubectl get svc -n <namespace>
kubectl get endpoints -n <namespace>

# Ingress issues
kubectl get ingress -A
kubectl describe ingress <ingress-name> -n <namespace>
```



## 📚 Useful Resources

- **ArgoCD Docs**: https://argo-cd.readthedocs.io/
- **Kustomize Docs**: https://kustomize.io/
- **k3s Docs**: https://k3s.io/
- **Kubernetes Docs**: https://kubernetes.io/docs/
