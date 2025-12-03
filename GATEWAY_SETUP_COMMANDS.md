# WireGuard VPN Gateway Setup Commands
# Run these commands on your K3s node (192.168.1.20) via SSH

# 1. Enable IP forwarding (temporary)
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv6.conf.all.forwarding=1

# 2. Make IP forwarding permanent
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
echo "net.ipv6.conf.all.forwarding=1" | sudo tee -a /etc/sysctl.conf

# 3. Detect main network interface
MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
echo "Main interface: $MAIN_INTERFACE"

# 4. Configure NAT/masquerading
sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o $MAIN_INTERFACE -j MASQUERADE
sudo ip6tables -t nat -A POSTROUTING -s fd00:10:8::/64 -o $MAIN_INTERFACE -j MASQUERADE

# 5. Install and save iptables rules
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
sudo netfilter-persistent save

echo "✅ Gateway setup complete!"
