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


## 2. **Access ArgoCD UI**
Open your browser and navigate to `https://localhost:8080`.
login to ArgoCD UI:
username: `admin`
password: `<output-from-above-command>`

## 3. **Create root application and start CI/CD GitOps**
create a new argocd/root-app.yaml:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: glasgow-gitops
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'https://github.com/Hatchi-Kin/glasgow-gitops.git'
    targetRevision: main
    path: argocd/apps
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

and push to main branch.
then run
```sh
kubectl apply -f argocd/root-app.yaml -n argocd
```