import subprocess
import argparse
from typing import List
import time

# Reuse your existing configuration
USERNAME = "bsg"
PASSWORD = "mlop!"
HOSTS = [
    ("adama", "192.168.1.20", "master"),
    ("boomer", "192.168.1.21", "worker"),
    ("apollo", "192.168.1.22", "worker"),
    ("starbuck", "192.168.1.23", "worker"),
]


def run_ssh_command(ip: str, command: str) -> bool:
    """Run command over SSH and return success status"""
    try:
        subprocess.check_output(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                f"{USERNAME}@{ip}",
                command,
            ],
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def cleanup_node(hostname: str, ip: str, is_master: bool) -> List[str]:
    """Clean up a single node and return list of errors if any"""
    errors = []
    print(f"\n🧹 Cleaning up node: {hostname} ({ip})")

    commands = [
        "sudo systemctl stop k3s k3s-agent || true",  # Stop k3s services
        "sudo rm -rf /var/lib/rancher/k3s || true",  # Remove k3s data
        "sudo rm -rf /etc/rancher/k3s || true",  # Remove k3s config
        "sudo rm -rf /var/lib/longhorn || true",  # Remove Longhorn data
        "sudo rm -rf /var/lib/kubelet || true",  # Remove kubelet data
        "sudo rm -rf /opt/longhorn || true",  # Remove any Longhorn binaries
        "sudo rm -rf /var/lib/cni || true",  # Remove CNI data
        "sudo rm -rf /var/run/k3s || true",  # Remove runtime data
        "sudo ip link delete flannel.1 || true",  # Clean up network interfaces
        "sudo ip link delete cni0 || true",
    ]

    for cmd in commands:
        print(f"  ⚡ Running: {cmd}")
        if not run_ssh_command(ip, cmd):
            errors.append(f"Failed to run '{cmd}' on {hostname}")

    # Uninstall k3s
    uninstall_script = (
        "/usr/local/bin/k3s-uninstall.sh"
        if is_master
        else "/usr/local/bin/k3s-agent-uninstall.sh"
    )
    if not run_ssh_command(ip, f"sudo {uninstall_script}"):
        errors.append(f"Failed to run uninstall script on {hostname}")

    return errors


def reinstall_k3s_master(master_ip: str) -> List[str]:
    """Reinstall k3s on master node"""
    errors = []
    print(f"\n🚀 Reinstalling k3s on master ({master_ip})")

    # More aggressive cleanup
    cleanup_commands = [
        "sudo killall -9 k3s-server k3s agent containerd || true",
        "sudo systemctl stop k3s k3s-agent containerd",
        "sudo systemctl disable k3s k3s-agent",
        "sudo rm -rf /var/lib/rancher /etc/rancher",
        "sudo rm -rf /etc/systemd/system/k3s*",
        "sudo rm -rf /var/lib/containerd",
        "sudo systemctl daemon-reload",
        "sudo systemctl reset-failed"
    ]
    
    for cmd in cleanup_commands:
        print(f"  ⚡ Running: {cmd}")
        run_ssh_command(master_ip, cmd)
        time.sleep(1)

    # Install k3s with specific options for better control
    print("📥 Installing k3s...")
    install_cmd = """
    curl -sfL https://get.k3s.io | \
    INSTALL_K3S_EXEC="server \
    --write-kubeconfig-mode 644 \
    --tls-san $(hostname -I | cut -d' ' -f1)" sh -
    """
    
    if not run_ssh_command(master_ip, install_cmd):
        errors.append("Failed to install k3s")
        return errors

    # Wait for k3s to be fully running
    print("🔍 Verifying k3s installation...")
    for i in range(30):
        try:
            # Check both service status and API server
            checks = [
                "sudo systemctl is-active k3s",
                "sudo k3s kubectl get --raw '/healthz'"
            ]
            
            all_good = True
            for check in checks:
                result = subprocess.check_output([
                    "sshpass", "-p", PASSWORD, "ssh",
                    "-o", "StrictHostKeyChecking=no",
                    f"{USERNAME}@{master_ip}",
                    check
                ], stderr=subprocess.PIPE).decode().strip()
                
                if not (result == "active" or result == "ok"):
                    all_good = False
                    break
            
            if all_good:
                print("✅ k3s is fully operational")
                
                return errors
                
        except Exception as e:
            print(f"  ⏳ Waiting for k3s... ({i+1}/30)")
            time.sleep(2)

    errors.append("k3s failed to start properly")
    return errors


def get_node_token(master_ip: str) -> str:
    """Get node token from master"""
    print("⏳ Getting node token...")
    try:
        # Read from the standard k3s token location
        token = subprocess.check_output([
            "sshpass", "-p", PASSWORD, "ssh",
            "-o", "StrictHostKeyChecking=no",
            f"{USERNAME}@{master_ip}",
            "sudo cat /var/lib/rancher/k3s/server/node-token"
        ], stderr=subprocess.PIPE)
        return token.decode().strip()
    except:
        return ""



def join_worker(worker_ip: str, master_ip: str, node_token: str) -> List[str]:
    """Join a worker node to the cluster"""
    errors = []
    print(f"\n🔄 Joining worker node ({worker_ip})")

    join_cmd = f'curl -sfL https://get.k3s.io | K3S_URL="https://{master_ip}:6443" K3S_TOKEN="{node_token}" sh -'
    if not run_ssh_command(worker_ip, join_cmd):
        errors.append(f"Failed to join worker {worker_ip}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="K3s Cluster Reset Tool")
    parser.add_argument(
        "--confirm", action="store_true", help="Confirm destructive action"
    )
    args = parser.parse_args()

    if not args.confirm:
        print("⚠️  WARNING: This will completely reset your k3s cluster!")
        print("All data will be lost. Use --confirm to proceed.")
        return

    all_errors = []

    # 1. Clean up all nodes
    for hostname, ip, role in HOSTS:
        is_master = role == "master"
        errors = cleanup_node(hostname, ip, is_master)
        all_errors.extend(errors)

    # 2. Reinstall master
    master_ip = next(ip for _, ip, role in HOSTS if role == "master")
    errors = reinstall_k3s_master(master_ip)
    all_errors.extend(errors)

    # 3. Get node token
    print("\n🔑 Getting node token...")
    node_token = get_node_token(master_ip)
    if not node_token:
        all_errors.append("Failed to get node token")
        print("\n❌ Failed! Check the errors above.")
        return

    # 4. Join workers
    for hostname, ip, role in HOSTS:
        if role == "worker":
            errors = join_worker(ip, master_ip, node_token)
            all_errors.extend(errors)

    # Summary
    if all_errors:
        print("\n❌ Completed with errors:")
        for error in all_errors:
            print(f"  - {error}")
    else:
        print("\n✅ Cluster reset completed successfully!")
        print("\nNext steps:")
        print("1. Wait a few minutes for all nodes to be ready")
        print("2. Run: kubectl get nodes")
        print("3. Install ArgoCD")
        print("4. Apply your GitOps configuration")


if __name__ == "__main__":
    main()
