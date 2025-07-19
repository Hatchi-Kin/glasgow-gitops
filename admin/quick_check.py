#!/usr/bin/env python3
"""
Glasgow GitOps Cluster Health Check
Quick status check for all cluster components
"""

import subprocess
import sys
import re
import json
from datetime import datetime

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
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def strip_ansi(text):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def ping_host(ip):
    try:
        subprocess.check_output(
            ["ping", "-c", "1", "-W", "1", ip], stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def ssh_check(ip):
    try:
        output = subprocess.check_output(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                f"{USERNAME}@{ip}",
                "hostname",
            ],
            stderr=subprocess.DEVNULL,
        )
        return output.decode().strip()
    except subprocess.CalledProcessError:
        return None


def get_cpu_temp(ip):
    try:
        output = subprocess.check_output(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                f"{USERNAME}@{ip}",
                "cat /sys/class/thermal/thermal_zone0/temp",
            ],
            stderr=subprocess.DEVNULL,
        )
        temp_c = int(output.decode().strip()) / 1000
        return f"{temp_c:.0f}°C"
    except Exception:
        return "N/A"


def get_cpu_percent(ip):
    try:
        output = subprocess.check_output(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                f"{USERNAME}@{ip}",
                "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'",
            ],
            stderr=subprocess.DEVNULL,
        )
        cpu_usage = float(output.decode().strip())
        return f"{cpu_usage:.0f}%"
    except Exception:
        return "N/A"


def get_ram_usage(ip):
    try:
        output = subprocess.check_output(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                f"{USERNAME}@{ip}",
                "free -m | awk '/Mem:/ {print $3 \" \" $2}'",
            ],
            stderr=subprocess.DEVNULL,
        )
        used, total = map(int, output.decode().strip().split())
        usage_percent = (used / total) * 100
        return f"{usage_percent:.0f}%"
    except Exception:
        return "N/A"


def get_disk_usage(ip):
    try:
        output = subprocess.check_output(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "ConnectTimeout=2",
                "-o",
                "StrictHostKeyChecking=no",
                f"{USERNAME}@{ip}",
                "df -h / | awk 'NR==2 {print $5}'",
            ],
            stderr=subprocess.DEVNULL,
        )
        usage = output.decode().strip().replace("%", "")
        return f"{usage}%"
    except Exception:
        return "N/A"


def kubectl_get_nodes():
    """Get Kubernetes node status"""
    try:
        output = subprocess.check_output(
            ["kubectl", "get", "nodes", "-o", "json"],
            stderr=subprocess.DEVNULL,
        )
        nodes_data = json.loads(output.decode())
        return nodes_data
    except Exception:
        return None


def get_k8s_node_status(hostname, nodes_data):
    """Get Kubernetes status for a specific node"""
    if not nodes_data:
        return "N/A"
    for node in nodes_data.get("items", []):
        if node["metadata"]["name"] == hostname:
            conditions = node["status"]["conditions"]
            ready_condition = next(
                (c for c in conditions if c["type"] == "Ready"), None
            )
            if ready_condition and ready_condition["status"] == "True":
                unschedulable = node["spec"].get("unschedulable", False)
                if unschedulable:
                    return "Cordoned"
                else:
                    return "Ready"
            else:
                return "NotReady"
    return "NotFound"


def get_pod_count(hostname):
    """Get running pod count for a node"""
    try:
        output = subprocess.check_output(
            [
                "kubectl",
                "get",
                "pods",
                "--all-namespaces",
                "--field-selector",
                f"spec.nodeName={hostname}",
                "-o",
                "json",
            ],
            stderr=subprocess.DEVNULL,
        )
        pods_data = json.loads(output.decode())
        running_pods = sum(
            1
            for pod in pods_data.get("items", [])
            if pod["status"]["phase"] == "Running"
        )
        total_pods = len(pods_data.get("items", []))
        return f"{running_pods}/{total_pods}"
    except Exception:
        return "N/A"


def check_nodes():
    """Check cluster nodes status"""
    print("🔍 Checking K3s Nodes...")
    success, output, error = run_command("kubectl get nodes")
    if success:
        print("✅ Nodes:")
        print(output)
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
        lines = output.split("\n")[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split()
                name = parts[0]
                sync_status = parts[1] if len(parts) > 1 else "Unknown"
                health_status = parts[2] if len(parts) > 2 else "Unknown"
                sync_icon = "✅" if sync_status == "Synced" else "⚠️"
                health_icon = "✅" if health_status == "Healthy" else "⚠️"
                print(
                    f"   {sync_icon} {health_icon} {name}: {sync_status}/{health_status}"
                )
    else:
        print(f"❌ Failed to get applications: {error}")
    print()


def check_pods():
    """Check pods in glasgow-prod namespace"""
    print("🔍 Checking Pods in glasgow-prod...")
    success, output, error = run_command("kubectl get pods -n glasgow-prod")
    if success:
        print("✅ Pods:")
        lines = output.split("\n")[1:]  # Skip header
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
    success, output, error = run_command("kubectl get pvc -n glasgow-prod")
    if success:
        print("✅ Persistent Volume Claims:")
        lines = output.split("\n")[1:]  # Skip header
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
        lines = output.split("\n")[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split()
                name = parts[0]
                age = parts[1] if len(parts) > 1 else "Unknown"
                print(f"   ✅ {name}: {age} old")
        success2, output2, error2 = run_command("kubectl get secrets -n glasgow-prod")
        if success2:
            secret_count = len(output2.split("\n")) - 1
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
        lines = output.split("\n")[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split()
                name = parts[0]
                hosts = parts[2] if len(parts) > 2 else "No host"
                print(f"   🌐 {name}: http://{hosts}")
    else:
        print(f"❌ Failed to get ingress: {error}")
    print()


def get_node_system_summary():
    """Get concise CPU temp, RAM, SSD usage for each node using SSH (no colors, aligned)"""
    print("\n🖥️  System Summary (via SSH):")
    print(f"{'Node':<10} {'CPU Temp':<9} {'RAM Used':<9} {'SSD Used':<9}")
    print("-" * 40)
    for hostname, ip, _ in HOSTS:
        cpu_temp = get_cpu_temp(ip)
        ram_used = get_ram_usage(ip)
        ssd_used = get_disk_usage(ip)
        print(f"{hostname:<10} {cpu_temp:<9} {ram_used:<9} {ssd_used:<9}")


def main():
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
    print(
        '   - Force sync: kubectl patch application <app> -n argocd --type merge -p=\'{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}\''
    )
    # Per-node system summary
    get_node_system_summary()
    print("")


if __name__ == "__main__":
    main()
