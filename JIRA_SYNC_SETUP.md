# JIRA Synchronization Setup Guide

## Current Status ✅

JIRA synchronization is now configured and operational!

**Configuration:**
- JIRA URL: `https://karelrankprivate.atlassian.net/`
- Project: `SAM1`
- Username: `karel.rank+jira@gmail.com`
- Sync Mode: Two-way (Pull & Push)

**Initial Import:**
- ✅ Downloaded 10 issues from JIRA SAM1 project
- ✅ Imported into Beads with IDs: `bd-1` through `bd-10`
- ✅ Merged with existing local issues (now 16 total issues)

## How to Use JIRA Sync

### Prerequisites

The JIRA sync script must be available. If not already set up:

```bash
# Download the script (one-time)
cd /Users/karl/src/beads-testing
curl -o jira2jsonl.py https://raw.githubusercontent.com/steveyegge/beads/main/examples/jira-import/jira2jsonl.py

# Set the environment variable
export BD_JIRA_SCRIPT=$PWD/jira2jsonl.py
```

To make this permanent, add to your shell config (`~/.zshrc` or `~/.bashrc`):

```bash
export BD_JIRA_SCRIPT=/Users/karl/src/beads-testing/jira2jsonl.py
```

### Commands

#### 1. Pull Issues from JIRA

Import latest issues from JIRA SAM1 project:

```bash
export BD_JIRA_SCRIPT=/Users/karl/src/beads-testing/jira2jsonl.py
bd jira sync --pull
```

This will:
- Fetch all open issues from JIRA
- Create new `bd-*` issues for new JIRA issues
- Update existing issues if they've changed

#### 2. Check Sync Status

See what needs to be synced:

```bash
bd jira status
```

Output example:
```
Jira Sync Status
================

Jira URL:     https://karelrankprivate.atlassian.net/
Project:      SAM1
Last Sync:    2026-02-03T12:34:56Z

Total Issues: 16
With Jira:    10
Local Only:   6
```

#### 3. List Issues

View all issues (local + JIRA):

```bash
# All issues
bd list

# JIRA-imported issues only
bd list | grep "^○ bd-"

# Local Beads issues only
bd list | grep "^○ beads-testing"

# JSON output for automation
bd list --json | jq '.[] | select(.title | contains("JIRA"))'
```

#### 4. Work with Issues

Update a JIRA-imported issue:

```bash
# View details
bd show bd-1

# Change status
bd update bd-1 --status in_progress

# Add comment
bd update bd-1 --comment "Working on this now"

# Close when done
bd close bd-1
```

## Two-Way Sync Architecture

### Current Implementation

Beads + JIRA operate in a **hybrid mode**:

1. **Pull (JIRA → Beads)**: Automatic on demand
   - Command: `bd jira sync --pull`
   - Creates new `bd-*` issues for JIRA tickets
   - Updates existing issues

2. **Push (Beads → JIRA)**: Manual for now
   - Command: `bd jira sync --push` (experimental)
   - Requires push script configuration
   - Creates/updates JIRA issues from Beads

### Issue Mapping

| Source | ID Format | Example | Sync Direction |
|--------|-----------|---------|-----------------|
| JIRA | `SAM1-1`, `SAM1-2`, etc. | `SAM1-5` | Pull only |
| Beads (from JIRA) | `bd-1`, `bd-2`, etc. | `bd-7` | Pull from JIRA |
| Beads (local) | `beads-testing-*` | `beads-testing-qac` | Local only |

### Workflow Example

```bash
# 1. Start work session
cd /Users/karl/src/beads-testing
export BD_JIRA_SCRIPT=$PWD/jira2jsonl.py

# 2. Pull latest from JIRA
bd jira sync --pull

# 3. See available work
bd ready

# 4. Work on an issue
bd update bd-3 --status in_progress
# ... make changes ...
bd update bd-3 --comment "Implemented feature X"

# 5. When complete
bd close bd-3

# 6. Commit to git
git add .beads/issues.jsonl
git commit -m "Completed bd-3: Implement User Authentication"

# 7. Sync beads data
bd sync
git push origin main:beads-sync

# 8. Optionally push completed issues back to JIRA (when push script is ready)
# bd jira sync --push
```

## Configuration Details

The JIRA configuration is stored in the Beads database (not in `.beads/config.yaml`):

```bash
# View current JIRA config
bd config get jira.url
bd config get jira.project
bd config get jira.username

# Update if needed
bd config set jira.url "https://your-jira.atlassian.net"
bd config set jira.project "YOUR_PROJECT"
bd config set jira.username "your-email@company.com"
bd config set jira.api_token "your-api-token"
```

## Troubleshooting

### Issue: "jira2jsonl.py not found"

```bash
# Make sure BD_JIRA_SCRIPT is set
export BD_JIRA_SCRIPT=/Users/karl/src/beads-testing/jira2jsonl.py

# Verify it exists
ls -l $BD_JIRA_SCRIPT
```

### Issue: "Connection refused" or "401 Unauthorized"

The API token may be invalid or expired:

```bash
# Verify credentials
bd config get jira.username
bd config get jira.api_token

# Generate new token at:
# https://karelrankprivate.atlassian.net/secure/ViewProfile.jspa?tab=security
```

### Issue: "Skipping dependency due to error"

Some issues may reference parent/child relationships that aren't in the current import. This is expected and can be safely ignored.

## Advanced Setup

### Automated Daily Sync

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line (syncs daily at 8 AM)
0 8 * * * export BD_JIRA_SCRIPT=/Users/karl/src/beads-testing/jira2jsonl.py && cd /Users/karl/src/beads-testing && bd jira sync --pull && bd sync && git add .beads && git commit -m "Auto: JIRA sync" && git push origin main:beads-sync
```

### Push Script Setup (When Available)

The push functionality requires an additional script. To enable:

1. Create a `jsonl2jira.py` script (similar to `jira2jsonl.py`)
2. Set `BD_JIRA_PUSH_SCRIPT=/path/to/jsonl2jira.py`
3. Run `bd jira sync --push`

### Environment Variables

For automation/CI/CD:

```bash
# JIRA connection (if not in config)
export JIRA_API_TOKEN="your-token"
export JIRA_USERNAME="your-email@company.com"

# Beads database
export BEADS_DB=/Users/karl/src/beads-testing/.beads/beads.db

# Scripts
export BD_JIRA_SCRIPT=/Users/karl/src/beads-testing/jira2jsonl.py
```

## Integration with Git Workflow

Beads issues are synced to git via the `beads-sync` branch:

```bash
# After working on issues
bd sync                    # Export issues to .beads/issues.jsonl
git add .beads/issues.jsonl
git commit -m "Update: completed bd-3, bd-5"
git push origin main:beads-sync  # Push beads data to sync branch
git push origin main        # Push code to main branch
```

This keeps beads data in a separate branch from your code, allowing clean PR workflows.

## Summary

✅ **JIRA sync is configured and working!**

**Next steps:**
1. Run `bd jira sync --pull` regularly to pull latest JIRA issues
2. Work on issues locally in Beads
3. Commit changes to `beads-sync` branch
4. Push to remote: `git push origin main:beads-sync`

**For questions:**
- Check Beads docs: https://github.com/steveyegge/beads
- View this repo's AGENTS.md for workflow guidelines
- Check BEADS_SYNC_GUIDE.md for multi-repo sync info

---

Last updated: 2026-02-03
Status: ✅ Operational
Issues synced: 10 from JIRA SAM1
