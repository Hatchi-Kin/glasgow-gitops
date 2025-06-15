import subprocess
import re

##  python3 quick_check.py

USERNAME = "bsg"
PASSWORD = "mlop!"
HOSTS = [
    ("adama", "192.168.1.20"),
    ("boomer", "192.168.1.21"),
    ("apollo", "192.168.1.22"),
    ("starbuck", "192.168.1.23"),
]

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
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
        return f"{temp_c:.1f}°C"
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
        return f"{float(output.decode().strip()):.1f}%"
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
        used_gb = used / 1024
        total_gb = total / 1024
        return f"{used_gb:.1f}/{total_gb:.1f}GB"
    except Exception:
        return "N/A"


print("Lab Status Check:\n")
print(f"{'IP':15} {'Ping':6} {'SSH':18} {'CPU':8} {'CPU%':7} {'RAM':12}")
print("-" * 70)
for _, ip in HOSTS:
    ping_status = f"{GREEN}UP{RESET}" if ping_host(ip) else f"{RED}DOWN{RESET}"
    ssh_result = ssh_check(ip)
    if ssh_result:
        cpu_temp = get_cpu_temp(ip)
        cpu_percent = get_cpu_percent(ip)
        ram_usage = get_ram_usage(ip)
        ssh_status = f"{GREEN}OK{RESET} ({ssh_result})"
    else:
        cpu_temp = cpu_percent = ram_usage = "N/A"
        ssh_status = f"{RED}FAIL{RESET}"

    print(
        f"{ip:15} {ping_status:{6+len(ping_status)-len(strip_ansi(ping_status))}} {ssh_status:{18+len(ssh_status)-len(strip_ansi(ssh_status))}} {cpu_temp:8} {cpu_percent:7} {ram_usage:12}"
    )
