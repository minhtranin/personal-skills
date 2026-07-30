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

[BE]: <what this task delivers>
     Scope   : <what this task covers>
     Files   : <file paths>
     Approach: <how to implement, following existing patterns>

[FE]: <what this task delivers>
     ...

════════════════════════════════════════════════════════
QUICK TEST AREAS (end-to-end)
════════════════════════════════════════════════════════
- <user-facing action to verify>
- ...
```

**Task design rules — split by layer, not by file:**

Every task title starts with its layer tag: **`[BE]:`** or **`[FE]:`**. Use those two by default — that is the split.

Rules:
- **Default to 2 subtasks: one `[BE]`, one `[FE]`.** If the issue only touches one side, that's **1 subtask**.
- **Never split within a layer.** All FE work for this issue is one `[FE]` task, even across many components, hooks, and files. Same for `[BE]`.
- **Small cross-layer work stays in one task.** If the change touches both sides but is a few lines each, make it one task under whichever layer dominates.
- **Exception — big shared piece gets its own task.** If a **large common/shared component** or a **large handler/worker** is substantial on its own (heavy logic, reused by multiple call sites, reviewable independently), give it a separate task tagged by its layer, e.g. `[BE]: <handler name>` or `[FE]: <shared component name>`.
- **Cap: 4 subtasks.** More than that means the split is too fine — merge back.
- **No file overlap** between tasks — each file owned by exactly one task, so PRs don't conflict.
- Order tasks so earlier ones don't block later ones (BE before FE).
- Follow the conventions and patterns found in Step 3 exactly — no new abstractions unless required.

**Anti-pattern (too granular):**
```
[T1] Add type definitions
[T2] Add API endpoint
[T3] Add service method
[T4] Wire up hook
[T5] Update component
[T6] Add tests
```
→ Should be: `[BE]: <endpoint + service + types>` · `[FE]: <hook + component>`

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
Create subtask: "[BE]: <title>"? (y / n / s=skip all remaining)
```

The subtask summary in Jira **must keep the layer tag** — `[BE]: <title>` / `[FE]: <title>`.

On `y`, create the subtask in Jira using the Python script below.
On `n`, skip this one and continue.
On `s`, stop creating and show a summary of what was created.

After each creation, show:
```
✓ <KEY> — <title>
  URL: <jira-url>/browse/<KEY>
```

Every created subtask must:
- be **assigned to the current Jira user** (`JIRA_EMAIL` — the person running this plan)
- be **transitioned to status "Selected for Development"** right after creation

Use this Python script pattern to create each subtask:

```python
python3 << 'PYEOF'
import json, os, sys, urllib.request, urllib.parse, base64

sys.path.insert(0, os.path.expanduser('~/.local/share/personal-skills/scripts/jira'))
from jira_adf import text_to_adf

email = os.environ.get('JIRA_EMAIL')
token = os.environ.get('JIRA_API_TOKEN')
url   = os.environ.get('JIRA_URL', '').rstrip('/')

if not all([email, token, url]):
    print('Missing JIRA env vars'); sys.exit(1)

parent_key    = 'PARENT_KEY'
summary       = 'SUBTASK_SUMMARY'
description   = 'DESCRIPTION_TEXT'
target_status = 'Selected for Development'

project  = parent_key.split('-')[0]
auth     = base64.b64encode(f'{email}:{token}'.encode()).decode()
headers  = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

def api_get(path):
    req = urllib.request.Request(f'{url}{path}', headers=headers)
    return json.loads(urllib.request.urlopen(req).read().decode())

def api_post(path, data):
    req = urllib.request.Request(
        f'{url}{path}', data=json.dumps(data).encode(), headers=headers, method='POST'
    )
    return urllib.request.urlopen(req)

# Resolve the requester's accountId so the subtask can be self-assigned
account_id = None
try:
    users = api_get(f'/rest/api/3/user/search?query={urllib.parse.quote(email)}')
    if users:
        account_id = users[0]['accountId']
except Exception as e:
    print(f'Warning: could not resolve accountId for {email}: {e}')

fields = {
    'project':     {'key': project},
    'summary':     summary,
    'issuetype':   {'name': 'Sub-task'},
    'parent':      {'key': parent_key},
    'description': text_to_adf(description),
}
if account_id:
    fields['assignee'] = {'id': account_id}

payload = json.dumps({'fields': fields}).encode()
req = urllib.request.Request(
    f'{url}/rest/api/3/issue', data=payload, headers=headers, method='POST'
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

# Move the new subtask to "Selected for Development"
try:
    transitions = api_get(f'/rest/api/3/issue/{key}/transitions')['transitions']
    match = next(
        (t for t in transitions if t['name'].strip().lower() == target_status.lower()),
        None
    )
    if match:
        api_post(f'/rest/api/3/issue/{key}/transitions', {'transition': {'id': match['id']}})
        print(f'Status: {target_status}')
    else:
        names = ', '.join(t['name'] for t in transitions)
        print(f'Warning: no transition named "{target_status}" available (options: {names})')
except urllib.error.HTTPError as e:
    print(f'Warning: transition failed {e.code}: {e.read().decode()}')
PYEOF
```

For each subtask, build the description from the task plan using this template — **these two sections only**:

```
## Acceptance Criteria
- <criterion 1>
- <criterion 2>

## Where to Test
- <action> → <expected result>
- <action> → <expected result>
```

**Description rules:**
- **Nothing beyond these two sections.** No Goal, no Changes table, no context, no approach, no file lists — the parent issue already holds that.
- No file paths or line numbers (they change; use the component/hook name instead)
- Acceptance Criteria: concrete and testable, 2–5 bullets
- Where to Test: concrete actions with expected results (page URL, user action, API endpoint)
- Keep it short — if a bullet needs a paragraph, it belongs in the parent issue, not here

---

## Step 7 — On "s" (single custom subtask)

Ask:
1. Layer — `BE` or `FE` (required — becomes the `[BE]:` / `[FE]:` title prefix)
2. Subtask title/summary (required)
3. Acceptance Criteria (optional — Enter to skip)
4. Where to Test (optional — Enter to skip)

Build the description using the same template as Step 6 (**Acceptance Criteria + Where to Test only**). Show a confirmation summary, then on `y` create via the same Python script as Step 6.

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

Ask what to change, draft the new description using the same template format (**Acceptance Criteria + Where to Test only**), show it for confirmation, then update on `y`:

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
- **No "Selected for Development" transition available:** the subtask is still created (just left at its default initial status) — show the warning with the available transition names and let the user transition it manually if needed
