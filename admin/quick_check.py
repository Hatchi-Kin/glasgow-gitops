#!/usr/bin/env python3
"""
Glasgow GitOps Cluster Health Check
Quick status check for all cluster components
"""

import subprocess
import sys
from datetime import datetime

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_nodes():
    """Check cluster nodes status"""
    print("🔍 Checking K3s Nodes...")
    success, output, error = run_command("kubectl get nodes")
    if success:
        print("✅ Nodes:")
        print(output)
        # Count ready nodes
        ready_count = output.count("Ready")
        print(f"   {ready_count} nodes ready")
    else:
        print(f"❌ Failed to get nodes: {error}")
    print()

def check_applications():
    """Check ArgoCD applications"""
    print("🔍 Checking ArgoCD Applications...")
    success, output, error = run_command("kubectl get applications -n argocd")
    if success:
        print("✅ Applications:")
        lines = output.split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split()
                name = parts[0]
                sync_status = parts[1] if len(parts) > 1 else "Unknown"
                health_status = parts[2] if len(parts) > 2 else "Unknown"
                
                # Color coding
                sync_icon = "✅" if sync_status == "Synced" else "⚠️"
                health_icon = "✅" if health_status == "Healthy" else "⚠️"
                
                print(f"   {sync_icon} {health_icon} {name}: {sync_status}/{health_status}")
    else:
        print(f"❌ Failed to get applications: {error}")
    print()

def check_pods():
    """Check pods in glasgow-prod namespace"""
    print("🔍 Checking Pods in glasgow-prod...")
    success, output, error = run_command("kubectl get pods -n glasgow-prod")
    if success:
        print("✅ Pods:")
        lines = output.split('\n')[1:]  # Skip header
        running_count = 0
        total_count = 0
        
        for line in lines:
            if line.strip():
                total_count += 1
                parts = line.split()
                name = parts[0]
                ready = parts[1]
                status = parts[2]
                
                if status == "Running" and "/" in ready:
                    ready_nums = ready.split("/")
                    if ready_nums[0] == ready_nums[1]:
                        running_count += 1
                        print(f"   ✅ {name}: {status} ({ready})")
                    else:
                        print(f"   ⚠️ {name}: {status} ({ready})")
                else:
                    print(f"   ❌ {name}: {status} ({ready})")
        
        print(f"   {running_count}/{total_count} pods running properly")
    else:
        print(f"❌ Failed to get pods: {error}")
    print()

def check_storage():
    """Check Longhorn storage"""
    print("🔍 Checking Storage...")
    
    # Check PVCs
    success, output, error = run_command("kubectl get pvc -n glasgow-prod")
    if success:
        print("✅ Persistent Volume Claims:")
        lines = output.split('\n')[1:]  # Skip header
        bound_count = 0
        total_count = 0
        
        for line in lines:
            if line.strip():
                total_count += 1
                parts = line.split()
                name = parts[0]
                status = parts[1]
                
                if status == "Bound":
                    bound_count += 1
                    print(f"   ✅ {name}: {status}")
                else:
                    print(f"   ❌ {name}: {status}")
        
        print(f"   {bound_count}/{total_count} PVCs bound")
    else:
        print(f"❌ Failed to get PVCs: {error}")
    print()

def check_secrets():
    """Check sealed secrets"""
    print("🔍 Checking Sealed Secrets...")
    success, output, error = run_command("kubectl get sealedsecrets -n glasgow-prod")
    if success:
        print("✅ Sealed Secrets:")
        lines = output.split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split()
                name = parts[0]
                age = parts[1] if len(parts) > 1 else "Unknown"
                print(f"   ✅ {name}: {age} old")
        
        # Check if regular secrets exist
        success2, output2, error2 = run_command("kubectl get secrets -n glasgow-prod")
        if success2:
            secret_count = len(output2.split('\n')) - 1
            print(f"   {secret_count} regular secrets created")
    else:
        print(f"❌ Failed to get sealed secrets: {error}")
    print()

def check_ingress():
    """Check ingress endpoints"""
    print("🔍 Checking Ingress Endpoints...")
    success, output, error = run_command("kubectl get ingress -n glasgow-prod")
    if success:
        print("✅ Ingress:")
        lines = output.split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split()
                name = parts[0]
                hosts = parts[2] if len(parts) > 2 else "No host"
                print(f"   🌐 {name}: http://{hosts}")
    else:
        print(f"❌ Failed to get ingress: {error}")
    print()

def main():
    """Main health check"""
    print(f"🏠 Glasgow GitOps Cluster Health Check")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print()
    
    # Check if kubectl is available
    success, _, _ = run_command("kubectl version --client")
    if not success:
        print("❌ kubectl not found or not configured")
        sys.exit(1)
    
    # Run all checks
    check_nodes()
    check_applications()
    check_pods()
    check_storage()
    check_secrets()
    check_ingress()
    
    print("🎉 Health check complete!")
    print("\n💡 Tips:")
    print("   - All services: kubectl get all -n glasgow-prod")
    print("   - ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443")
    print("   - Force sync: kubectl patch application <app> -n argocd --type merge -p='{\"operation\":{\"initiatedBy\":{\"username\":\"admin\"},\"sync\":{\"revision\":\"HEAD\"}}}'")

if __name__ == "__main__":
    main()
