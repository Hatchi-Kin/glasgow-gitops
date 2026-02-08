#!/usr/bin/env python3
"""
Glasgow GitOps Cluster Management Script
Easily start/stop/restart cluster components
"""

import subprocess
import sys
import time
import argparse


def run_command(cmd, show_output=True):
    """Run a command and optionally show output"""
    if show_output:
        print(f"🔧 Running: {cmd}")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=not show_output, text=True
        )
        if show_output:
            return result.returncode == 0
        else:
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def stop_all_apps():
    """Stop all applications (scale to 0)"""
    print("🛑 Stopping all applications...")

    apps = ["postgres", "minio", "fastapi", "n8n"]

    for app in apps:
        print(f"   Stopping {app}...")
        run_command(f"kubectl scale deployment {app} --replicas=0 -n glasgow-prod")

    print("✅ All applications stopped")


def start_all_apps():
    """Start all applications (scale to 1)"""
    print("🚀 Starting all applications...")

    # Start in order (database first)
    apps_order = [("postgres", 1), ("minio", 1), ("fastapi", 1), ("n8n", 1)]

    for app, replicas in apps_order:
        print(f"   Starting {app}...")
        run_command(
            f"kubectl scale deployment {app} --replicas={replicas} -n glasgow-prod"
        )

        # Wait a bit between apps
        if app == "postgres":
            print("   Waiting for database to be ready...")
            time.sleep(10)
        else:
            time.sleep(3)

    print("✅ All applications started")


def restart_app(app_name):
    """Restart a specific application"""
    print(f"🔄 Restarting {app_name}...")

    # Delete pods to force restart
    run_command(f"kubectl delete pods -n glasgow-prod -l app={app_name}")

    print(f"✅ {app_name} restarted")


def restart_all():
    """Restart all applications"""
    print("🔄 Restarting all applications...")

    # Restart in reverse order, then forward order
    apps = ["n8n", "fastapi", "minio", "postgres"]

    for app in apps:
        restart_app(app)
        time.sleep(5)

    print("✅ All applications restarted")


def force_sync_argocd():
    """Force sync all ArgoCD applications"""
    print("🔄 Force syncing all ArgoCD applications...")

    # Get all applications
    success, output, error = run_command(
        "kubectl get applications -n argocd -o name", show_output=False
    )

    if success:
        apps = output.split("\n")
        for app_line in apps:
            if app_line.strip():
                app_name = app_line.replace("application.argoproj.io/", "")
                print(f"   Syncing {app_name}...")
                run_command(
                    f'kubectl patch application {app_name} -n argocd --type merge -p=\'{{"operation":{{"initiatedBy":{{"username":"admin"}},"sync":{{"revision":"HEAD"}}}}}}\''
                )

    print("✅ All applications synced")


def reset_namespace():
    """Reset the glasgow-prod namespace (DANGER!)"""
    print("⚠️  WARNING: This will delete all data in glasgow-prod namespace!")
    confirm = input("Type 'RESET' to confirm: ")

    if confirm == "RESET":
        print("🗑️  Deleting glasgow-prod namespace...")
        run_command("kubectl delete namespace glasgow-prod")

        print("⏳ Waiting for namespace to be recreated...")
        time.sleep(10)

        print("🔄 Force syncing ArgoCD to recreate everything...")
        force_sync_argocd()

        print("✅ Namespace reset complete")
    else:
        print("❌ Reset cancelled")


def uncordon_all_nodes():
    """Uncordon all nodes to allow scheduling"""
    print("🔓 Uncordoning all nodes...")
    nodes = ["adama", "apollo", "boomer", "starbuck"]
    cmd = f"kubectl uncordon {' '.join(nodes)}"
    run_command(cmd)
    print("✅ Nodes uncordoned and ready for scheduling")


def show_status():
    """Show current cluster status"""
    print("📊 Current Cluster Status")
    print("=" * 30)

    print("\n🏠 Nodes:")
    run_command("kubectl get nodes")

    print("\n📱 Applications:")
    run_command("kubectl get applications -n argocd")

    print("\n🐳 Pods:")
    run_command("kubectl get pods -n glasgow-prod")

    print("\n💾 Storage:")
    run_command("kubectl get pvc -n glasgow-prod")

    print("\n🌐 Ingress:")
    run_command("kubectl get ingress -n glasgow-prod")


def main():
    parser = argparse.ArgumentParser(description="Glasgow GitOps Cluster Management")
    parser.add_argument(
        "action",
        choices=["stop", "start", "restart", "restart-app", "sync", "reset", "status", "uncordon"],
        help="Action to perform",
    )
    parser.add_argument("--app", help="Specific app name for restart-app")

    args = parser.parse_args()

    print("🏠 Glasgow GitOps Cluster Manager")
    print("=" * 40)

    if args.action == "stop":
        stop_all_apps()
    elif args.action == "start":
        start_all_apps()
    elif args.action == "restart":
        restart_all()
    elif args.action == "restart-app":
        if not args.app:
            print("❌ --app required for restart-app")
            sys.exit(1)
        restart_app(args.app)
    elif args.action == "sync":
        force_sync_argocd()
    elif args.action == "reset":
        reset_namespace()
    elif args.action == "status":
        show_status()
    elif args.action == "uncordon":
        uncordon_all_nodes()


if __name__ == "__main__":
    main()
