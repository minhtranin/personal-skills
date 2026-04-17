---
name: ps:jira-plantask
description: Given a Jira issue key, research the codebase, produce an implementation plan aligned to existing patterns, break it into independent subtasks, create them in Jira, then guide implementation step by step. Use when the user runs /ps-jira-plantask <ISSUE-KEY>.
argument-hint: <PROJ-123> [--no-create] [--refresh]
allowed-tools: [Bash, Read, Write, Agent]
---

# Jira Plan & Task Creator

**Arguments:** $ARGUMENTS

Parse the issue key from arguments. Accept `PROJ-123` or a full Jira URL.
- `--no-create` — produce the plan but skip creating subtasks in Jira
- `--refresh`   — re-fetch from Jira even if cached

---

## Step 0 — Bootstrap scripts if missing

```bash
ls "$HOME/.local/share/personal-skills/scripts/jira/fetch_jira.py" 2>/dev/null || \
  curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

---

## Step 1 — Check credentials

```bash
bash "$HOME/.local/share/personal-skills/scripts/jira/check_jira_credentials.sh"
```

- **Exit 0:** continue.
- **Exit 1:** show the printed instructions exactly as-is and stop.

---

## Step 2 — Fetch issue from Jira

```bash
python3 "$HOME/.local/share/personal-skills/scripts/jira/fetch_jira.py" "<ISSUE_KEY>"
```

Outputs JSON: `key`, `url`, `summary`, `type`, `status`, `priority`, `reporter`, `assignee`, `description`, `comments[]`.

Extract:
- Full description text
- All comment bodies (may contain decisions, edge cases, clarifications)
- Current status / assignee

If the issue is already `Done` or `Closed`, warn the user and ask whether to continue.

---

## Step 3 — Research codebase

Using the description + comments as the requirement source, use the **Explore** agent to deeply research the codebase:

- Find all files related to the feature/bug area (components, hooks, stores, API, types, tests)
- Identify the existing code patterns and style conventions used in those files (naming, folder structure, state management approach, test patterns)
- Map each requirement bullet to the file(s) that would need to change
- Note any shared utilities, constants, or interfaces that should be reused rather than duplicated
- Identify what is missing vs what already partially exists

Return a structured map:

```
Requirement → File(s) → Current state → What needs to change
```

---

## Step 4 — Produce the implementation plan

Show the following output to the user:

```
════════════════════════════════════════════════════════
PLAN: <ISSUE_KEY> — <Issue Summary>
════════════════════════════════════════════════════════

REQUIREMENT SUMMARY
───────────────────
<3–5 sentences: what the issue asks for, why it's needed, any constraints from comments>

════════════════════════════════════════════════════════
CODEBASE IMPACT
════════════════════════════════════════════════════════
| # | Requirement | File | Current State | Change Needed |
|---|-------------|------|---------------|---------------|
| 1 | ...         | ...  | ...           | ...           |

════════════════════════════════════════════════════════
ACCEPTANCE CRITERIA
════════════════════════════════════════════════════════
1. <concrete, testable criterion>
2. ...

════════════════════════════════════════════════════════
IMPLEMENTATION TASKS
════════════════════════════════════════════════════════

Each task is independent and can be implemented and reviewed separately.

[T1] <Task title>
     Scope   : <what this task covers>
     Files   : <file paths>
     Approach: <how to implement, following existing patterns>
     AC      : <acceptance criteria specific to this task>
     Test    : <where/how to verify — component, page, API endpoint, etc.>

[T2] <Task title>
     ...

════════════════════════════════════════════════════════
QUICK TEST AREAS (end-to-end)
════════════════════════════════════════════════════════
- <user-facing action to verify>
- ...
```

**Task design rules:**
- Each task must be independently implementable (no circular dependencies between tasks)
- Tasks should be ordered so earlier tasks don't block later ones
- Prefer small, focused tasks (1–3 files each) over large catch-all tasks
- Follow the conventions and patterns found in Step 3 exactly — no new abstractions unless required
- Include a test/verify step in every task description

---

## Step 5 — Ask what to do next

```
What would you like to do?
  c) Create all tasks above as Jira subtasks
  s) Create a single custom subtask
  m) Create multiple custom subtasks
  e) Edit an existing issue description
  q) Quit
```

Wait for input.

---

## Step 6 — On "c" (create all tasks as subtasks)

For each task in the plan:

```
Create subtask: "[T1] <title>"? (y / n / s=skip all remaining)
```

On `y`, create the subtask in Jira using the Python script below.
On `n`, skip this one and continue.
On `s`, stop creating and show a summary of what was created.

After each creation, show:
```
✓ <KEY> — <title>
  URL: <jira-url>/browse/<KEY>
```

Use this Python script pattern to create each subtask:

```python
python3 << 'PYEOF'
import json, os, sys, urllib.request, base64

sys.path.insert(0, os.path.expanduser('~/.local/share/personal-skills/scripts/jira'))
from jira_adf import text_to_adf

email = os.environ.get('JIRA_EMAIL')
token = os.environ.get('JIRA_API_TOKEN')
url   = os.environ.get('JIRA_URL', '').rstrip('/')

if not all([email, token, url]):
    print('Missing JIRA env vars'); sys.exit(1)

parent_key  = 'PARENT_KEY'
summary     = 'SUBTASK_SUMMARY'
description = 'DESCRIPTION_TEXT'

project  = parent_key.split('-')[0]
auth     = base64.b64encode(f'{email}:{token}'.encode()).decode()

payload = json.dumps({
    'fields': {
        'project':     {'key': project},
        'summary':     summary,
        'issuetype':   {'name': 'Sub-task'},
        'parent':      {'key': parent_key},
        'description': text_to_adf(description),
    }
}).encode()

req = urllib.request.Request(
    f'{url}/rest/api/3/issue',
    data=payload,
    headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'},
    method='POST'
)

try:
    resp   = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    key    = result.get('key', 'N/A')
    print(f'Created: {key}')
    print(f'URL: {url}/browse/{key}')
except urllib.error.HTTPError as e:
    print(f'Error {e.code}: {e.read().decode()}')
    sys.exit(1)
PYEOF
```

For each subtask, build the description from the task plan using this template:

```
## Goal
<2–3 sentences connecting this subtask to the parent issue's context and why it matters>

## Changes

| Area | Change | Impact |
|------|--------|--------|
| **<Area 1>** | <what to change> | <expected result> |
| **<Area 2>** | <what to change> | <expected result> |

## Acceptance Criteria
- <criterion 1>
- <criterion 2>

## Where to Test
- <action> → <expected result>
- <action> → <expected result>
```

**Description rules:**
- No file paths or line numbers (they change; use the component/hook name instead)
- Use the **Changes table** to summarize scope — one row per logical area, bold the Area column
- Goal section: brief context from parent — don't repeat the full parent description
- Acceptance Criteria must be concrete and testable
- Where to Test: concrete actions with expected results (page URL, user action, API endpoint)

---

## Step 7 — On "s" (single custom subtask)

Ask:
1. Subtask title/summary (required)
2. Goal — brief context (optional — will auto-fill from parent if skipped)
3. Changes — enter each as `Area | Change | Impact` (optional — one per line, empty to skip)
4. Acceptance Criteria (optional — Enter to skip)
5. Where to Test (optional — Enter to skip)

Build the description using the same template as Step 6 (Goal + Changes table + AC + Where to Test). Show a confirmation summary, then on `y` create via the same Python script as Step 6.

---

## Step 8 — On "m" (multiple custom subtasks)

Loop through the Step 7 flow. After each creation ask:
```
Create another subtask? (y/n)
```
Continue until `n`.

---

## Step 9 — On "e" (edit a description)

Ask: "Which issue key to edit? (default: <ISSUE_KEY>)"

Fetch the current description:

```python
python3 << 'PYEOF'
import json, os, urllib.request, base64

email = os.environ.get('JIRA_EMAIL')
token = os.environ.get('JIRA_API_TOKEN')
url   = os.environ.get('JIRA_URL', '').rstrip('/')
auth  = base64.b64encode(f'{email}:{token}'.encode()).decode()

req = urllib.request.Request(
    f'{url}/rest/api/2/issue/ISSUE_KEY?fields=summary,description',
    headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode())
print(json.dumps(data['fields'].get('description', {}), indent=2))
PYEOF
```

Ask what to change, draft the new description using the same template format (Goal + Changes table + AC + Where to Test), show it for confirmation, then update on `y`:

```python
python3 << 'PYEOF'
import json, os, sys, urllib.request, base64

sys.path.insert(0, os.path.expanduser('~/.local/share/personal-skills/scripts/jira'))
from jira_adf import text_to_adf

email = os.environ.get('JIRA_EMAIL')
token = os.environ.get('JIRA_API_TOKEN')
url   = os.environ.get('JIRA_URL', '').rstrip('/')
auth  = base64.b64encode(f'{email}:{token}'.encode()).decode()

new_description = 'NEW DESCRIPTION TEXT'

payload = json.dumps({'fields': {'description': text_to_adf(new_description)}}).encode()

req = urllib.request.Request(
    f'{url}/rest/api/3/issue/ISSUE_KEY',
    data=payload,
    headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'},
    method='PUT'
)
try:
    resp = urllib.request.urlopen(req)
    print(f'Updated successfully (HTTP {resp.status})')
except urllib.request.HTTPError as e:
    print(f'Error {e.code}: {e.read().decode()}')
PYEOF
```

---

## Step 10 — On "q" (quit)

Exit without creating anything.

---

## Step 11 — Implementation guide

After all subtasks are created (or if `--no-create` was passed), output a step-by-step implementation guide:

```
════════════════════════════════════════════════════════
IMPLEMENTATION ORDER
════════════════════════════════════════════════════════

Work through the subtasks in this order to avoid merge conflicts
and keep each PR reviewable independently:

1. <SUBTASK_KEY> — <title>
   Start here: <first file/component to open>
   Pattern to follow: <existing file that uses the same pattern>

2. <SUBTASK_KEY> — <title>
   ...

After each subtask, run:
- <test command or manual verification step>
```

---

## Error handling

- **Missing env vars:** remind user to set `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_URL`
- **HTTP 401/403:** tell user credentials are invalid or lack permission, run `/ps-jira-login`
- **HTTP 404:** issue key not found — ask user to verify
- **Explore agent fails:** proceed with manual codebase description — ask user which files are involved
- **Subtask creation fails:** show error, offer to retry with the same data
