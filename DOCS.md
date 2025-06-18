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

# Logs

## 1. Check FastAPI pod logs:

```bash
kubectl logs -n fastapi-prod deployment/fastapi
```

Or if you want to follow logs in real-time:
```bash
kubectl logs -n fastapi-prod deployment/fastapi -f
```

## 2. Get specific pod name and check logs:

```bash
kubectl get pods -n fastapi-prod
kubectl logs -n fastapi-prod <pod-name>
```

## 3. Check previous logs if pod restarted:

```bash
kubectl logs -n fastapi-prod deployment/fastapi --previous
```

## 4. Check pod status and events:

```bash
kubectl describe pod -n fastapi-prod -l app=fastapi
```




### 🎯 Quick Access URLs
- **FastAPI Root**: `http://api.glasgow.local/`
- **Health Check**: `http://api.glasgow.local/health`
- **Local FastAPI**: `http://localhost:8081/` (with port-forward)


# K3s Homelab Cluster

> A learning project for Kubernetes using K3s on bare metal

## Cluster Architecture

| Hostname   | Role           | CPU/RAM         | IP              |
|------------|----------------|-----------------|-----------------|
| adama      | control plane  | i5-7200U, 8GB   | 192.168.1.20    |
| boomer     | worker         | N150, 16GB      | 192.168.1.21    |
| apollo     | worker         | N150, 16GB      | 192.168.1.22    |
| starbuck   | worker         | N150, 16GB      | 192.168.1.23    |


## Quick Reference

### Cluster Lifecycle

```sh
# Check status
python3 galactica_on_and_off.py status

# Shutdown cluster
python3 galactica_on_and_off.py off -f

# Prepare cluster after power on
python3 galactica_on_and_off.py on
```

### Common Commands

```sh
# Check cluster health
kubectl get nodes
kubectl get pods -A
```
### Network Configuration

```sh
# Check connectivity between nodes
ping 192.168.1.20  # adama
ping 192.168.1.21  # boomer
ping 192.168.1.22  # apollo
ping 192.168.1.23  # starbuck
```

## Control Plane Setup

### Install K3s Server on adama

```sh
# Installation
curl -sfL https://get.k3s.io | sh -

# Verify installation
sudo systemctl status k3s
k3s --version
kubectl get nodes

# Get join token for workers (you'll need this)
sudo cat /var/lib/rancher/k3s/server/node-token
```

### Configure kubectl for Regular User

```sh
# Set up kubectl access without requiring sudo
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config
echo 'export KUBECONFIG=~/.kube/config' >> ~/.bashrc
source ~/.bashrc

## Worker Node Setup

Run on each worker node (boomer, apollo, starbuck):

```sh
# Replace TOKEN with the actual token from the master node
curl -sfL https://get.k3s.io | K3S_URL=https://192.168.1.20:6443 K3S_TOKEN=TOKEN sh -
```

### Add Labels to Worker Nodes

```sh
# Add worker role labels
kubectl label node boomer node-role.kubernetes.io/worker=worker
kubectl label node apollo node-role.kubernetes.io/worker=worker
kubectl label node starbuck node-role.kubernetes.io/worker=worker
```

### Configure Remote Kubeconfig

```sh
# ON MASTER NODE: Create a remote-accessible config
sudo cp /etc/rancher/k3s/k3s.yaml ~/k3s-remote.yaml
sudo chown $USER:$USER ~/k3s-remote.yaml
chmod 600 ~/k3s-remote.yaml
sed -i 's/127.0.0.1/192.168.1.20/' ~/k3s-remote.yaml

# ON LOCAL MACHINE: Copy the config file
scp bsg@192.168.1.20:~/k3s-remote.yaml ~/k3s.yaml
export KUBECONFIG=~/k3s.yaml

# Add to shell profile
echo 'export KUBECONFIG=~/k3s.yaml' >> ~/.bashrc

# Test connection
kubectl get nodes
```