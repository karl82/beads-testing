# JIRA Sync - Quick Start

## Setup (One Time)

```bash
# 1. Set environment variable (add to ~/.zshrc or ~/.bashrc)
export BD_JIRA_SCRIPT=/Users/karl/src/beads-testing/jira2jsonl.py

# 2. Verify
echo $BD_JIRA_SCRIPT
```

## Daily Workflow

```bash
# 1. Start work session
cd /Users/karl/src/beads-testing
export BD_JIRA_SCRIPT=/Users/karl/src/beads-testing/jira2jsonl.py

# 2. Pull latest from JIRA
bd jira sync --pull

# 3. See what needs work
bd ready

# 4. Pick an issue and work on it
bd update bd-3 --status in_progress

# 5. When done
bd close bd-3

# 6. Commit to git
git add .beads/issues.jsonl
git commit -m "Completed bd-3"
git push origin main:beads-sync
```

## Common Commands

| Command | What it does |
|---------|-------------|
| `bd jira status` | Show sync status |
| `bd jira sync --pull` | Import JIRA issues into Beads |
| `bd list` | List all issues (local + JIRA) |
| `bd show bd-1` | View JIRA issue details |
| `bd ready` | Show issues ready to work on |
| `bd update bd-1 --status in_progress` | Start working on issue |
| `bd close bd-1` | Mark issue complete |

## Current Status

- ✅ JIRA URL: https://karelrankprivate.atlassian.net/
- ✅ Project: SAM1
- ✅ Issues synced: 10 from JIRA, 7 local
- ✅ Last sync: 2026-02-03 21:47:41

## Files Reference

- **JIRA_SYNC_SETUP.md** - Full setup guide
- **BEADS_SYNC_GUIDE.md** - Multi-repo sync configuration
- **AGENTS.md** - Team workflow guidelines

---

For full details, see `JIRA_SYNC_SETUP.md`
