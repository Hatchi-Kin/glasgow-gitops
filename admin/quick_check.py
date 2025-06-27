import subprocess
import re
import json
import argparse

##  python3 quick_check.py

USERNAME = "bsg"
PASSWORD = "mlop!"
HOSTS = [
    ("adama", "192.168.1.20", "master"),
    ("boomer", "192.168.1.21", "worker"),
    ("apollo", "192.168.1.22", "worker"),
    ("starbuck", "192.168.1.23", "worker"),
]

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


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
        color = RED if temp_c > 80 else YELLOW if temp_c > 70 else GREEN
        return f"{color}{temp_c:.0f}°C{RESET}"
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
        color = RED if cpu_usage > 90 else YELLOW if cpu_usage > 70 else GREEN
        return f"{color}{cpu_usage:.0f}%{RESET}"
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
        color = RED if usage_percent > 90 else YELLOW if usage_percent > 70 else GREEN
        return f"{color}{usage_percent:.0f}%{RESET}"
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
        usage_int = int(usage)
        color = RED if usage_int > 90 else YELLOW if usage_int > 80 else GREEN
        return f"{color}{usage}%{RESET}"
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
                    return f"{YELLOW}Cordoned{RESET}"
                else:
                    return f"{GREEN}Ready{RESET}"
            else:
                return f"{RED}NotReady{RESET}"

    return f"{RED}NotFound{RESET}"


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


def check_k8s_services():
    """Check status of key Kubernetes services"""
    services = {
        "ArgoCD": ("argocd", "app.kubernetes.io/name=argocd-server"),
        "MinIO": ("glasgow-prod", "app=minio"),
        "PostgreSQL": ("glasgow-prod", "app=postgres"),
        "FastAPI": ("glasgow-prod", "app=fastapi"),
        "n8n": ("glasgow-prod", "app=n8n"),
    }

    print(f"\n{CYAN}=== Applications ==={RESET}")

    for service_name, (namespace, selector) in services.items():
        try:
            output = subprocess.check_output(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-n",
                    namespace,
                    "-l",
                    selector,
                    "-o",
                    "json",
                ],
                stderr=subprocess.DEVNULL,
            )
            pods_data = json.loads(output.decode())
            pods = pods_data.get("items", [])

            if not pods:
                status = f"{RED}No Pods{RESET}"
                ready = "0/0"
            else:
                running = sum(1 for pod in pods if pod["status"]["phase"] == "Running")
                ready_count = 0
                for pod in pods:
                    if pod["status"]["phase"] == "Running":
                        conditions = pod["status"].get("conditions", [])
                        ready_condition = next(
                            (c for c in conditions if c["type"] == "Ready"), None
                        )
                        if ready_condition and ready_condition["status"] == "True":
                            ready_count += 1

                total = len(pods)
                if running == total and ready_count == total:
                    status = f"{GREEN}OK{RESET}"
                elif running > 0:
                    status = f"{YELLOW}Partial{RESET}"
                else:
                    status = f"{RED}Down{RESET}"

                ready = f"{ready_count}/{total}"

            print(f"  {service_name:10} {status:15} ({ready})")

        except Exception:
            print(f"  {service_name:10} {RED}Error{RESET:15} (N/A)")


def check_pvc_status():
    """Check Persistent Volume Claims status"""
    try:
        output = subprocess.check_output(
            ["kubectl", "get", "pvc", "--all-namespaces", "-o", "json"],
            stderr=subprocess.DEVNULL,
        )
        pvc_data = json.loads(output.decode())
        pvcs = pvc_data.get("items", [])

        if pvcs:
            print(f"\n{CYAN}=== Storage ==={RESET}")

            for pvc in pvcs:
                name = pvc["metadata"]["name"]
                namespace = pvc["metadata"]["namespace"]
                status = pvc["status"]["phase"]
                capacity = pvc["status"].get("capacity", {}).get("storage", "N/A")

                status_color = GREEN if status == "Bound" else RED
                print(f"  {name:12} {status_color}{status:8}{RESET} ({capacity})")

    except Exception:
        print(f"\n{RED}Error checking storage{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Glasgow GitOps Cluster Health Check")
    parser.add_argument("--basic", action="store_true", help="Basic node check only")
    parser.add_argument("--apps", action="store_true", help="Applications only")
    parser.add_argument("--compact", action="store_true", help="Compact output")
    args = parser.parse_args()

    if args.apps:
        check_k8s_services()
        check_pvc_status()
        return

    # Get Kubernetes node data
    nodes_data = kubectl_get_nodes()

    print(f"{BLUE}🚀 Glasgow GitOps Status{RESET}")
    print()

    if args.compact:
        # Ultra compact format
        print(f"{'Node':8} {'Status':12} {'Pods':5} {'CPU':4} {'RAM':4} {'Disk':4}")
        print("-" * 45)

        for hostname, ip, expected_role in HOSTS:
            if ping_host(ip) and ssh_check(ip):
                k8s_status = get_k8s_node_status(hostname, nodes_data)
                pod_count = get_pod_count(hostname)
                cpu_temp = get_cpu_temp(ip)
                ram_usage = get_ram_usage(ip)
                disk_usage = get_disk_usage(ip)

                print(
                    f"{hostname:8} {k8s_status:22} {pod_count:5} {cpu_temp:14} {ram_usage:14} {disk_usage:14}"
                )
            else:
                print(
                    f"{hostname:8} {RED}Offline{RESET:22} {'N/A':5} {'N/A':14} {'N/A':14} {'N/A':14}"
                )
    else:
        # Standard format - each node on separate lines
        for hostname, ip, expected_role in HOSTS:
            role_symbol = "🎯" if expected_role == "master" else "⚙️"
            print(f"{role_symbol} {BLUE}{hostname.upper()}{RESET} ({ip})")

            if ping_host(ip):
                ssh_result = ssh_check(ip)
                if ssh_result:
                    k8s_status = get_k8s_node_status(hostname, nodes_data)
                    pod_count = get_pod_count(hostname)
                    cpu_temp = get_cpu_temp(ip)
                    cpu_percent = get_cpu_percent(ip)
                    ram_usage = get_ram_usage(ip)
                    disk_usage = get_disk_usage(ip)

                    print(f"  Status: {k8s_status}")
                    print(
                        f"  Pods: {pod_count} | CPU: {cpu_temp} ({cpu_percent}) | RAM: {ram_usage} | Disk: {disk_usage}"
                    )
                else:
                    print(f"  Status: {RED}SSH Failed{RESET}")
            else:
                print(f"  Status: {RED}Offline{RESET}")
            print()

    if not args.basic:
        check_k8s_services()
        check_pvc_status()

        # Cluster summary
        if nodes_data:
            total_nodes = len(nodes_data.get("items", []))
            ready_nodes = sum(
                1
                for node in nodes_data.get("items", [])
                for condition in node["status"]["conditions"]
                if condition["type"] == "Ready" and condition["status"] == "True"
            )

            print(f"\n{CYAN}=== Summary ==={RESET}")
            print(f"Cluster: {GREEN}{ready_nodes}/{total_nodes} Ready{RESET}")

            # Check cordoned nodes
            cordoned_nodes = [
                node["metadata"]["name"]
                for node in nodes_data.get("items", [])
                if node["spec"].get("unschedulable", False)
            ]
            if cordoned_nodes:
                print(f"Cordoned: {YELLOW}{', '.join(cordoned_nodes)}{RESET}")
                print(f"💡 Fix: kubectl uncordon {' '.join(cordoned_nodes)}")


if __name__ == "__main__":
    main()
