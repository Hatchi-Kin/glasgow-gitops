#!/usr/bin/env python3
"""
Choose Master Node - Compare worker nodes to select best master candidate
"""

import subprocess
import sys

USERNAME = "bsg"
PASSWORD = "mlop!"
WORKERS = [
    ("boomer", "192.168.1.21"),
    ("apollo", "192.168.1.22"),
    ("starbuck", "192.168.1.23"),
]


def ssh_command(ip, cmd):
    """Execute SSH command and return output"""
    try:
        result = subprocess.check_output(
            [
                "sshpass",
                "-p",
                PASSWORD,
                "ssh",
                "-o",
                "ConnectTimeout=3",
                "-o",
                "StrictHostKeyChecking=no",
                f"{USERNAME}@{ip}",
                cmd,
            ],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return result.decode().strip()
    except Exception:
        return None


def get_uptime(ip):
    """Get system uptime in seconds"""
    output = ssh_command(ip, "cat /proc/uptime")
    if output:
        return float(output.split()[0])
    return 0


def get_cpu_usage(ip):
    """Get current CPU usage percentage"""
    output = ssh_command(ip, "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
    if output:
        try:
            return float(output)
        except ValueError:
            return 0
    return 0


def get_memory_info(ip):
    """Get memory usage (used, total in MB)"""
    output = ssh_command(ip, "free -m | awk '/Mem:/ {print $3,$2}'")
    if output:
        parts = output.split()
        return int(parts[0]), int(parts[1])
    return 0, 0


def get_disk_usage(ip):
    """Get root disk usage percentage"""
    output = ssh_command(ip, "df -h / | awk 'NR==2 {print $5}' | tr -d '%'")
    if output:
        try:
            return int(output)
        except ValueError:
            return 0
    return 0


def get_temperature(ip):
    """Get CPU temperature in Celsius"""
    output = ssh_command(ip, "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
    if output:
        try:
            return int(output) / 1000.0
        except ValueError:
            return 0
    return 0


def get_error_count(ip):
    """Get system error count from last 7 days"""
    output = ssh_command(
        ip, "journalctl -p err --since '7 days ago' 2>/dev/null | grep -c '^'"
    )
    if output:
        try:
            return int(output)
        except ValueError:
            return 0
    return 0


def get_pod_count(hostname):
    """Get number of pods running on this node"""
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
        import json

        pods_data = json.loads(output.decode())
        running = sum(
            1
            for pod in pods_data.get("items", [])
            if pod["status"]["phase"] == "Running"
        )
        return running, len(pods_data.get("items", []))
    except Exception:
        return 0, 0


def score_node(hostname, ip):
    """Calculate a score for each node (higher = better candidate)"""
    print(f"\n{'='*50}")
    print(f"📊 Analyzing: {hostname} ({ip})")
    print(f"{'='*50}")

    score = 100  # Start with perfect score
    reasons = []

    # Uptime (higher is better - more stable)
    uptime_sec = get_uptime(ip)
    uptime_days = uptime_sec / 86400 if uptime_sec else 0
    print(f"⏱️  Uptime: {uptime_days:.1f} days")
    if uptime_days > 7:
        score += 10
        reasons.append(f"Excellent uptime ({uptime_days:.1f} days)")
    elif uptime_days < 1:
        score -= 5
        reasons.append(f"Recent reboot ({uptime_days:.1f} days)")

    # CPU usage (lower is better)
    cpu_usage = get_cpu_usage(ip)
    print(f"🖥️  CPU Usage: {cpu_usage:.1f}%")
    if cpu_usage < 20:
        score += 5
        reasons.append(f"Low CPU usage ({cpu_usage:.1f}%)")
    elif cpu_usage > 50:
        score -= 10
        reasons.append(f"High CPU usage ({cpu_usage:.1f}%)")

    # Memory usage (lower is better)
    mem_used, mem_total = get_memory_info(ip)
    mem_percent = (mem_used / mem_total * 100) if mem_total else 0
    print(f"💾 Memory: {mem_used}MB / {mem_total}MB ({mem_percent:.0f}%)")
    if mem_percent < 40:
        score += 5
        reasons.append(f"Low memory usage ({mem_percent:.0f}%)")
    elif mem_percent > 70:
        score -= 10
        reasons.append(f"High memory usage ({mem_percent:.0f}%)")

    # Disk usage (lower is better)
    disk_percent = get_disk_usage(ip)
    print(f"💿 Disk Usage: {disk_percent}%")
    if disk_percent < 50:
        score += 5
        reasons.append(f"Plenty of disk space ({disk_percent}%)")
    elif disk_percent > 80:
        score -= 15
        reasons.append(f"High disk usage ({disk_percent}%)")

    # Temperature (lower is better)
    temp = get_temperature(ip)
    print(f"🌡️  Temperature: {temp:.0f}°C")
    if temp < 50:
        score += 5
        reasons.append(f"Cool temperature ({temp:.0f}°C)")
    elif temp > 70:
        score -= 10
        reasons.append(f"High temperature ({temp:.0f}°C)")

    # Error count (lower is better)
    error_count = get_error_count(ip)
    print(f"⚠️  Errors (7d): {error_count}")
    if error_count == 0:
        score += 10
        reasons.append("No errors in logs")
    elif error_count > 50:
        score -= 15
        reasons.append(f"Many errors ({error_count})")

    # Pod count (lower is better - less to migrate)
    running_pods, total_pods = get_pod_count(hostname)
    print(f"🎯 Pods: {running_pods}/{total_pods} running")
    if running_pods < 5:
        score += 5
        reasons.append(f"Few pods ({running_pods})")
    elif running_pods > 15:
        score -= 5
        reasons.append(f"Many pods ({running_pods})")

    # IP address bonus (lower IP = easier to remember)
    if ip == "192.168.1.21":
        score += 5
        reasons.append("Lowest IP (easier to remember)")

    print(f"\n🏆 Score: {score}/100")
    if reasons:
        print(f"📝 Key factors:")
        for reason in reasons:
            print(f"   • {reason}")

    return score, reasons


def main():
    print("=" * 50)
    print("🔍 Master Node Candidate Evaluation")
    print("=" * 50)
    print("\nAnalyzing all worker nodes...\n")

    results = []

    for hostname, ip in WORKERS:
        score, reasons = score_node(hostname, ip)
        results.append((hostname, ip, score, reasons))

    # Sort by score (highest first)
    results.sort(key=lambda x: x[2], reverse=True)

    print("\n" + "=" * 50)
    print("📊 FINAL RANKINGS")
    print("=" * 50)

    for i, (hostname, ip, score, reasons) in enumerate(results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        print(f"\n{medal} #{i}: {hostname} ({ip})")
        print(f"   Score: {score}/100")

    winner_name, winner_ip, winner_score, winner_reasons = results[0]

    print("\n" + "=" * 50)
    print("✅ RECOMMENDATION")
    print("=" * 50)
    print(f"\n🎯 Choose: {winner_name} ({winner_ip})")
    print(f"\nWhy {winner_name}:")
    for reason in winner_reasons[:5]:  # Top 5 reasons
        print(f"  ✓ {reason}")

    print(
        f"\n💡 Next step: Use {winner_ip} as your new control plane IP in the migration"
    )
    print(f"   Update from: 192.168.1.20 (adama)")
    print(f"   Update to:   {winner_ip} ({winner_name})")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

