# Quick Start - New Apartment Setup

## 🚀 TL;DR - Get Your Cluster Running Fast

### 1. Physical Setup (5 minutes)
```bash
# Connect everything:
# - Freebox to fiber
# - All Pis to network switch
# - Switch to Freebox
# - Power on: adama first, wait 3 min, then others
```

### 2. Find Your New Network (2 minutes)
```bash
# On your laptop, check your IP
ip addr show | grep inet

# Access Freebox admin
# URL: http://mafreebox.freebox.fr
# or: http://192.168.0.254 (or .1.254)

# Note your network range (probably 192.168.0.x or 192.168.1.x)
```

### 3. Set Static IPs in Freebox (5 minutes)
Go to: **Paramètres** → **DHCP** → **Baux statiques**

Add these (adjust to your network range):
- adama: `192.168.0.20`
- boomer: `192.168.0.21`
- apollo: `192.168.0.22`
- starbuck: `192.168.0.23`

Reboot all Pis after setting this up.

### 4. Update All IP References (2 minutes)
```bash
cd ~/Documents/glasgow-gitops

# Run the automated update script
python3 admin/update_network_ips.py

# Enter old IP: 192.168.1.20
# Enter new IP: 192.168.0.20 (or whatever you chose)
# Follow prompts
```

### 5. Verify Cluster (3 minutes)
```bash
# Test kubectl
kubectl get nodes
# Should show all 4 nodes

# If nodes show SchedulingDisabled:
python3 admin/cluster_manager.py uncordon

# Full health check
python3 admin/quick_check.py
```

### 6. Commit & Sync (2 minutes)
```bash
# Commit the IP changes
git add .
git commit -m "Update network config for new apartment"
git push origin main

# Force sync ArgoCD
python3 admin/cluster_manager.py sync

# Check everything is running
kubectl get pods -n glasgow-prod
```

### 7. Setup External Access (10 minutes)

**Get your public IP:**
```bash
curl ifconfig.me
```

**Configure Freebox port forwarding:**
- Go to: **Paramètres** → **Gestion des ports**
- Add:
  - Port 80 → 192.168.0.20:80 (HTTP)
  - Port 443 → 192.168.0.20:443 (HTTPS)
  - Port 51820 → 192.168.0.20:51820 (WireGuard VPN)

**Update OVH DNS (if you have a domain):**
1. Login to https://www.ovh.com/manager/
2. Go to your domain → DNS Zone
3. Update A records to your new public IP
4. Wait 5-30 minutes for propagation

### 8. Test Everything (2 minutes)
```bash
# Local access
curl http://argocd.192.168.0.20.nip.io
curl http://minio.192.168.0.20.nip.io

# External access (from phone on 4G)
curl http://<your-public-ip>
```

---

## ✅ Done!

Your services should now be accessible at:
- **Local**: `http://<service>.192.168.0.20.nip.io`
- **External**: `http://yourdomain.com` (if configured)

---

## 🔧 Common Issues

**Nodes not Ready?**
```bash
# Check K3s on control plane
ssh bsg@192.168.0.20
sudo systemctl status k3s

# Restart if needed
sudo systemctl restart k3s
```

**Pods stuck Pending?**
```bash
# Check Longhorn storage
kubectl get pods -n longhorn-system

# Wait 5 minutes for Longhorn to stabilize
```

**Can't access services?**
```bash
# Check Traefik ingress
kubectl get pods -n kube-system | grep traefik

# Check ingress resources
kubectl get ingress -n glasgow-prod
```

---

## 📚 Full Documentation

For detailed step-by-step instructions, see:
- `docs/NEW_APARTMENT_SETUP.md` - Complete setup guide
- `admin/update_network_ips.py` - Automated IP update tool
- `README.md` - General cluster documentation

---

**Total Time: ~30 minutes** ⏱️
