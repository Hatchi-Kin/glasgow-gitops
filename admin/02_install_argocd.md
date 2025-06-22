# ArgoCD Install & Usage

ArgoCD manages all cluster resources via GitOps.

## 🚀 Install

```sh
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl get pods -n argocd
```

## 🔑 Access UI

```sh
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
- Open [http://localhost:8080](http://localhost:8080)
- Username: `admin`
- Password:
  ```sh
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
  ```

## 🖥️ Port-Forwarding (tmux)

```sh
tmux new-session -d -s argocd-pf 'kubectl port-forward svc/argocd-server -n argocd 8080:443'
tmux attach-session -t argocd-pf
# Detach: Ctrl+B, then D
# Kill: tmux kill-session -t argocd-pf
```

## 📦 Common Commands

```sh
argocd app list
argocd app sync glasgow-gitops
argocd app get glasgow-gitops
```

## 🌐 Concepts

- **GitOps:** Cluster state is defined in Git.
- **Applications:** Each major component is an ArgoCD app.
- **Sync:** ArgoCD applies Git changes to the cluster.
- **Health:** ArgoCD monitors app health and sync status.

---
