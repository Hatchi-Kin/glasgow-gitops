#!/usr/bin/env python3
"""
Glasgow GitOps Longhorn Mount Cleanup Script
Unmounts stale Longhorn volumes and restarts k3s on all nodes
"""
import subprocess
import time
import sys

USERNAME = "bsg"
PASSWORD = "mlop!"
HOSTS = [
    ("adama", "192.168.1.20", "master"),
    ("boomer", "192.168.1.21", "worker"),
    ("apollo", "192.168.1.22", "worker"),
    ("starbuck", "192.168.1.23", "worker"),
]

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def cleanup_node(hostname, ip, node_type):
    """SSH into node and clean up stale Longhorn mounts"""
    print(f"🧹 Cleaning {hostname} ({ip})...")
    
    # Unmount stale Longhorn mount points
    unmount_cmd = f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no {USERNAME}@{ip} 'sudo umount -l /var/lib/kubelet/plugins/kubernetes.io/csi/driver.longhorn.io/*/globalmount 2>/dev/null; sudo umount -l /var/lib/kubelet/pods/*/volumes/kubernetes.io~csi/pvc-*/mount 2>/dev/null; echo Done'"
    
    success, out, err = run_command(unmount_cmd)
    if success:
        print(f"   ✅ Unmounted stale volumes")
    else:
        print(f"   ⚠️  Unmount attempt: {out}")
    
    time.sleep(2)
    
    # Restart k3s service
    print(f"   🔄 Restarting k3s...")
    if node_type == "master":
        service_name = "k3s"
    else:
        service_name = "k3s-agent"
    
    restart_cmd = f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no {USERNAME}@{ip} 'sudo systemctl restart {service_name}'"
    
    success, out, err = run_command(restart_cmd)
    if success:
        print(f"   ✅ {service_name} restarted")
    else:
        print(f"   ⚠️  Restart warning: {err}")
    
    time.sleep(5)

def main():
    print("🏠 Glasgow GitOps Longhorn Cleanup")
    print("=" * 50)
    print("This will unmount stale Longhorn volumes and restart k3s on all nodes.")
    print()
    
    confirm = input("⚠️  Continue? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        sys.exit(0)
    
    print("\n🧹 Starting cleanup sequence...\n")
    
    # Clean all nodes
    for hostname, ip, node_type in HOSTS:
        cleanup_node(hostname, ip, node_type)
    
    print("\n⏳ Waiting 30 seconds for k3s to stabilize...")
    time.sleep(30)
    
    print("\n🔄 Deleting stuck pods to force remount...")
    delete_cmd = "kubectl delete pods -n glasgow-prod --all --ignore-not-found=true"
    success, out, err = run_command(delete_cmd)
    if success:
        print("✅ Pods deleted, they will restart with fresh mounts")
    else:
        print(f"⚠️  Pod deletion: {err}")
    
    print("\n🎉 Cleanup complete!")
    print("💡 Run: python3 admin/quick_check.py")

if __name__ == "__main__":
    main()