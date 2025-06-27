# K3s Homelab Cluster Setup

This is my personal cheat sheet for bootstrapping the K3s cluster from scratch.

## 
 Prerequisites

- All nodes have a user `bsg` with passwordless `sudo` access.
- SSH access is configured for all nodes.
- A static IP is assigned to the control plane node (`adama`).

## 
 Node Layout

| Hostname   | Role           | IP              | Notes                               |
|------------|----------------|-----------------|-------------------------------------|
| adama      | control plane  | 192.168.1.20    | Runs the Kubernetes API server.     |
| boomer     | worker         | 192.168.1.21    | Runs application pods.              |
| apollo     | worker         | 192.168.1.22    | Runs application pods.              |
| starbuck   | worker         | 192.168.1.23    | Runs application pods.              |

## 
 Installation Workflow

### 1. Install K3s on the Control Plane (`adama`)

This command downloads and runs the K3s installer. It sets up this node as the master.

```sh
ssh bsg@adama "curl -sfL https://get.k3s.io | sh -"
```

### 2. Get the Cluster Join Token

The token is like a password that allows other nodes to join the cluster.

```sh
# Run this on adama
ssh bsg@adama "sudo cat /var/lib/rancher/k3s/server/node-token"
```

### 3. Join Worker Nodes

This command installs the K3s agent on the worker nodes and connects them to the control plane.

```sh
# Replace <WORKER_HOSTNAME> with boomer, apollo, starbuck
# Replace <NODE_TOKEN> with the token from step 2
ssh bsg@<WORKER_HOSTNAME> \
  "curl -sfL https://get.k3s.io | K3S_URL=https://192.168.1.20:6443 K3S_TOKEN=<NODE_TOKEN> sh -"
```

### 4. Get `kubeconfig` for Remote Access

This is the most important step for managing the cluster from my local machine.

1.  **Copy the config file** on `adama`.
2.  **Replace the server URL** from `127.0.0.1` to the actual IP of `adama`.
3.  **Securely copy it** to my local machine.

```sh
# Run this from your local machine
ssh bsg@adama "sudo cp /etc/rancher/k3s/k3s.yaml /home/bsg/k3s.yaml && sudo chown bsg:bsg /home/bsg/k3s.yaml"
scp bsg@adama:/home/bsg/k3s.yaml ~/.kube/config
sed -i 's/127.0.0.1/192.168.1.20/' ~/.kube/config
```

### 5. Verify Cluster Status

Now, from my local machine, I can run `kubectl` commands.

```sh
# Check that all nodes are Ready
kubectl get nodes -o wide

# Check that all system pods are running
kubectl get pods -A
```

---

```