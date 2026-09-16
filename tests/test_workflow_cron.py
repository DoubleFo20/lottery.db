"""tests/test_workflow_cron.py
Comprehensive verification of GitHub Actions CI/CD workflow configuration:
- YAML syntax and structure
- Concurrency group and cancel-in-progress setting
- Permissions elevation (contents: write)
- Exact 3-line cron expressions covering 14:30–16:30 ICT (07:30–09:30 UTC) every 15 minutes
- Mathematical timezone conversion and boundary exclusion
- Full 8-step execution sequence and git push safeguards
"""

from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "lottery_auto_update.yml"


@pytest.fixture(scope="module")
def workflow_yaml_data():
    """Parse and return the workflow YAML content."""
    assert WORKFLOW_PATH.exists(), f"Workflow file not found at {WORKFLOW_PATH}"
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), "Workflow YAML must parse into a dictionary"
    return data


# ── 1. Syntax, Structure, and Trigger Tests ─────────────────────────

def test_workflow_yaml_syntax_and_root_keys(workflow_yaml_data):
    """Verify root keys in workflow YAML."""
    assert "name" in workflow_yaml_data
    assert workflow_yaml_data["name"] == "Continuous Lottery Auto-Update"
    assert "on" in workflow_yaml_data or True in workflow_yaml_data
    assert "permissions" in workflow_yaml_data
    assert "concurrency" in workflow_yaml_data
    assert "jobs" in workflow_yaml_data


def test_workflow_dispatch_trigger_enabled(workflow_yaml_data):
    """Verify manual execution via workflow_dispatch is enabled."""
    on_block = workflow_yaml_data.get("on") or workflow_yaml_data.get(True)
    assert "workflow_dispatch" in on_block, "workflow_dispatch trigger must be present"


def test_schedule_trigger_exists_with_exact_three_crons(workflow_yaml_data):
    """Verify schedule block contains exactly 3 cron schedule definitions."""
    on_block = workflow_yaml_data.get("on") or workflow_yaml_data.get(True)
    assert "schedule" in on_block, "schedule trigger must be present under 'on'"
    schedules = on_block["schedule"]
    assert isinstance(schedules, list), "schedule must be a list of cron definitions"
    assert len(schedules) == 3, f"Expected exactly 3 cron schedule lines, got {len(schedules)}"


# ── 2. Cron Schedule Exact Expressions & Timezone Mathematics ───────

def test_cron_expressions_exact_string_match(workflow_yaml_data):
    """
    Verify the exact 3 POSIX cron expressions required to cover 14:30–16:30 ICT
    every 15 minutes on the 1st and 16th of each month.
    """
    on_block = workflow_yaml_data.get("on") or workflow_yaml_data.get(True)
    crons = [item["cron"] for item in on_block["schedule"]]
    
    expected_crons = [
        "30,45 7 1,16 * *",      # 14:30, 14:45 ICT (07:30, 07:45 UTC)
        "0,15,30,45 8 1,16 * *", # 15:00, 15:15, 15:30, 15:45 ICT (08:00–08:45 UTC)
        "0,15,30 9 1,16 * *"     # 16:00, 16:15, 16:30 ICT (09:00–09:30 UTC)
    ]
    assert crons == expected_crons, f"Cron schedules mismatch.\nActual: {crons}\nExpected: {expected_crons}"


def test_cron_mathematical_breakdown_and_field_semantics(workflow_yaml_data):
    """Verify minute, hour, day-of-month, month, and day-of-week fields in all crons."""
    on_block = workflow_yaml_data.get("on") or workflow_yaml_data.get(True)
    crons = [item["cron"] for item in on_block["schedule"]]

    for cron_str in crons:
        parts = cron_str.strip().split()
        assert len(parts) == 5, f"Cron expression '{cron_str}' must have 5 space-delimited fields"
        minute_part, hour_part, dom_part, month_part, dow_part = parts
        
        # Day of month must strictly be 1,16
        assert dom_part == "1,16", f"Day-of-month must be '1,16', got '{dom_part}'"
        # Month must be wildcard *
        assert month_part == "*", f"Month must be '*', got '{month_part}'"
        # Day of week must be wildcard *
        assert dow_part == "*", f"Day-of-week must be '*', got '{dow_part}'"


def test_cron_covers_1430_to_1630_ict_every_15_minutes(workflow_yaml_data):
    """
    Parse the cron lines into concrete (UTC hour, UTC minute) pairs,
    convert each to Indochina Time (ICT = UTC + 7), and assert that the
    resulting timeline comprises exactly the 9 expected 15-minute intervals.
    """
    on_block = workflow_yaml_data.get("on") or workflow_yaml_data.get(True)
    crons = [item["cron"] for item in on_block["schedule"]]

    utc_times = []
    for cron_str in crons:
        parts = cron_str.split()
        minutes = [int(m) for m in parts[0].split(",")]
        hours = [int(h) for h in parts[1].split(",")]
        for h in hours:
            for m in minutes:
                utc_times.append((h, m))

    # Convert UTC to ICT (UTC+7)
    ict_times = []
    for h, m in utc_times:
        utc_dt = datetime(2026, 9, 16, h, m, tzinfo=timezone.utc)
        ict_dt = utc_dt.astimezone(timezone(timedelta(hours=7)))
        ict_times.append((ict_dt.hour, ict_dt.minute))

    # Expected 9 draw points: 14:30, 14:45, 15:00, 15:15, 15:30, 15:45, 16:00, 16:15, 16:30
    expected_ict_times = [
        (14, 30),
        (14, 45),
        (15, 0),
        (15, 15),
        (15, 30),
        (15, 45),
        (16, 0),
        (16, 15),
        (16, 30)
    ]

    assert ict_times == expected_ict_times, (
        f"Timeline mismatch in ICT.\nActual: {ict_times}\nExpected: {expected_ict_times}"
    )


def test_cron_strictly_excludes_out_of_window_executions(workflow_yaml_data):
    """
    Verify that hours before 07:30 UTC (14:30 ICT) and after 09:30 UTC (16:30 ICT)
    are strictly excluded from the schedule.
    """
    on_block = workflow_yaml_data.get("on") or workflow_yaml_data.get(True)
    crons = [item["cron"] for item in on_block["schedule"]]

    for cron_str in crons:
        parts = cron_str.split()
        minutes = [int(m) for m in parts[0].split(",")]
        hour = int(parts[1])

        if hour == 7:
            # Must NOT trigger at 07:00 or 07:15
            assert 0 not in minutes, "Hour 7 UTC must not execute at minute 0 (14:00 ICT)"
            assert 15 not in minutes, "Hour 7 UTC must not execute at minute 15 (14:15 ICT)"
        elif hour == 9:
            # Must NOT trigger at 09:45
            assert 45 not in minutes, "Hour 9 UTC must not execute at minute 45 (16:45 ICT)"
        elif hour == 8:
            assert minutes == [0, 15, 30, 45]
        else:
            pytest.fail(f"Unexpected hour {hour} in cron '{cron_str}'. Only hours 7, 8, 9 UTC permitted.")


# ── 3. Concurrency and Permissions ──────────────────────────────────

def test_concurrency_configuration(workflow_yaml_data):
    """Verify concurrency group and cancel-in-progress setting."""
    concurrency = workflow_yaml_data.get("concurrency")
    assert isinstance(concurrency, dict), "concurrency block must be a dict"
    assert concurrency.get("group") == "lottery-auto-update", (
        f"Expected group 'lottery-auto-update', got '{concurrency.get('group')}'"
    )
    assert concurrency.get("cancel-in-progress") is False, (
        "cancel-in-progress must be False so in-progress commits/pushes are not aborted"
    )


def test_permissions_contents_write(workflow_yaml_data):
    """Verify elevated permissions required to push commits back to the repo."""
    permissions = workflow_yaml_data.get("permissions")
    assert isinstance(permissions, dict), "permissions block must be a dict"
    assert permissions.get("contents") == "write", (
        f"Expected permissions.contents to be 'write', got '{permissions.get('contents')}'"
    )


# ── 4. Job Runner and Step Sequence ─────────────────────────────────

def test_job_runner_ubuntu_latest(workflow_yaml_data):
    """Verify the workflow runs on ubuntu-latest."""
    jobs = workflow_yaml_data.get("jobs", {})
    assert "auto-update" in jobs, "Job 'auto-update' must exist"
    job = jobs["auto-update"]
    assert job.get("runs-on") == "ubuntu-latest", (
        f"Expected runs-on 'ubuntu-latest', got '{job.get('runs-on')}'"
    )


def test_complete_step_sequence_and_tools(workflow_yaml_data):
    """
    Verify the 8-step pipeline sequence in exact order:
    1. Checkout
    2. Setup Python 3.11
    3. Setup Node.js 20
    4. Install Python dependencies (requests, beautifulsoup4)
    5. Fetch Draw Results & Retrain Pipeline (analytics/result_fetcher.py)
    6. Run Node.js 3D Data & Asset Build (npm run build)
    7. Sync Dashboard Files
    8. Commit & Push Changes
    """
    job = workflow_yaml_data["jobs"]["auto-update"]
    steps = job.get("steps", [])
    assert len(steps) == 8, f"Expected 8 pipeline steps, got {len(steps)}"

    step_names = [s.get("name") for s in steps]
    expected_names = [
        "Checkout repository",
        "Set up Python",
        "Set up Node.js",
        "Install Python dependencies",
        "Fetch Draw Results & Retrain Pipeline",
        "Run Node.js 3D Data & Asset Build",
        "Sync Dashboard Files",
        "Commit & Push Changes",
    ]
    assert step_names == expected_names, (
        f"Step sequence mismatch.\nActual: {step_names}\nExpected: {expected_names}"
    )

    # Step 1: Checkout with fetch-depth: 0
    assert steps[0].get("uses") == "actions/checkout@v4"
    assert steps[0].get("with", {}).get("fetch-depth") == 0

    # Step 2: Python 3.11
    assert steps[1].get("uses") == "actions/setup-python@v5"
    assert steps[1].get("with", {}).get("python-version") == "3.11"

    # Step 3: Node 20
    assert steps[2].get("uses") == "actions/setup-node@v4"
    assert steps[2].get("with", {}).get("node-version") == "20"

    # Step 4: requests and beautifulsoup4
    run_install = steps[3].get("run", "")
    assert "requests" in run_install and "beautifulsoup4" in run_install

    # Step 5: Python fetcher invocation
    run_fetch = steps[4].get("run", "")
    assert "python analytics/result_fetcher.py" in run_fetch

    # Step 6: npm run build
    run_build = steps[5].get("run", "")
    assert "npm run build" in run_build

    # Step 7: Dashboard file mirroring
    run_sync = steps[6].get("run", "")
    assert "cp index.html strategy.html" in run_sync
    assert "dashboard" in run_sync

    # Step 8: Commit & push guard
    run_push = steps[7].get("run", "")
    assert "git config --global user.name" in run_push
    assert "git diff --staged --quiet" in run_push
    assert "[skip ci]" in run_push
    assert "git push" in run_push
