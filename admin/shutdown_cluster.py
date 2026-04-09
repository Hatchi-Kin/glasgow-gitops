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
    # Use --force to handle standalone pods and --disable-eviction for stuck pods
    cmd = f"kubectl drain {node_name} --ignore-daemonsets --delete-emptydir-data --force --disable-eviction --grace-period=30 --timeout=60s"
    
    success, out, err = run_command(cmd)
    if success:
        print(f"✅ {node_name} drained successfully")
    else:
        print(f"⚠️  {node_name} drain warning: {err}")
        # Try to force delete any remaining pods on this node
        print(f"   Attempting to force delete remaining pods on {node_name}...")
        force_cmd = f"kubectl delete pods --all-namespaces --field-selector spec.nodeName={node_name} --force --grace-period=0"
        run_command(force_cmd)
    time.sleep(3)

def shutdown_host(hostname, ip):
    """SSH into host and shut down"""
    print(f"🛑 Shutting down {hostname} ({ip})...")
    cmd = f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no {USERNAME}@{ip} 'sudo shutdown -h now'"
    success, out, err = run_command(cmd)
    if success:
        print(f"✅ {hostname} shutdown initiated")
    else:
        print(f"❌ Failed to shut down {hostname}: {err}")

def cleanup_standalone_pods():
    """Delete standalone pods that block draining"""
    print("🧹 Cleaning up standalone pods...")
    
    # Delete iperf3-server and any other standalone pods
    cmd = "kubectl get pods --all-namespaces --field-selector status.phase=Running -o json"
    success, out, err = run_command(cmd)
    
    if success and out:
        import json
        try:
            data = json.loads(out)
            for pod in data.get('items', []):
                owner_refs = pod.get('metadata', {}).get('ownerReferences', [])
                if not owner_refs:  # No controller
                    pod_name = pod['metadata']['name']
                    namespace = pod['metadata']['namespace']
                    print(f"   Deleting standalone pod: {namespace}/{pod_name}")
                    run_command(f"kubectl delete pod {pod_name} -n {namespace} --force --grace-period=0")
        except:
            pass
    
    time.sleep(2)

def main():
    print("🏠 Glasgow GitOps Cluster Shutdown")
    print("=" * 50)
    
    confirm = input("⚠️  This will shut down ALL cluster nodes. Continue? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        sys.exit(0)
    
    # Clean up standalone pods first
    cleanup_standalone_pods()
    
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