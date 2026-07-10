#!/bin/bash
# Fix routing on all nodes

NODES=("192.168.1.21" "192.168.1.22" "192.168.1.23")
PASSWORD="mlop!"

for node in "${NODES[@]}"; do
    echo "Fixing routes on $node..."
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no bsg@$node 'sudo ip route del default via 192.168.1.1 2>/dev/null; echo "Route fixed"'
done

echo "Done! Restarting K3s on control plane..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no bsg@192.168.1.23 'sudo systemctl restart k3s'

echo "Waiting 30 seconds..."
sleep 30

echo "Testing connectivity..."
kubectl run -it --rm test --image=busybox --restart=Never -- ping -c 2 8.8.8.8
