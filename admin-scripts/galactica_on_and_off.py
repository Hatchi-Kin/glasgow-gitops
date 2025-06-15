#!/usr/bin/env python3
# filepath: /home/kin/Documents/mykuber/galactica_on_and_off.py

import subprocess
import time
import sys
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
            check=False
        )
        if result.returncode != 0 and not quiet:
            print(f"Command failed on {hostname}: {result.stderr}")
            return False, result.stdout
        return True, result.stdout
    except Exception as e:
        if not quiet:
            print(f"Error on {hostname}: {e}")
        return False, None


def check_node_status():
    """Check status of all nodes"""
    print("Checking node status...")
    master_ip = next((ip for h, ip, role in HOSTS if role == "master"), None)
    if not master_ip:
        print("Error: No master node found")
        return {}
    
    cmd = f"echo '{SUDO_PASSWORD}' | sudo -S kubectl get nodes -o wide"
    success, output = run_ssh_command("adama", master_ip, cmd)
    
    if not success:
        print("Failed to get node status")
        return {}
    
    print("\nCurrent node status:")
    print(output)
    
    return output


def cordon_node(hostname):
    """Cordon a Kubernetes node before shutdown"""
    print(f"Cordoning node {hostname}...")
    master_ip = next((ip for h, ip, role in HOSTS if role == "master"), None)
    if not master_ip:
        print("Error: No master node found")
        return False
    
    full_cmd = f"echo '{SUDO_PASSWORD}' | sudo -S kubectl cordon {hostname}"
    
    success, output = run_ssh_command("adama", master_ip, full_cmd)
    if success:
        print(f"Successfully cordoned {hostname}")
    else:
        print(f"Warning: Failed to cordon {hostname}, continuing anyway")
    return True


def uncordon_node(hostname):
    """Uncordon a Kubernetes node after startup"""
    print(f"Uncordoning node {hostname}...")
    master_ip = next((ip for h, ip, role in HOSTS if role == "master"), None)
    if not master_ip:
        print("Error: No master node found")
        return False
    
    full_cmd = f"echo '{SUDO_PASSWORD}' | sudo -S kubectl uncordon {hostname}"
    
    success, output = run_ssh_command("adama", master_ip, full_cmd)
    if success:
        print(f"Successfully uncordoned {hostname}")
    else:
        print(f"Warning: Failed to uncordon {hostname}")
    return True


def shutdown_machine(hostname, ip, is_worker=True):
    """Shutdown a machine via SSH"""
    print(f"Shutting down {hostname} ({ip})...")
    try:
        # Execute shutdown command via SSH with sudo password
        shutdown_cmd = f"echo '{SUDO_PASSWORD}' | sudo -S shutdown -h now"
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
            check=False  # Don't raise exception, as SSH connection will close
        )
        return True
    except Exception as e:
        print(f"Failed to shutdown {hostname} ({ip}): {e}")
        return False


def wait_for_node(hostname, ip, max_attempts=10):
    """Wait for a node to be accessible via SSH"""
    print(f"Waiting for {hostname} ({ip}) to be accessible...")
    
    for i in range(max_attempts):
        cmd = "echo 'connected'"
        success, _ = run_ssh_command(hostname, ip, cmd, quiet=True)
        if success:
            print(f"{hostname} is accessible!")
            return True
        print(f"Attempt {i+1}/{max_attempts}...")
        time.sleep(3)
    
    print(f"Warning: Could not connect to {hostname} after {max_attempts} attempts")
    return False


def cluster_off(args):
    """Shut down the K3s cluster"""
    if not args.force:
        answer = input("Are you sure you want to shutdown the entire K3s cluster? (yes/no): ")
        if answer.lower() != "yes":
            print("Shutdown cancelled.")
            sys.exit(0)

    # Check current status
    check_node_status()

    results = []
    worker_nodes = [(h, ip) for h, ip, role in HOSTS if role == "worker"]
    master_node = next(((h, ip) for h, ip, role in HOSTS if role == "master"), None)

    if not master_node:
        print("Error: No master node configured")
        sys.exit(1)

    # 1. First cordon worker nodes if not skipped
    if not args.no_cordon:
        for hostname, _ in worker_nodes:
            cordon_node(hostname)
            time.sleep(1)

    # 2. Shutdown worker nodes
    print("\nShutting down worker nodes...")
    for hostname, ip in worker_nodes:
        success = shutdown_machine(hostname, ip, is_worker=True)
        results.append((hostname, success))
        time.sleep(2)  # Longer delay between shutdowns

    # 3. Finally shutdown master node
    print(f"\nWaiting {args.wait} seconds before shutting down master node...")
    time.sleep(args.wait)  # Give time for worker nodes to fully shutdown
    master_hostname, master_ip = master_node
    success = shutdown_machine(master_hostname, master_ip, is_worker=False)
    results.append((master_hostname, success))

    # Print summary
    print("\nShutdown Summary:")
    for hostname, success in results:
        status = "Shutdown initiated" if success else "FAILED"
        print(f"{hostname}: {status}")
    
    print("\nIMPORTANT: After restart, run 'python3 galactica_on_and_off.py on' to uncordon nodes")


def cluster_on(args):
    """Start up and prepare the K3s cluster"""
    master_node = next(((h, ip) for h, ip, role in HOSTS if role == "master"), None)
    worker_nodes = [(h, ip) for h, ip, role in HOSTS if role == "worker"]
    
    if not master_node:
        print("Error: No master node configured")
        sys.exit(1)
    
    # 1. Wait for master to be accessible
    master_hostname, master_ip = master_node
    if not wait_for_node(master_hostname, master_ip, args.max_attempts):
        print("Cannot reach master node. Ensure it's powered on.")
        if not args.force:
            sys.exit(1)
    
    # 2. Wait a bit for K3s to start
    print(f"\nWaiting {args.wait} seconds for K3s to initialize...")
    time.sleep(args.wait)
    
    # 3. Check node status
    check_node_status()
    
    # 4. Uncordon all nodes
    for hostname, _ in worker_nodes:
        uncordon_node(hostname)
        time.sleep(1)
    
    # 5. Final status check
    time.sleep(3)
    check_node_status()
    
    print("\nCluster is now ready!")


def status(args):
    """Check cluster status"""
    check_node_status()


def main():
    parser = argparse.ArgumentParser(description="K3s Cluster Management")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check cluster status")
    
    # On command
    on_parser = subparsers.add_parser("on", help="Prepare cluster after startup")
    on_parser.add_argument(
        "--wait", type=int, default=15, 
        help="Seconds to wait for K3s to initialize (default: 15)"
    )
    on_parser.add_argument(
        "--max-attempts", type=int, default=10,
        help="Maximum attempts to connect to nodes (default: 10)"
    )
    on_parser.add_argument(
        "-f", "--force", action="store_true",
        help="Continue even if master node is unreachable"
    )
    
    # Off command
    off_parser = subparsers.add_parser("off", help="Shut down cluster")
    off_parser.add_argument(
        "-f", "--force", action="store_true", 
        help="Force shutdown without confirmation"
    )
    off_parser.add_argument(
        "--no-cordon", action="store_true", 
        help="Skip cordoning nodes"
    )
    off_parser.add_argument(
        "--wait", type=int, default=7,
        help="Seconds to wait before shutting down master (default: 7)"
    )
    
    args = parser.parse_args()
    
    if args.command == "on":
        cluster_on(args)
    elif args.command == "off":
        cluster_off(args)
    elif args.command == "status":
        status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()