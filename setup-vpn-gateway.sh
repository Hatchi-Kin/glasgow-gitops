#!/bin/bash
# This script enables IP forwarding and NAT on your K3s node
# Run this ONCE on your K3s node (192.168.1.20) to enable VPN internet access

echo "Configuring K3s node as VPN gateway..."

# 1. Enable IP forwarding (temporary - until reboot)
echo "Enabling IP forwarding..."
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv6.conf.all.forwarding=1

# 2. Make IP forwarding permanent
echo "Making IP forwarding permanent..."
sudo tee -a /etc/sysctl.conf > /dev/null <<EOF
# Enable IP forwarding for WireGuard VPN
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
EOF

# 3. Determine the main network interface
MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
echo "Detected main network interface: $MAIN_INTERFACE"

# 4. Configure NAT/masquerading with iptables
echo "Setting up NAT/masquerading..."
sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o $MAIN_INTERFACE -j MASQUERADE
sudo ip6tables -t nat -A POSTROUTING -s fd00:10:8::/64 -o $MAIN_INTERFACE -j MASQUERADE

# 5. Save iptables rules (Debian/Ubuntu)
echo "Saving iptables rules..."
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save

echo "✅ VPN gateway configuration complete!"
echo ""
echo "Your K3s node is now configured to forward VPN traffic to the internet."
echo "Clients connecting to the VPN will:"
echo "  - Have internet access through your home connection"
echo "  - Appear to be browsing from your home IP"
echo "  - Have access to your local cluster services"
