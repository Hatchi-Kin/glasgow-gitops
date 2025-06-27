# ArgoCD Cheat Sheet

## 🔑 Access UI

```sh
# Forward the ArgoCD server port to your local machine
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
- **URL:** [http://localhost:8080](http://localhost:8080)
- **Username:** `admin`
- **Password:**
  ```sh
  # Decode the initial admin secret
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
  ```

## 📦 Common Commands

```sh
# List all managed applications
argocd app list

# Force a sync for the entire stack
argocd app sync root-app

# Get the status and details of the root app
argocd app get root-app
```

## 🧠 Core Design Decisions

- **Why use the "App of Apps" pattern?**
  - My `root-app.yaml` defines the entire stack. To add or remove a new service (like cert-manager later), I only need to add or remove it from `apps/`. ArgoCD handles the rest. It keeps the main deployment simple and modular.

- **Where are the applications defined?**
  - The `root-app.yaml` points to the `apps/` directory. Each file in there, like `glasgow-prod-stack.yaml`, is an "App" that ArgoCD manages.

- **How do I see the sync status?**
  - Use `argocd app list` or the UI. "Synced" means the cluster matches Git. "OutOfSync" means there are differences, and a sync is needed.

---
