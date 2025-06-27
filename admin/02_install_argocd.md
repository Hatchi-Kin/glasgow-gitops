# ArgoCD Installation & Workflow

This is my cheat sheet for installing ArgoCD and connecting it to this Git repository.

## 🤔 Why ArgoCD?

ArgoCD is the heart of my GitOps workflow. It automatically syncs the state of the cluster with the YAML files in this repository. I make changes in Git, and ArgoCD makes them happen in Kubernetes.

## 🚀 Installation

1.  **Create the namespace:** ArgoCD needs its own namespace to live in.
    ```sh
    kubectl create namespace argocd
    ```
2.  **Apply the official manifest:** This installs all the necessary ArgoCD components.
    ```sh
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    ```
3.  **Verify the installation:** Check that all the pods are running.
    ```sh
    kubectl get pods -n argocd
    ```

## 🔗 Connecting to This Repository

Once ArgoCD is running, I need to tell it to manage my cluster. I do this by applying the `root-app.yaml` from this repository.

```sh
# This command tells ArgoCD to start managing the applications defined in my repo.
kubectl apply -f ../argocd/root-app.yaml
```

## 🔑 Accessing the UI

1.  **Get the initial password:**
    ```sh
    # This decodes the secret that contains the initial admin password.
    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
    ```
2.  **Port-forward the UI:**
    ```sh
    # This makes the ArgoCD UI available on my local machine.
    kubectl port-forward svc/argocd-server -n argocd 8080:443
    ```
    - **URL:** [http://localhost:8080](http://localhost:8080)
    - **Username:** `admin`

### My `tmux` Workflow

I like to run the port-forward in a `tmux` session so it stays running in the background.

```sh
# Start a new detached tmux session named 'argocd-pf'
tmux new-session -d -s argocd-pf 'kubectl port-forward svc/argocd-server -n argocd 8080:443'

# Attach to the session to see the output
tmux attach-session -t argocd-pf

# Detach from the session: Ctrl+B, then D

# Kill the session when I'm done
tmux kill-session -t argocd-pf
```

## 🗑️ Cleanup

If I need to start over, I can uninstall ArgoCD completely.

```sh
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl delete namespace argocd
```

---