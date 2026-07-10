# Freebox Network Configuration for K3s Pod Network

## Problem
Pods in your K3s cluster can't reach the internet because the Freebox is blocking or not routing traffic from the pod network (`10.42.0.0/16`).

## Solution: Configure Freebox to Allow Pod Network

### Step 1: Access Freebox Admin Panel

1. Open browser: `http://mafreebox.freebox.fr` or `http://192.168.1.254`
2. Login with your Freebox credentials

### Step 2: Check Firewall Settings

**Option A: Disable Firewall (Quick Test)**

1. Go to: **Paramètres de la Freebox** → **Mode avancé** → **Pare-feu**
2. Temporarily **disable the firewall** to test if that's the issue
3. Click **Appliquer**
4. Test from your laptop:
   ```bash
   kubectl run test --image=busybox --restart=Never -- ping -c 2 8.8.8.8
   sleep 10
   kubectl logs test
   kubectl delete pod test
   ```
5. If it works, re-enable firewall and proceed to Option B

**Option B: Add Firewall Rule for Pod Network**

1. Go to: **Paramètres de la Freebox** → **Mode avancé** → **Pare-feu**
2. Click **Ajouter une règle**
3. Add rule:
   - **Source IP**: `192.168.1.20` (adama - your K3s control plane)
   - **Destination**: `Toutes` (All)
   - **Protocol**: `Tous` (All)
   - **Action**: `Accepter` (Accept)
   - **Description**: "K3s pod network traffic"
4. Repeat for other nodes: `192.168.1.21`, `192.168.1.22`, `192.168.1.23`
5. Click **Appliquer**

### Step 3: Check NAT/Routing Settings

**Enable IPv4 Forwarding (if option exists)**

1. Go to: **Paramètres de la Freebox** → **Mode avancé** → **Routeur**
2. Look for **IPv4 forwarding** or **Routage** option
3. Ensure it's **enabled**

**Check if there's a "DMZ" or "Exposed Host" setting**

1. Go to: **Paramètres de la Freebox** → **Gestion des ports**
2. Check if there's a DMZ option
3. Do NOT enable DMZ (security risk), but check if it's accidentally enabled

### Step 4: Check DHCP Settings

1. Go to: **Paramètres de la Freebox** → **DHCP**
2. Verify your static IP reservations are correct:
   - `adama`: `192.168.1.20`
   - `boomer`: `192.168.1.21`
   - `apollo`: `192.168.1.22`
   - `starbuck`: `192.168.1.23`

### Step 5: Alternative - Use Bridge Mode (Advanced)

If the above doesn't work, you might need to configure the Freebox in bridge mode, but this is more complex and not recommended unless necessary.

---

## Quick Test Commands

After making changes in Freebox, test from your laptop:

```bash
# Test 1: Ping from pod
kubectl run test --image=busybox --restart=Never -- ping -c 3 8.8.8.8
sleep 15
kubectl logs test
kubectl delete pod test

# Test 2: HTTP request
kubectl run test --image=busybox --restart=Never -- wget -T 5 -O- http://example.com
sleep 15
kubectl logs test
kubectl delete pod test

# Test 3: DNS + HTTP
kubectl run test --image=nicolaka/netshoot --restart=Never -- curl -v http://github.com
sleep 20
kubectl logs test
kubectl delete pod test
```

---

## Alternative Solution: Manual NAT on Nodes

If Freebox configuration doesn't work, you can configure NAT directly on your K3s nodes:

```bash
# Run this on adama (control plane)
sshpass -p 'mlop!' ssh bsg@192.168.1.20 << 'EOF'
# Add masquerade rule
sudo iptables -t nat -A POSTROUTING -s 10.42.0.0/16 ! -d 10.42.0.0/16 -o enp4s0f1 -j MASQUERADE

# Make it persistent
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save

# Verify
sudo iptables -t nat -L POSTROUTING -n -v | grep 10.42
EOF
```

Then test again.

---

## Common Freebox Settings Locations

Different Freebox models have slightly different UIs. Look for these sections:

- **Firewall**: `Paramètres` → `Mode avancé` → `Pare-feu`
- **Port Forwarding**: `Paramètres` → `Gestion des ports`
- **DHCP**: `Paramètres` → `DHCP`
- **Routing**: `Paramètres` → `Mode avancé` → `Routeur`
- **IPv6**: `Paramètres` → `Mode avancé` → `IPv6`

---

## What to Look For

The key issue is that the Freebox needs to:
1. **Allow traffic FROM your K3s nodes** (192.168.1.20-23)
2. **Not block outgoing connections** from those IPs
3. **Allow NAT/masquerading** so pod traffic appears to come from the node IPs

Most likely, the Freebox firewall is blocking traffic because it sees packets with source IPs from `10.42.0.0/16` (pod network) which it doesn't recognize.

The masquerade rules on your nodes should rewrite those source IPs to `192.168.1.20` (node IP), but something might be preventing that.

---

## Still Not Working?

If none of the above works, the issue might be:

1. **Freebox firmware bug** - Check for Freebox firmware updates
2. **IPv6 interference** - Try disabling IPv6 temporarily
3. **MTU issues** - Pod network MTU might be too large

Let me know what you find in the Freebox UI and we can troubleshoot further!
