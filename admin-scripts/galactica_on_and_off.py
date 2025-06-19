import subprocess
import time
import argparse

USERNAME = "bsg"
PASSWORD = "mlop!"
SUDO_PASSWORD = "mlop!"
HOSTS = [
    ("adama", "192.168.1.20", "master"),
    ("boomer", "192.168.1.21", "worker"),
    ("apollo", "192.168.1.22", "worker"),
    ("starbuck", "192.168.1.23", "worker"),
]


def run_ssh_command(hostname, ip, command, quiet=False):
    """Run a command over SSH on a remote host"""
    if not quiet:
        print(f"Running on {hostname}: {command}")
    try:
        result = subprocess.run(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ConnectTimeout=5",
                f"{USERNAME}@{ip}",
                command,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 and not quiet:
            print(f"Command failed on {hostname}: {result.stderr}")
            return False, result.stdout
        return True, result.stdout
    except Exception as e:
        if not quiet:
            print(f"Error on {hostname}: {e}")
        return False, None


def kubectl_command(command):
    """Run kubectl command on master node"""
    master_ip = next((ip for h, ip, role in HOSTS if role == "master"), None)
    if not master_ip:
        print("Error: No master node found")
        return False, None

    full_cmd = f"echo '{SUDO_PASSWORD}' | sudo -S kubectl {command}"
    return run_ssh_command("adama", master_ip, full_cmd)


def drain_node(hostname):
    """Drain a Kubernetes node before shutdown"""
    print(f"Draining node {hostname}...")
    cmd = f"drain {hostname} --ignore-daemonsets --delete-emptydir-data --timeout=300s"
    success, output = kubectl_command(cmd)
    if success:
        print(f"Successfully drained {hostname}")
    else:
        print(f"Warning: Failed to drain {hostname}, continuing anyway")
    return True


def uncordon_node(hostname):
    """Uncordon a Kubernetes node after startup"""
    print(f"Uncordoning node {hostname}...")
    success, output = kubectl_command(f"uncordon {hostname}")
    if success:
        print(f"Successfully uncordoned {hostname}")
    else:
        print(f"Warning: Failed to uncordon {hostname}")
    return success


def shutdown_machine(hostname, ip):
    """Shutdown a machine via SSH"""
    print(f"Shutting down {hostname} ({ip})...")
    shutdown_cmd = f"echo '{SUDO_PASSWORD}' | sudo -S shutdown -h now"
    try:
        subprocess.run(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ConnectTimeout=5",
                f"{USERNAME}@{ip}",
                shutdown_cmd,
            ],
            check=False,
        )
        return True
    except Exception as e:
        print(f"Failed to shutdown {hostname}: {e}")
        return False


def wait_for_node(hostname, ip, max_attempts=10):
    """Wait for a node to be accessible via SSH"""
    print(f"Waiting for {hostname} to be accessible...")
    for i in range(max_attempts):
        success, _ = run_ssh_command(hostname, ip, "echo 'connected'", quiet=True)
        if success:
            print(f"{hostname} is accessible!")
            return True
        print(f"Attempt {i+1}/{max_attempts}...")
        time.sleep(3)
    return False


def run_verification():
    """Run the verification script"""
    print("\nRunning cluster verification...")
    try:
        result = subprocess.run(
            ["python3", "quick_check.py"],
            cwd="/home/kin/Documents/glasgow-gitops/admin-scripts",
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to run verification script: {e}")
        return False


def cluster_off(args):
    """Shut down the K3s cluster"""
    if not args.force:
        answer = input("Shutdown entire cluster? (yes/no): ")
        if answer.lower() != "yes":
            print("Cancelled.")
            return

    # Get node lists
    worker_nodes = [(h, ip) for h, ip, role in HOSTS if role == "worker"]
    master_node = next(((h, ip) for h, ip, role in HOSTS if role == "master"), None)

    # 1. Drain worker nodes
    if not args.no_drain:
        for hostname, _ in worker_nodes:
            drain_node(hostname)
            time.sleep(1)

    # 2. Shutdown workers
    print("\nShutting down workers...")
    for hostname, ip in worker_nodes:
        shutdown_machine(hostname, ip)
        time.sleep(2)

    # 3. Shutdown master
    print(f"\nWaiting {args.wait}s before master shutdown...")
    time.sleep(args.wait)
    shutdown_machine(*master_node)

    print("\nShutdown complete!")
    print("After restart, run: python3 galactica_on_and_off.py on")


def cluster_on(args):
    """Start up and prepare the K3s cluster"""
    master_node = next(((h, ip) for h, ip, role in HOSTS if role == "master"), None)
    worker_nodes = [(h, ip) for h, ip, role in HOSTS if role == "worker"]

    # 1. Wait for master
    if not wait_for_node(*master_node, args.max_attempts):
        print("Master unreachable!")
        if not args.force:
            return

    # 2. Wait for K3s
    print(f"\nWaiting {args.wait}s for K3s...")
    time.sleep(args.wait)

    # 3. Uncordon all nodes
    print("\nUncordoning nodes...")
    for hostname, _ in worker_nodes:
        uncordon_node(hostname)
        time.sleep(1)

    # 4. Run verification
    if not args.skip_verify:
        run_verification()

    print("\nCluster ready! 🚀")


def status():
    """Check cluster status"""
    kubectl_command("get nodes")


def main():
    parser = argparse.ArgumentParser(description="Glasgow GitOps Cluster Management")
    subparsers = parser.add_subparsers(dest="command")

    # Status
    subparsers.add_parser("status", help="Check cluster status")

    # On
    on_parser = subparsers.add_parser("on", help="Startup cluster")
    on_parser.add_argument(
        "--wait", type=int, default=15, help="K3s init wait (default: 15s)"
    )
    on_parser.add_argument(
        "--max-attempts", type=int, default=10, help="Connection attempts"
    )
    on_parser.add_argument(
        "--skip-verify", action="store_true", help="Skip verification"
    )
    on_parser.add_argument("-f", "--force", action="store_true", help="Force startup")

    # Off
    off_parser = subparsers.add_parser("off", help="Shutdown cluster")
    off_parser.add_argument(
        "-f", "--force", action="store_true", help="No confirmation"
    )
    off_parser.add_argument("--no-drain", action="store_true", help="Skip draining")
    off_parser.add_argument("--wait", type=int, default=7, help="Master shutdown wait")

    args = parser.parse_args()

    if args.command == "on":
        cluster_on(args)
    elif args.command == "off":
        cluster_off(args)
    elif args.command == "status":
        status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
