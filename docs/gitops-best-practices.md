# Glasgow GitOps Best Practices

## Repository Structure
This repository follows a standard GitOps structure using ArgoCD.

- **`apps/`**: ArgoCD Application manifests. These define *what* to deploy.
- **`components/`**: The actual Kubernetes manifests (Deployments, Services, etc.) for each application.
- **`sealed-secrets/`**: Encrypted secrets. **NEVER** commit raw secrets.

## Management Workflow

### 1. Making Changes
- **Edit** the manifests in `components/<app-name>/`.
- **Commit** and **Push** your changes.
- ArgoCD will automatically sync the changes (or you can trigger a sync manually).

### 2. Adding a New App
1.  Create a folder in `components/<new-app>`.
2.  Add your K8s manifests (`deployment.yaml`, `service.yaml`, etc.).
3.  Create an ArgoCD Application manifest in `apps/<new-app>.yaml` pointing to your component folder.

### 3. Secrets Management
We use **Sealed Secrets**.
To create a new secret:
1.  Create a `secret.yaml` locally (do NOT commit).
2.  Run: `kubeseal < secret.yaml > sealed-secret.yaml`
3.  Commit `sealed-secret.yaml`.

## Resource Management
- **Requests & Limits**: Every container MUST have `resources.requests` and `resources.limits` defined.
    - `requests`: Guaranteed resources. Kubernetes uses this for scheduling.
    - `limits`: Maximum resources. Prevents a runaway process from killing the node.

## Node Affinity
- **Adama**: Reserved for heavy inference workloads.
    - Use `nodeSelector: kubernetes.io/hostname: adama` to target this node.

## Troubleshooting
- **App "Processing" or "OutOfSync"**: Check if the manifest in Git matches the live state. Some controllers (like Knative) might modify the live object, causing drift.
