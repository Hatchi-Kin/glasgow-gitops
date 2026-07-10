# Glasgow Homelab - New Apartment Setup Guide (Free Fiber)

## 🏠 Overview
This guide covers setting up your K3s homelab cluster in your new apartment with Free (France ISP) fiber internet and full stack IP.

## 📋 Prerequisites Checklist
- [ ] Free Freebox router installed and online
- [ ] All 4 Raspberry Pi nodes (adama, apollo, boomer, starbuck)
- [ ] Network switch (if using one)
- [ ] Ethernet cables
- [ ] Power supplies for all nodes

---

## Phase 1: Physical Setup & Network Discovery

### Step 1: Connect Hardware

1. **Connect Freebox to fiber**
   - Ensure Freebox is powered on and connected to fiber ONT
   - Wait for all lights to be stable (usually 5-10 minutes)

2. **Connect your laptop to Freebox**
   - Connect via WiFi or Ethernet to access Freebox admin panel

3. **Find your new network range**
   ```bash
   # On your laptop, check your IP
   ip addr show
   # or
   ifconfig
   ```
   
   Free typically uses `192.168.0.x` or `192.168.1.x` range.
   Note your:
   - **Gateway IP** (usually `192.168.0.254` or `192.168.1.254`)
   - **Your laptop IP**
   - **Network range** (e.g., `192.168.0.0/24`)

### Step 2: Configure Static IPs on Freebox

Access Freebox admin panel:
- URL: `http://mafreebox.freebox.fr` or `http://192.168.0.254`
- Default login: Check sticker on your Freebox

**Reserve static IPs for your nodes:**

Go to: **Paramètres de la Freebox** → **DHCP** → **Baux statiques**

Add 4 static leases (adjust IPs based on your network):
- `adama`: `192.168.0.20` (or `.1.20` if using that range)
- `boomer`: `192.168.0.21`
- `apollo`: `192.168.0.22`
- `starbuck`: `192.168.0.23`

You'll need the MAC addresses of each Pi. You can:
1. Boot them one at a time and check DHCP leases
2. Or check the sticker on each Pi
3. Or SSH into them with old IPs first (if they boot)

### Step 3: Connect and Power On Nodes

1. **Connect all nodes to network switch**
2. **Connect switch to Freebox**
3. **Power on nodes in order:**
   - Power on `adama` (control plane) first
   - Wait 3 minutes
   - Power on `boomer`, `apollo`, `starbuck`
   - Wait 5 minutes for all to boot

### Step 4: Verify Node Connectivity

```bash
# From your laptop, ping each node
ping 192.168.0.20  # adama
ping 192.168.0.21  # boomer
ping 192.168.0.22  # apollo
ping 192.168.0.23  # starbuck
```

If pings fail, check:
- Freebox DHCP leases to see what IPs were assigned
- Network cables
- Node power

---

## Phase 2: Update Node Configuration

### Step 5: SSH into Each Node and Update Network Config

**For each node, you'll need to:**

1. **SSH into the node** (use whatever IP it got from DHCP first)
   ```bash
   # Find current IPs from Freebox admin panel, then:
   ssh bsg@<current-ip>
   # Password: mlop!
   ```

2. **Update hostname resolution** (if needed)
   ```bash
   # Check current hostname
   hostname
   
   # If it's not correct, update /etc/hostname
   sudo nano /etc/hostname
   # Should be: adama, boomer, apollo, or starbuck
   
   # Update /etc/hosts
   sudo nano /etc/hosts
   # Add/update:
   192.168.0.20  adama
   192.168.0.21  boomer
   192.168.0.22  apollo
   192.168.0.23  starbuck
   ```

3. **Check K3s status**
   ```bash
   # On adama (control plane)
   sudo systemctl status k3s
   
   # On workers (boomer, apollo, starbuck)
   sudo systemctl status k3s-agent
   ```

4. **If K3s is not running, start it**
   ```bash
   # On adama
   sudo systemctl start k3s
   
   # On workers
   sudo systemctl start k3s-agent
   ```

### Step 6: Update kubectl Config on Your Laptop

```bash
# SSH into adama
ssh bsg@192.168.0.20

# Copy K3s config
sudo cat /etc/rancher/k3s/k3s.yaml

# On your laptop, update ~/.kube/config
# Replace the server IP with new adama IP (192.168.0.20)
nano ~/.kube/config

# Change:
# server: https://192.168.1.20:6443
# to:
# server: https://192.168.0.20:6443
```

Or copy the entire config:
```bash
# On your laptop
scp bsg@192.168.0.20:/etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i 's/127.0.0.1/192.168.0.20/g' ~/.kube/config
```

### Step 7: Verify Cluster is Running

```bash
cd ~/Documents/glasgow-gitops

# Check nodes
kubectl get nodes

# Should show all 4 nodes as Ready
# If SchedulingDisabled, uncordon them:
python3 admin/cluster_manager.py uncordon

# Check cluster health
python3 admin/quick_check.py
```

---

## Phase 3: Update Ingress Configurations

Your services currently use `192.168.1.20.nip.io` which needs to be updated to `192.168.0.20.nip.io` (or whatever your new IP is).

### Step 8: Update All Ingress Resources

```bash
cd ~/Documents/glasgow-gitops

# Find all files with old IP
grep -r "192.168.1.20" components/

# Update them all at once
find components/ -type f -name "*.yaml" -exec sed -i 's/192.168.1.20/192.168.0.20/g' {} +

# Also check sealed-secrets and argocd folders
find sealed-secrets/ -type f -name "*.yaml" -exec sed -i 's/192.168.1.20/192.168.0.20/g' {} +
find argocd/ -type f -name "*.yaml" -exec sed -i 's/192.168.1.20/192.168.0.20/g' {} +

# Verify changes
git diff
```

### Step 9: Commit and Push Changes

```bash
git add .
git commit -m "Update network config for new apartment (192.168.0.x)"
git push origin main
```

### Step 10: Force Sync ArgoCD

```bash
# Wait for ArgoCD to detect changes, or force sync
python3 admin/cluster_manager.py sync

# Check application status
kubectl get applications -n argocd

# Check pods
kubectl get pods -n glasgow-prod
```

---

## Phase 4: External Access Setup

### Step 11: Get Your New Public IP

```bash
# From your laptop (connected to Freebox)
curl ifconfig.me
# or
curl icanhazip.com
```

Note this IP - this is your new public IP from Free.

### Step 12: Configure Freebox Port Forwarding

Access Freebox admin panel:
- Go to: **Paramètres de la Freebox** → **Gestion des ports**

Add port forwarding rules:

| External Port | Internal IP | Internal Port | Protocol | Description |
|--------------|-------------|---------------|----------|-------------|
| 80 | 192.168.0.20 | 80 | TCP | HTTP to K3s |
| 443 | 192.168.0.20 | 443 | TCP | HTTPS to K3s |
| 51820 | 192.168.0.20 | 51820 | UDP | WireGuard VPN |

**Important for Free "Full Stack IP":**
- Free gives you a public IPv4 AND IPv6
- Make sure port forwarding is enabled for both IPv4 and IPv6
- Check "Activer le mode bridge" is OFF (you want NAT mode)

### Step 13: Update OVH DNS Records

You mentioned needing to update OVH to redirect to your new IP. 

**If you have a domain at OVH:**

1. **Login to OVH Manager**: https://www.ovh.com/manager/
2. **Go to your domain** → **DNS Zone**
3. **Update A records** to point to your new public IP:

   ```
   @ (root)           A    <your-new-public-ip>
   * (wildcard)       A    <your-new-public-ip>
   argocd             A    <your-new-public-ip>
   minio              A    <your-new-public-ip>
   n8n                A    <your-new-public-ip>
   fastapi            A    <your-new-public-ip>
   msv2-webapp        A    <your-new-public-ip>
   ```

4. **Wait for DNS propagation** (5-60 minutes)

5. **Test DNS resolution:**
   ```bash
   dig yourdomain.com
   dig argocd.yourdomain.com
   ```

**If you DON'T have a domain yet:**
- You can use `nip.io` for now: `http://argocd.192.168.0.20.nip.io`
- Or register a domain at OVH and follow the steps above

### Step 14: Update Ingress for Real Domain (Optional)

If you have a domain, update your ingress resources:

```bash
cd ~/Documents/glasgow-gitops

# Replace nip.io with your real domain
find components/ -type f -name "*ingress*.yaml" -exec sed -i 's/192.168.0.20.nip.io/yourdomain.com/g' {} +

# Commit changes
git add .
git commit -m "Update ingress to use real domain"
git push origin main

# Sync ArgoCD
python3 admin/cluster_manager.py sync
```

---

## Phase 5: VPN Gateway Setup (Optional)

If you want to access your homelab remotely via WireGuard VPN:

### Step 15: Re-configure VPN Gateway

```bash
# SSH into adama
ssh bsg@192.168.0.20

# Run the gateway setup script
cd /path/to/glasgow-gitops
bash setup-vpn-gateway.sh
```

This will:
- Enable IP forwarding
- Configure NAT for VPN clients
- Allow VPN clients to access internet through your Free connection

### Step 16: Update WireGuard Client Configs

Your WireGuard clients need to be updated with:
- New public IP (endpoint)
- New internal network range (if changed)

Example client config update:
```ini
[Interface]
PrivateKey = <your-private-key>
Address = 10.8.0.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = <server-public-key>
Endpoint = <your-new-public-ip>:51820  # <-- Update this
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

---

## Phase 6: Verification & Testing

### Step 17: Full System Check

```bash
cd ~/Documents/glasgow-gitops

# Run comprehensive health check
python3 admin/quick_check.py

# Check all services are accessible
curl http://argocd.192.168.0.20.nip.io
curl http://minio.192.168.0.20.nip.io
curl http://fastapi.192.168.0.20.nip.io
```

### Step 18: Test External Access

From your phone (disconnect from WiFi, use 4G/5G):
```
http://<your-public-ip>  # Should reach Traefik
http://yourdomain.com    # If you set up domain
```

### Step 19: Test VPN (if configured)

1. Connect to WireGuard VPN from external network
2. Try accessing internal services:
   ```
   http://192.168.0.20
   http://argocd.192.168.0.20.nip.io
   ```

---

## 🔧 Troubleshooting

### Nodes Not Joining Cluster

```bash
# On adama, check K3s logs
sudo journalctl -u k3s -f

# On workers, check K3s agent logs
sudo journalctl -u k3s-agent -f

# Check if workers can reach control plane
ping 192.168.0.20
telnet 192.168.0.20 6443
```

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n glasgow-prod

# Describe problematic pod
kubectl describe pod <pod-name> -n glasgow-prod

# Check Longhorn storage
kubectl get pods -n longhorn-system
```

### External Access Not Working

1. **Check Freebox port forwarding** is active
2. **Check public IP** hasn't changed: `curl ifconfig.me`
3. **Check Traefik** is running: `kubectl get pods -n kube-system | grep traefik`
4. **Check ingress** resources: `kubectl get ingress -n glasgow-prod`

### DNS Not Resolving

```bash
# Check DNS propagation
dig yourdomain.com
nslookup yourdomain.com

# Check OVH DNS zone is correct
# Login to OVH Manager and verify A records
```

---

## 📝 Quick Reference

### New Network Info
- **Network Range**: `192.168.0.0/24` (adjust if different)
- **Gateway**: `192.168.0.254` (Freebox)
- **Control Plane**: `adama` @ `192.168.0.20`
- **Workers**: 
  - `boomer` @ `192.168.0.21`
  - `apollo` @ `192.168.0.22`
  - `starbuck` @ `192.168.0.23`

### Service URLs (Local)
- ArgoCD: `http://argocd.192.168.0.20.nip.io`
- MinIO: `http://minio.192.168.0.20.nip.io`
- FastAPI: `http://fastapi.192.168.0.20.nip.io`
- n8n: `http://n8n.192.168.0.20.nip.io`
- MSV2 Webapp: `http://msv2-webapp.192.168.0.20.nip.io`

### Useful Commands
```bash
# Cluster status
python3 admin/quick_check.py

# Restart all apps
python3 admin/cluster_manager.py restart

# Sync ArgoCD
python3 admin/cluster_manager.py sync

# Check public IP
curl ifconfig.me

# Update all ingress IPs
find components/ -type f -name "*.yaml" -exec sed -i 's/OLD_IP/NEW_IP/g' {} +
```

---

## ✅ Success Checklist

- [ ] All 4 nodes powered on and reachable
- [ ] K3s cluster shows all nodes Ready
- [ ] All pods in glasgow-prod are Running
- [ ] Local services accessible via nip.io URLs
- [ ] Freebox port forwarding configured
- [ ] OVH DNS updated with new public IP
- [ ] External access working (if configured)
- [ ] VPN working (if configured)

---

**Félicitations! Your homelab is now running in your new apartment! 🎉**
