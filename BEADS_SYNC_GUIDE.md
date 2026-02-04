# Beads Cross-Repository Synchronization Guide

This document explains how to effectively sync beads between repositories in your workflow.

## Quick Summary

You now have **two synchronization patterns** configured:

1. **Sync-Branch Pattern** (already in use)
   - Beads data in `beads-sync` branch
   - Code in `main` branch
   - Agents clone and get persistent memory

2. **Multi-Repo Hydration** (newly added)
   - Central `/tmp/shared-planning` imported into `beads-testing`
   - Unified view of issues across repos
   - Shared roadmap and planning

## Sync Methods Explained

### Method 1: Sync-Branch (Single Repo, Git-Native)

**Configuration**: ✅ Already set up in `.beads/config.yaml`

```yaml
sync.branch: "beads-sync"
sync.mode: "git-branch"
```

**Workflow**:
```bash
# On any branch, work with beads
cd /Users/karl/src/beads-testing
bd create "New feature"
bd update beads-testing-xyz --status in_progress

# Export to JSONL
bd sync

# Commit locally
git add .beads/issues.jsonl
git commit -m "Update: beads-testing-xyz"

# Push to sync branch (not main)
git push origin main:beads-sync

# Main branch stays clean for code PRs
git push origin main
```

**Why this works for agents**:
- Clone with `-b beads-sync` flag
- Get full issue history
- Have persistent memory across sessions
- No need to be on main branch

### Method 2: Multi-Repo Hydration (Central Planning)

**Configuration**: ✅ Newly configured

```yaml
repos:
  primary: "."                    # This repo (beads-testing)
  additional:
    - "/tmp/shared-planning"      # Central planning repo
```

**Setup**:
```bash
# Create central planning repo
mkdir -p ~/org-planning
cd ~/org-planning
bd init
bd create "Q1 Roadmap" --type epic --priority P1
bd sync && git add .beads && git commit -m "Initial planning"

# Add to beads-testing
cd ~/beads-testing
bd repo add ~/org-planning
bd repo sync
```

**View unified issues**:
```bash
cd ~/beads-testing
bd ready --json
# Shows issues from:
# - beads-testing-* (primary)
# - org-planning-* (imported)
```

**Key feature**: Issues maintain their origin
- Write to `beads-testing-*` → saved to beads-testing repo
- Read from `org-planning-*` → pulls from org-planning repo

### Method 3: Federation (Advanced - Peer-to-Peer)

**Status**: Available, requires Dolt backend

```bash
# Start daemon with federation
bd daemon start --federation

# Add a peer
bd federation add-peer --name remote --url dolthub://team/repo

# Sync with peer
bd federation sync remote
```

**Best for**: Distributed teams, agent villages, real-time sync

## Architecture: Your Current Setup

```
┌─────────────────────────────────────────────────────┐
│ beads-testing (PRIMARY)                              │
├─────────────────────────────────────────────────────┤
│ .beads/                                              │
│  ├── issues.jsonl (6 issues)                         │
│  ├── config.yaml                                     │
│  │   ├── sync.branch: "beads-sync"                   │
│  │   └── repos: [shared-planning]                    │
│  └── beads.db (SQLite)                               │
│                                                      │
│ Branches:                                            │
│  ├── main (code + latest issues)                     │
│  └── beads-sync (issue tracking)                     │
└─────────────────────────────────────────────────────┘
         ↓ (hydrates from)
┌─────────────────────────────────────────────────────┐
│ /tmp/shared-planning (ADDITIONAL)                    │
├─────────────────────────────────────────────────────┤
│ .beads/                                              │
│  ├── issues.jsonl (1 epic)                           │
│  ├── config.yaml                                     │
│  └── beads.db                                        │
│                                                      │
│ Branches:                                            │
│  └── main (shared planning)                          │
└─────────────────────────────────────────────────────┘
```

## Sync Frequency

### Sync-Branch
- **Manual**: When you commit to beads-sync
- **Automatic** (if daemon configured): Every 5 seconds
- **On clone**: Agents get full history via git pull

### Multi-Repo
- **Manual**: `bd repo sync` (every session)
- **Cron**: Schedule daily sync
- **Pull timing**: Issues imported after sync

```bash
# Daily sync (cron job)
0 0 * * * cd ~/beads-testing && bd repo sync && git add .beads && git commit -m "Auto: repo sync" && git push

# Or manual before work
bd repo sync
bd ready --json  # See all available work
```

## Best Practices

### ✅ DO

- Run `bd doctor` regularly (catches issues)
- Keep databases under 500 issues (performance)
- Sync multi-repo daily
- Use sync-branch for git-based workflows
- Archive old issues: `bd cleanup`
- Use short prefixes: `beads-testing` not `beads-testing-project`

### ❌ DON'T

- Push beads data to main branch (defeats the purpose)
- Create epics with 100+ child tasks (use sub-epics)
- Ignore conflicts (let AI resolve them)
- Mix code commits with issue-only commits

## Agent Workflow Example

```bash
# Session 1: Explore and understand
git clone -b beads-sync https://github.com/karl82/beads-testing.git
cd beads-testing
bd ready --json
# Sees:
# - beads-testing-qac (Notification system epic)
# - shared-planning-2bj (Roadmap epic)

bd show beads-testing-qac.1
# Full context available

# Session 2: Work on task
bd update beads-testing-qac.1 --status in_progress
# Edit code...
bd close beads-testing-qac.1
bd create "discovered-issue" --parent beads-testing-qac
bd sync
git push origin main:beads-sync

# Session 3: Fresh clone, new agent
git clone -b beads-sync <url>
bd ready --json
# Sees all previous work + new discovered issues
# Continues seamlessly
```

## Troubleshooting

### Issue: "no beads database found"
```bash
# First clone?
bd init

# Corrupted database?
bd doctor --fix

# Legacy database?
bd migrate --update-repo-id
```

### Issue: Repo sync not pulling issues
```bash
# Check repos configured
bd repo list

# Force sync
bd repo sync

# Verify import
bd list --json | grep 'shared-planning'
```

### Issue: Conflicts in JSONL merge
```bash
# Let AI handle it
git status  # Shows conflict
bd resolve-conflicts  # Uses AI to fix

# Or manual
git checkout --theirs .beads/issues.jsonl
bd sync  # Re-import
```

## Next Steps

### 1. Test multi-repo sync
```bash
cd ~/beads-testing
bd repo sync
bd list --json | wc -l  # Should show 7+ issues
```

### 2. Add more repos as needed
```bash
mkdir ~/backend
cd ~/backend && bd init
cd ~/beads-testing && bd repo add ~/backend && bd repo sync
```

### 3. Set up daily sync (optional)
```bash
# Add to crontab
0 0 * * * cd ~/beads-testing && bd repo sync
```

### 4. Try federation (advanced)
```bash
bd daemon start --federation
bd federation add-peer --url dolthub://team/beads
```

## References

- [Beads GitHub](https://github.com/steveyegge/beads)
- [Multi-repo configuration](https://github.com/steveyegge/beads#multi-repo)
- [Federation docs](https://github.com/steveyegge/beads#federation)
- [Best practices](https://steve-yegge.medium.com/beads-best-practices-2db636b9760c)

---

Last updated: 2026-02-03
Configuration verified: ✅ Sync-branch + Multi-repo
