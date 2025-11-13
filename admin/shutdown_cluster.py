#!/usr/bin/env python3
"""
Glasgow GitOps Cluster Shutdown Script
Gracefully shuts down all cluster nodes
"""
import subprocess
import time
import sys

USERNAME = "bsg"
PASSWORD = "mlop!"
HOSTS = [
    ("boomer", "192.168.1.21"),
    ("apollo", "192.168.1.22"),
    ("starbuck", "192.168.1.23"),
    ("adama", "192.168.1.20"),  # Control plane last
]

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def drain_node(node_name):
    """Drain a node gracefully"""
    print(f"🔄 Draining {node_name}...")
    if node_name == "adama":
        cmd = f"kubectl drain {node_name} --ignore-daemonsets --delete-emptydir-data --disable-eviction"
    else:
        cmd = f"kubectl drain {node_name} --ignore-daemonsets --delete-emptydir-data"
    
    success, out, err = run_command(cmd)
    if success:
        print(f"✅ {node_name} drained successfully")
    else:
        print(f"⚠️  {node_name} drain warning: {err}")
    time.sleep(5)

def shutdown_host(hostname, ip):
    """SSH into host and shut down"""
    print(f"🛑 Shutting down {hostname} ({ip})...")
    cmd = f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no {USERNAME}@{ip} 'sudo shutdown -h now'"
    success, out, err = run_command(cmd)
    if success:
        print(f"✅ {hostname} shutdown initiated")
    else:
        print(f"❌ Failed to shut down {hostname}: {err}")

def main():
    print("🏠 Glasgow GitOps Cluster Shutdown")
    print("=" * 50)
    
    confirm = input("⚠️  This will shut down ALL cluster nodes. Continue? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        sys.exit(0)
    
    print("\n📋 Draining all nodes...")
    
    # Drain all worker nodes first
    for hostname, ip in HOSTS[:-1]:  # All except adama
        drain_node(hostname)
    
    # Drain control plane last
    drain_node(HOSTS[-1][0])
    
    print("\n⏳ Waiting 10 seconds before shutting down nodes...")
    time.sleep(10)
    
    print("\n🔌 Initiating shutdown sequence...")
    
    # Shut down all nodes
    for hostname, ip in HOSTS:
        shutdown_host(hostname, ip)
        time.sleep(2)
    
    print("\n🎉 All nodes are shutting down!")
    print("💡 To restart: Power on all nodes, starting with adama (control plane)")

if __name__ == "__main__":
    main()