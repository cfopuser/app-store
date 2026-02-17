## File: run.py
#!/usr/bin/env python3
"""
Orchestrator for the modular APK patching framework.

Usage:
    python run.py                           # Process all registered apps
    python run.py --app bit                 # Process only the 'bit' app
    python run.py --app bit --step download # Only run the download step
    python run.py --list                    # List all registered apps
"""

import argparse
import json
import sys

from core.utils import (
    discover_apps,
    generate_apps_listing,
    load_app_config,
    run_apk_mitm,
    set_github_output,
    update_status,
    update_version,
)
from core.downloader import download_app
from core.patcher import run_patch


def process_app(app_id: str, step: str = "all", no_mitm: bool = False) -> bool:
    """
    Run the pipeline for a single app.

    Args:
        app_id: The app identifier (subfolder name under apps/).
        step: Which step to run — 'download', 'patch', or 'all'.

    Returns:
        True if the step(s) completed successfully.
    """
    print(f"\n{'='*60}")
    print(f"  Processing app: {app_id}")
    print(f"{'='*60}\n")

    try:
        config = load_app_config(app_id)
    except FileNotFoundError as e:
        print(f"[-] {e}")
        return False

    # Variables to track version state
    new_version = None
    update_needed = False

    # --- Download step ---
    output_filename = f"{app_id}_latest.apk"
    if step in ("download", "all"):
        update_needed, new_version = download_app(config, output_filename=output_filename)
        set_github_output("update_needed", str(update_needed).lower())

        if new_version:
            set_github_output("new_version", new_version)

        if not update_needed:
            print(f"[i] [{app_id}] No update needed. Done.")
            return True

        if not no_mitm and not config.get("skip_mitm", False):
            # Run MITM and check success
            mitm_success = run_apk_mitm(output_filename)
            if not mitm_success:
                print(f"[-] [{app_id}] apk-mitm failed. Aborting to prevent bad patch.")
                return False

        if step == "download":
            return True

    # --- Patch step ---
    if step in ("patch", "all"):
        # In CI the decompiled directory is always "build_output"
        decompiled_dir = "build_output"
        success = run_patch(app_id, decompiled_dir)

        if not success:
            update_status(
                config["status_file"],
                success=False,
                failed_version=new_version if (step == "all" and new_version) else "unknown",
                error_message="Patching failed",
            )
            print(f"[-] [{app_id}] Patching failed!")
            return False

        # If we are here, patch was successful.
        update_status(config["status_file"], success=True)
        
        # If running locally in 'all' mode, update the version file now.
        # In CI, this is handled by the workflow file after the APK is signed.
        if step == "all" and update_needed and new_version:
            print(f"[+] [{app_id}] Updating version file to {new_version}")
            update_version(config["version_file"], new_version)
            
        print(f"[+] [{app_id}] Pipeline completed successfully!")
        return True

    return True


def list_apps():
    """Print all registered apps and their metadata."""
    app_ids = discover_apps()
    if not app_ids:
        print("No apps registered. Add an app by creating apps/<name>/app.json")
        return

    print(f"\n{'='*50}")
    print(f"  Registered Apps ({len(app_ids)})")
    print(f"{'='*50}\n")

    for app_id in app_ids:
        try:
            config = load_app_config(app_id)
            print(f"  [{app_id}]")
            print(f"    Name:    {config.get('name', 'N/A')}")
            print(f"    Package: {config.get('package_name', 'N/A')}")
            print(f"    Source:  {config.get('source', 'N/A')}")
            print(f"    Maintainer: {config.get('maintainer', 'N/A')}")
            print()
        except Exception as e:
            print(f"  [{app_id}] Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Modular APK Patching Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                           Process all apps
  python run.py --app bit                 Process only 'bit'
  python run.py --app bit --step download Only download
  python run.py --list                    List registered apps
        """,
    )
    parser.add_argument(
        "--app",
        help="Process only this app ID (default: all apps)",
    )
    parser.add_argument(
        "--step",
        choices=["download", "patch", "all"],
        default="all",
        help="Which pipeline step to run (default: all)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered apps and exit",
    )
    parser.add_argument(
        "--update-listing",
        action="store_true",
        help="Regenerate apps.json and exit",
    )
    parser.add_argument(
        "--no-mitm",
        action="store_true",
        help="Skip running apk-mitm on the downloaded APK",
    )

    args = parser.parse_args()

    if args.list:
        list_apps()
        return

    if args.update_listing:
        generate_apps_listing()
        return

    # Determine which apps to process
    if args.app:
        app_ids = [args.app]
    else:
        app_ids = discover_apps()
        if not app_ids:
            print("[-] No apps found under apps/. Nothing to do.")
            sys.exit(1)

    # Process each app
    results = {}
    for app_id in app_ids:
        success = process_app(app_id, step=args.step, no_mitm=args.no_mitm)
        results[app_id] = success

    # Summary
    print(f"\n{'='*50}")
    print("  Summary")
    print(f"{'='*50}")
    for app_id, success in results.items():
        status = "✓ OK" if success else "✗ FAILED"
        print(f"  {app_id}: {status}")
    print()

    # Set overall output for CI
    all_ok = all(results.values())
    set_github_output("all_success", str(all_ok).lower())

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()