# Glasgow GitOps - Longhorn Edition

A complete GitOps setup with K3s, ArgoCD, and Longhorn distributed storage for persistent data.

## 🎯 What This Gives You

- **K3s cluster** with 4 nodes (1 control-plane, 3 workers)
- **ArgoCD** for GitOps management 
- **Longhorn** for distributed persistent storage
- **Web UIs** accessible via nip.io (no port forwarding needed)

## 🚀 Quick Start

### 1. Install K3s Cluster

**On control plane node (adama):**
```bash
curl -sfL https://get.k3s.io | sh -
```

**Get the join token:**
```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

**On each worker node (boomer, apollo, starbuck):**
```bash
curl -sfL https://get.k3s.io | K3S_URL=https://192.168.1.20:6443 K3S_TOKEN=<NODE_TOKEN> sh -
```

### 2. Configure kubectl on Local Machine

```bash
# Copy kubeconfig from control plane
ssh bsg@adama "sudo cp /etc/rancher/k3s/k3s.yaml /home/bsg/k3s.yaml && sudo chown bsg:bsg /home/bsg/k3s.yaml"
scp bsg@adama:/home/bsg/k3s.yaml ~/.kube/config
sed -i 's/127.0.0.1/192.168.1.20/' ~/.kube/config

# Make it permanent
echo 'export KUBECONFIG=~/.kube/config' >> ~/.bashrc
source ~/.bashrc
```

### 3. Add Worker Node Labels

```bash
kubectl label node boomer node-role.kubernetes.io/worker=worker
kubectl label node apollo node-role.kubernetes.io/worker=worker  
kubectl label node starbuck node-role.kubernetes.io/worker=worker
```

**Verify cluster:**
```bash
kubectl get nodes
```
Should show:
```
NAME       STATUS   ROLES                  AGE   VERSION
adama      Ready    control-plane,master   20m   v1.32.6+k3s1
apollo     Ready    worker                 10m   v1.32.6+k3s1
boomer     Ready    worker                 10m   v1.32.6+k3s1
starbuck   Ready    worker                 10m   v1.32.6+k3s1
```

### 4. Bootstrap ArgoCD

```bash
# Create namespace and install ArgoCD
kubectl apply -f argocd/argocd-install.yaml
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl get pods -n argocd

# Deploy the root app (this deploys everything else via GitOps)
kubectl apply -f argocd/root-app.yaml
```

### 5. Access Web UIs

After a few minutes, access the UIs directly (no port forwarding needed):

- **ArgoCD**: http://argocd.192.168.1.20.nip.io
- **Longhorn**: http://longhorn.192.168.1.20.nip.io

**ArgoCD Login:**
- Username: `admin`
- Password: Get with `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

## 📋 What Gets Deployed

| Component | Purpose | UI Access |
|-----------|---------|-----------|
| **ArgoCD** | GitOps controller | http://argocd.192.168.1.20.nip.io |
| **Longhorn** | Distributed storage | http://longhorn.192.168.1.20.nip.io |
| **Traefik** | Ingress controller | Built into K3s |

## 🗂️ Repository Structure

```
├── argocd/
│   ├── argocd-install.yaml     # ArgoCD namespace
│   ├── root-app.yaml           # Root application
│   └── apps/
│       ├── longhorn.yaml       # Longhorn application
│       └── ingress.yaml        # Ingress configuration
└── components/
    ├── longhorn/
    │   ├── kustomization.yaml  # Kustomization config
    │   └── longhorn.yaml       # Longhorn manifests (5000+ lines)
    └── ingress/
        ├── kustomization.yaml
        ├── argocd-ingress.yaml # ArgoCD web UI ingress
        ├── longhorn-ingress.yaml # Longhorn web UI ingress
        └── argocd-config.yaml  # ArgoCD config for ingress
```

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
