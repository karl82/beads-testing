# JIRA Filtering and Large-Scale Sync Guide

## 1. JIRA Filtering Capabilities

### Yes, You Can Filter JIRA Issues!

The Beads JIRA sync script supports **JQL (JIRA Query Language)** filtering, which is JIRA's powerful query syntax.

### Filtering Methods

#### Method 1: By Project (Default)
```bash
# Sync only SAM1 project
python3 jira2jsonl.py --from-config
# Equivalent to: --jql "project=SAM1"
```

#### Method 2: By Status
```bash
# Only open issues
python3 jira2jsonl.py --from-config --state open

# Only closed issues
python3 jira2jsonl.py --from-config --state closed

# All issues
python3 jira2jsonl.py --from-config --state all
```

#### Method 3: Custom JQL Query
```bash
# Advanced filtering with JQL
export BD_JIRA_SCRIPT=/Users/karl/src/beads-testing/jira2jsonl.py

# Only high priority issues
python3 jira2jsonl.py --from-config --jql "project=SAM1 AND priority=Highest"

# Recent issues (last 30 days)
python3 jira2jsonl.py --from-config --jql "project=SAM1 AND updated >= -30d"

# Open epics only
python3 jira2jsonl.py --from-config --jql "project=SAM1 AND type=Epic AND status!=Done"

# Assigned to specific person
python3 jira2jsonl.py --from-config --jql "assignee=karel.rank+jira@gmail.com"

# Combination: Open analytics dashboard work
python3 jira2jsonl.py --from-config --jql "project=SAM1 AND parent=SAM1-11 AND status!=Done"
```

### Common JQL Examples

| Use Case | JQL Query |
|----------|-----------|
| Open issues only | `project=SAM1 AND status!=Done AND status!=Closed` |
| High priority | `project=SAM1 AND priority IN (Highest, High)` |
| Epics only | `project=SAM1 AND type=Epic` |
| Tasks in epic | `parent=SAM1-11` |
| Last 7 days | `project=SAM1 AND updated >= -7d` |
| My issues | `project=SAM1 AND assignee=currentUser()` |
| Has label | `project=SAM1 AND labels=analytics` |
| No assignee | `project=SAM1 AND assignee=EMPTY` |
| Multiple projects | `project IN (SAM1, SAM2, SAM3)` |
| Complex filter | `project=SAM1 AND (priority=Highest OR labels=critical) AND status!=Done` |

---

## 2. Handling 100K+ JIRA Issues

### What Happens with Large-Scale Syncs?

#### Current Behavior (jira2jsonl.py)

1. **Pagination**: Script fetches 100 issues at a time (default `maxResults=100`)
2. **Progress Reporting**: Shows `Fetched X/TOTAL issues...` for each batch
3. **Memory Loading**: All issues loaded into memory before converting to JSONL
4. **Database Import**: Beads database imports and deduplicates issues

#### Performance Metrics

```
Estimated Times (100K issues):
- Fetch from JIRA API:  ~5-10 minutes (1000 batches × 100 issues)
- Memory usage:         ~500MB-1GB (depends on issue size)
- JSONL export:         ~1-2 minutes
- Beads import:         ~2-5 minutes
- Total time:           ~10-20 minutes

Network Considerations:
- API calls: ~1000 requests for 100K issues
- Rate limits: Check JIRA Cloud rate limits (typically 8 req/sec)
- Bandwidth: ~100-200MB depending on issue details
```

### Strategies for Handling Large Syncs

#### Strategy 1: Incremental Filtering (Recommended)
Instead of syncing all 100K at once, sync incrementally:

```bash
#!/bin/bash
# sync_jira_filtered.sh

SCRIPT="/Users/karl/src/beads-testing/jira2jsonl.py"

# Month 1: Current month
python3 $SCRIPT --from-config --jql "updated >= -30d" | bd import

# Critical issues: High priority
python3 $SCRIPT --from-config --jql "priority=Highest" | bd import

# Active work: Epics and their tasks
python3 $SCRIPT --from-config --jql "type=Epic OR type=Task" | bd import

# Specific team: Assigned to team members
python3 $SCRIPT --from-config --jql "assignee IN (user1@company.com, user2@company.com)" | bd import
```

#### Strategy 2: Project-Based Filtering
If you have multiple JIRA projects, sync them separately:

```bash
# Sync project by project
for PROJECT in SAM1 SAM2 SAM3 SAM4; do
  echo "Syncing $PROJECT..."
  python3 jira2jsonl.py --from-config --jql "project=$PROJECT" | bd import
done
```

#### Strategy 3: Date-Based Rolling Sync
Keep only recent issues:

```bash
# Sync only last 6 months
python3 jira2jsonl.py --from-config --jql "updated >= -180d"

# Or combine with status
python3 jira2jsonl.py --from-config --jql "updated >= -180d OR status IN (Open, In Progress)"
```

#### Strategy 4: Selective Type Filtering
Focus on actionable work:

```bash
# Only tasks and subtasks (skip larger epics initially)
python3 jira2jsonl.py --from-config --jql "type IN (Task, Subtask) AND status!=Done"

# Or only epics for planning
python3 jira2jsonl.py --from-config --jql "type=Epic AND status!=Done"
```

---

## 3. Beads Database Handling

### How Beads Manages Large Issue Counts

#### Deduplication
- Beads automatically deduplicates based on external_ref
- Multiple syncs won't create duplicate issues
- Safe to re-sync the same query

#### Database Performance
- **Recommended limit**: <500 issues per database instance
- **Hard limit**: No technical limit, but UI becomes slower
- **Best practice**: Archive old issues regularly

```bash
# Check issue count
bd list | wc -l

# Archive old/closed issues
bd cleanup --before 2025-01-01 --status closed

# View archived issues
bd list --archived
```

#### Memory Management
```bash
# Rebuild database if slow
bd doctor --fix

# Check database size
ls -lh .beads/beads.db

# Export and reimport (clean slate)
bd export > backup.jsonl
rm .beads/beads.db
bd import < backup.jsonl
```

---

## 4. Production Recommendations

### For 100K+ Issue Syncs

1. **Start Filtered** ✅
   ```bash
   # Don't sync everything at once!
   # Start with recent/critical issues
   python3 jira2jsonl.py --from-config \
     --jql "updated >= -90d AND status!=Done"
   ```

2. **Use Date Ranges** ✅
   ```bash
   # Quarterly sync approach
   Q1=$(python3 -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))")
   python3 jira2jsonl.py --from-config --jql "updated >= $Q1"
   ```

3. **Separate by Team/Project** ✅
   ```bash
   # Each team maintains their own beads instance
   # Team A: bd init (instance 1)
   # Team B: bd init (instance 2)
   # Sync only their project to their instance
   ```

4. **Periodic Cleanup** ✅
   ```bash
   # Monthly archive of completed work
   bd cleanup --before $(date -d '30 days ago' +%Y-%m-%d) --status Done
   ```

5. **Use Multi-Repo Feature** ✅
   ```bash
   # Create different repos for different concerns
   # Central repo: All open issues across projects
   # Team repo: Team-specific issues only
   # Archive repo: Completed work (read-only)
   ```

---

## 5. Practical Example: 100K JIRA Sync Plan

### Phased Approach for Large Organization

```mermaid
Phase 1 (Week 1):     Phase 2 (Week 2):     Phase 3 (Ongoing):
├─ Current work      ├─ Historical data    ├─ Daily incremental
├─ Open issues       ├─ Completed work     ├─ Recent changes
├─ Active projects   └─ Archive setup      └─ Maintenance
└─ ~10K issues          ~50K issues           ~100K total
```

#### Phase 1: Critical Path (10K issues)
```bash
# Week 1: Import current work only
python3 jira2jsonl.py --from-config \
  --jql "status IN (Open, 'In Progress', 'Ready for Review') AND updated >= -90d" | \
  bd import
```

#### Phase 2: Historical (50K issues)
```bash
# Week 2: Add historical completed work to separate repo
mkdir ~/beads-archive
cd ~/beads-archive
bd init

python3 ../jira2jsonl.py --from-config \
  --jql "status IN (Done, Closed) AND updated >= -365d" | \
  bd import
```

#### Phase 3: Full Sync (100K issues)
```bash
# Ongoing: Set up automated filtering
# Main repo: Recent + open (keep < 20K)
# Archive repo: Completed work (read-only, ~80K)
# Meta repo: All issues, statistics only

# Daily sync (only changes)
0 2 * * * ~/sync_jira_daily.sh
```

---

## 6. Performance Tips

### Optimize Pagination
```python
# In jira2jsonl.py, you can adjust max_results
# Default: 100 (good balance)
# Reduce for slow networks: 50
# Increase if stable: 250
max_results = 100  # Line 439 in jira2jsonl.py
```

### Use Selective Fields
```bash
# If performance is slow, limit fields
# Modify jira2jsonl.py line 446:
# fields=*all  →  fields=summary,description,status,priority
```

### Cache Recently Synced Data
```bash
# Store JQL queries for common filters
cat > ~/.jira_queries.sh << 'EOF'
export JIRA_CURRENT="updated >= -30d AND status!=Done"
export JIRA_CRITICAL="priority IN (Highest, High)"
export JIRA_TEAM="assignee IN (user1, user2, user3)"
EOF

# Use in sync scripts
source ~/.jira_queries.sh
python3 jira2jsonl.py --from-config --jql "$JIRA_CURRENT"
```

---

## 7. Testing Your Filtering

### Test Query Before Full Sync
```bash
# Count how many issues match your filter
python3 jira2jsonl.py --from-config \
  --jql "project=SAM1 AND priority=Highest" | \
  wc -l

# Estimate sync time
ISSUE_COUNT=$(...)  # From above
BATCHES=$((ISSUE_COUNT / 100 + 1))
echo "Will need ~$BATCHES API calls (~$((BATCHES / 8)) seconds)"
```

### Dry Run with Sample
```bash
# Test with just a few issues
# Modify jira2jsonl.py temporarily:
# Add: if len(all_issues) >= 10: break  # (line 472)

python3 jira2jsonl.py --from-config --jql "your query" | head -10
```

---

## 8. Summary: Best Practices for 100K+ Issues

| Scenario | Recommendation |
|----------|-----------------|
| **New org sync** | Start with `status!=Done` filter, ~10-50K |
| **Team onboarding** | Single project or team filter, ~1-5K |
| **Large organization** | Use multi-repo: work + archive + stats |
| **Continuous sync** | Daily incremental with `updated >= -1d` |
| **Historical data** | Separate read-only archive repository |
| **Migration project** | Phase approach: current → historical → full |

### Command Reference: Smart Filtering

```bash
# Recent + open
python3 jira2jsonl.py --from-config --jql "status!=Done AND updated>=-30d"

# My team's work
python3 jira2jsonl.py --from-config --jql "assignee IN (team@example.com, members) AND status!=Done"

# Active epics
python3 jira2jsonl.py --from-config --jql "type=Epic AND status!=Done"

# Critical + high
python3 jira2jsonl.py --from-config --jql "priority IN (Highest, High)"

# Latest changes
python3 jira2jsonl.py --from-config --jql "updated >= -7d"

# Avoid too many at once!
# ✅ Good: 5K-50K issues per sync
# ❌ Bad: 100K all at once
```

---

**Last Updated**: 2026-02-04  
**Script**: jira2jsonl.py (supports full JQL filtering)  
**Status**: ✅ Filtering Fully Supported
