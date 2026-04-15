---
name: ps:pr-create
description: Create a GitHub PR using the team's standard format — FEAT/FIX prefix, GRAP ticket in title, Jira link + bullet-point description, no co-author. Use when the user runs /ps:pr-create <base-branch> [jira-ticket] or asks to create a PR.
argument-hint: <base-branch> [jira-ticket]
allowed-tools: [Bash]
---

# PR Creator

The user wants to create a GitHub pull request following the team's standard format.

**Arguments:** $ARGUMENTS

Parse arguments:
- `base-branch` — target branch (e.g. `release/6.1`, `main`). Required.
- `jira-ticket` — Jira ticket ID (e.g. `GRAP-18762`). Optional — try to detect from current branch name if not provided.

---

## Step 1 — Gather context

Run these in parallel:

```bash
# Current branch
git branch --show-current

# Commits ahead of base branch
git log <base-branch>..<current-branch> --oneline

# Short diff stat
git diff <base-branch>..HEAD --stat
```

---

## Step 2 — Detect Jira ticket

If `jira-ticket` was not passed as argument, extract it from the branch name:
- Branch `feature/GRAP-18762` → ticket `GRAP-18762`
- Branch `fix/GRAP-18762-something` → ticket `GRAP-18762`
- If no ticket found, leave blank and skip Jira link in description.

---

## Step 3 — Determine PR prefix

- Use `FEAT:` for feature branches (`feature/`, `enhance/`)
- Use `FIX:` for fix branches (`fix/`, `hotfix/`)
- Default to `FEAT:` if unclear

---

## Step 4 — Compose title and description

**Title format:**
```
<PREFIX>: <JIRA-TICKET> <concise summary of changes>
```
Example: `FEAT: GRAP-18762 Improve UI and fix data issues in Other loans/Debt obligations`

**Description format:**
```
## Summary

https://grapplefinance.atlassian.net/browse/<JIRA-TICKET>    ← omit if no ticket

- <short bullet 1>
- <short bullet 2>
- <short bullet 3>
...
```

Rules:
- Keep each bullet short and high-level — one line max, no details
- Group related commits into a single bullet, don't list every commit separately
- Aim for 3–5 bullets total regardless of how many commits there are
- Use plain language, no markdown headers inside bullets
- Do NOT add any co-author or "Generated with" lines

---

## Step 5 — Push branch if needed

Check if the current branch has a remote tracking branch:

```bash
git status -sb
```

If `## <branch>...origin/<branch>` is missing, push first:

```bash
git push origin <current-branch>
```

---

## Step 6 — Create the PR

```bash
gh pr create \
  --base <base-branch> \
  --head <current-branch> \
  --title "<TITLE>" \
  --body "<DESCRIPTION>"
```

Pass body via `"$(cat <<'EOF' ... EOF)"` to preserve newlines correctly.

---

## Step 7 — Output

Print the PR URL returned by `gh pr create`. Done.
