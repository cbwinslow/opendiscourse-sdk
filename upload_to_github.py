#!/usr/bin/env python3
"""
OpenDiscourse GitHub Upload Helper

This script helps upload the analysis suite to GitHub and GitLab.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description=""):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False


def check_git_status():
    """Check current git status"""
    print("Checking git status...")
    run_command("git status", "Check git status")


def add_files_to_git():
    """Add all files to git"""
    print("Adding files to git...")
    run_command("git add .", "Add all files to git")


def create_initial_commit():
    """Create initial commit"""
    print("Creating initial commit...")
    run_command(
        'git commit -m "Initial commit: Complete OpenDiscourse analysis suite with political bias detection, content safety analysis, and semantic similarity analysis"',
        "Initial commit",
    )


def push_to_github():
    """Push to GitHub"""
    print("Pushing to GitHub...")
    success = run_command("git push origin main", "Push to GitHub")
    if success:
        print("✅ Successfully pushed to GitHub!")
    else:
        print("❌ Failed to push to GitHub")

    return success


def push_to_gitlab():
    """Push to GitLab"""
    print("Pushing to GitLab...")
    success = run_command("git push origin main", "Push to GitLab")
    if success:
        print("✅ Successfully pushed to GitLab!")
    else:
        print("❌ Failed to push to GitLab")

    return success


def create_github_repo():
    """Create GitHub repository"""
    repo_name = "opendiscourse-analysis"

    print(f"Creating GitHub repository: {repo_name}")

    # Check if repo already exists
    result = run_command(f"gh repo view {repo_name}", "Check if repo exists")

    if "not found" in result.stdout.lower():
        print(f"✅ Created new repository: {repo_name}")
        run_command(
            f"gh repo create {repo_name} --public --description 'OpenDiscourse Analysis Suite - Political bias detection, content safety analysis, and semantic similarity analysis'",
            "Create GitHub repo",
        )
    else:
        print(f"ℹ Repository already exists: {repo_name}")

    return repo_name


def setup_remote():
    """Setup remote origin"""
    print("Setting up remote origin...")

    # Try GitHub first
    github_url = run_command(
        "gh repo view opendiscourse-analysis --json",
        "Get GitHub repo URL",
        capture_output=True,
    ).stdout.strip()

    if github_url and "not found" not in github_url.lower():
        print("✅ Found GitHub repository")
        run_command("git remote add origin " + github_url, "Add GitHub remote")
        return "github"

    # Try GitLab
    print("ℹ GitHub repository not found, trying GitLab...")
    gitlab_url = "https://gitlab.com/cbwinslow/opendiscourse-analysis"

    run_command("git remote add origin " + gitlab_url, "Add GitLab remote")
    return "gitlab"


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Upload OpenDiscourse analysis to GitHub/GitLab"
    )
    parser.add_argument("--github", action="store_true", help="Upload to GitHub")
    parser.add_argument("--gitlab", action="store_true", help="Upload to GitLab")
    parser.add_argument(
        "--both", action="store_true", help="Upload to both GitHub and GitLab"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no actual upload)"
    )

    args = parser.parse_args()

    print("🚀 OpenDiscourse GitHub Upload Helper")
    print("=" * 50)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual uploads will be performed")
        return

    # Check git status
    check_git_status()

    # Add files to git
    if not add_files_to_git():
        print("❌ Failed to add files to git")
        return

    # Create initial commit if needed
    result = run_command("git log --oneline -1", "Check if initial commit needed")
    if "no commits yet" in result.stdout:
        if not create_initial_commit():
            print("❌ Failed to create initial commit")
            return

    # Setup remote if needed
    remote = setup_remote()

    # Upload based on arguments
    if args.github or args.both:
        if remote == "github" or args.both:
            success = push_to_github()
        elif remote == "gitlab" or args.both:
            success = push_to_gitlab()
        else:
            print("❌ No remote configured")
            return

    if success:
        print("🎉 Upload completed successfully!")
        print(
            f"📍 Repository URL: {run_command('gh repo view opendiscourse-analysis --json', 'Get repo URL', capture_output=True).stdout.strip()}"
        )
    else:
        print("❌ Upload failed")


if __name__ == "__main__":
    main()
