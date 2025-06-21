## 1. **Install ArgoCD**

**Namespace:**  
```sh
kubectl create namespace argocd
```

**Install ArgoCD (Official, Stable):**  
```sh
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**Verify Installation:**  
```sh
kubectl get ns
kubectl get pods -n argocd
```

**Expose ArgoCD UI (port-forward for now):**  
```sh
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**get the initial admin password**
```sh
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```
login to ArgoCD UI:
username: `admin`
password: `<output-from-above-command>`
---
