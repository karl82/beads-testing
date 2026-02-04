#!/usr/bin/env python3
"""
Push Beads issues to JIRA.

Usage:
    python push_to_jira.py --issue beads-testing-641
    python push_to_jira.py --all
"""

import json
import sys
import base64
import subprocess
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pathlib import Path
import argparse


def get_bd_config(key: str) -> str:
    """Get a value from bd config."""
    try:
        result = subprocess.run(
            ["bd", "config", "get", key],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def load_issues():
    """Load issues from .beads/issues.jsonl."""
    issues_file = Path(".beads/issues.jsonl")
    if not issues_file.exists():
        print("Error: .beads/issues.jsonl not found")
        sys.exit(1)
    
    issues = []
    with open(issues_file, 'r') as f:
        for line in f:
            if line.strip():
                issues.append(json.loads(line))
    return issues


def create_jira_issue(jira_url: str, project: str, username: str, api_token: str, issue: dict) -> dict:
    """Create an issue in JIRA using REST API."""
    
    # Map priority: P1/1 -> 1 (Highest), P2/2 -> 3 (Medium), P3/3 -> 5 (Lowest)
    priority_map = {1: 1, 2: 3, 3: 5, "P1": 1, "P2": 3, "P3": 5}
    priority_id = priority_map.get(issue.get("priority"), 3)
    
    # Map issue type
    issue_type_map = {
        "epic": "Epic",
        "task": "Task",
        "story": "Story",
        "bug": "Bug",
        "subtask": "Sub-task"
    }
    issue_type = issue_type_map.get(issue.get("issue_type", "task"), "Task")
    
    # Build JIRA issue
    jira_issue = {
        "fields": {
            "project": {"key": project},
            "summary": issue.get("title", ""),
            "description": issue.get("description", ""),
            "issuetype": {"name": issue_type},
            "priority": {"id": str(priority_id)},
        }
    }
    
    # Prepare auth
    auth_str = base64.b64encode(f"{username}:{api_token}".encode()).decode()
    
    # Create request (try both API v3 and v2)
    url = f"{jira_url.rstrip('/')}/rest/api/2/issues"
    req = Request(
        url,
        data=json.dumps(jira_issue).encode(),
        headers={
            "Authorization": f"Basic {auth_str}",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    
    try:
        with urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result
    except HTTPError as e:
        error_msg = e.read().decode()
        print(f"Error creating issue in JIRA: {e.status} {error_msg}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Push Beads issues to JIRA")
    parser.add_argument("--issue", help="Specific issue ID to push")
    parser.add_argument("--all", action="store_true", help="Push all local-only issues")
    args = parser.parse_args()
    
    # Get JIRA config
    jira_url = get_bd_config("jira.url")
    project = get_bd_config("jira.project")
    username = get_bd_config("jira.username")
    api_token = get_bd_config("jira.api_token")
    
    if not all([jira_url, project, username, api_token]):
        print("Error: JIRA not fully configured")
        print("Set: jira.url, jira.project, jira.username, jira.api_token")
        sys.exit(1)
    
    # Load issues
    issues = load_issues()
    
    # Filter issues to push
    if args.issue:
        issues_to_push = [i for i in issues if i.get("id") == args.issue]
        if not issues_to_push:
            print(f"Error: Issue {args.issue} not found")
            sys.exit(1)
    elif args.all:
        # Push all local issues (not from JIRA)
        issues_to_push = [i for i in issues if not i.get("external_ref")]
    else:
        print("Use --issue <id> or --all")
        sys.exit(1)
    
    # Push each issue
    for issue in issues_to_push:
        print(f"Pushing {issue.get('id')}: {issue.get('title')}...")
        try:
            result = create_jira_issue(jira_url, project, username, api_token, issue)
            jira_key = result.get("key")
            print(f"✓ Created JIRA issue: {jira_key}")
            print(f"  URL: {jira_url}/browse/{jira_key}")
        except Exception as e:
            print(f"✗ Failed to push {issue.get('id')}: {e}")
            sys.exit(1)
    
    print("\n✓ Push complete!")


if __name__ == "__main__":
    main()
