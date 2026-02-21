Stew
/

I am working on -
Stew v0.1 - a lightweight overnight processing system that generates a concise daily “Morning Brief” at 05:30. It reviews the previous 24 hours of journal-style inputs and extracts behavioural signals aligned to three core trajectory pillars: relationship (intentional connection with Jodie), mental/emotional discipline (focus, drift containment, self-regulation), and physical consistency (training and nutrition behaviours). The output is a short, slightly firm and directive brief that reinforces what is on track, highlights blind spots, and defines up to three specific, executable priority moves for the day. The system is intentionally minimal: no long-term analytics, no complex modelling, and no optimisation loops. It acts as a behavioural stabiliser rather than a productivity engine or reflective therapy tool. By constraining output length, enforcing a hard cap on priorities, and flagging recurring drift patterns (such as unbounded system-building), Stew is designed to maintain clarity, prevent distraction creep, and keep daily effort aligned with long-term trajectory.

I have the telegram brain dump already running and working and details of that are in the project files, along with stew_v01_plan.txt which is a broad way forward for the next set of enhancements...
11:28 am
Reading the Stew v0.1 plan
Done

Good, I've got the full picture. Let me build the complete stew.py — all stages in one flat file, as planned. I'll study your actual brain dump data to make sure the heuristics match your real patterns.
Creating Stew v0.1 - overnight processing system
Done

Now let me also create the config.py and a setup README so you can drop this straight onto your server:
Created a file, read a file
Done

Here's what's in stew.py and how it maps to your plan:

Stages 1–6 all implemented in one flat file, no abstraction layers.

Stage 2 (Delta Loader) — reads your JSONL, filters by timestamp >= now - 24h. Also loads 7-day window separately for drift detection.

Stage 3 (Pillar Assessor) — keyword matching against your actual data patterns. I pulled keywords from your real entries (temazepam for mental/sleep, Jodie/anniversary/wedding vows for relationship, body fat measurements/running vest/electrolytes for physical). The heuristics reflect what you actually dump.

Stage 4 (Priority Generator) — addresses weakest pillars first, drift containment gets a slot if flagged, hard cap at 3. Language is firm, not therapeutic.

Stage 5 (Brief Builder) — exactly the structure from your plan, 12-line hard cap enforced.

Stage 6 (Drift Guard) — three drift themes baked in: system_building, open_source_hoarding, and tool_collecting (all very visible in your actual dump data). Threshold is 3 hits in 7 days.

To deploy: symlink your live brain_dump_log.jsonl into stew/input/, run once to test, then set the cron. The SETUP.md has the exact commands.

One thing to tweak once you've run it a few times: the RELATIONSHIP_KEYWORDS set. Right now "Jodie" is the anchor — if she appears in your dumps under other references, just add them. Same for the physical keywords if you track different metrics.
Stew
PY 
Setup
Document · MD 


Claude is AI and can make mistakes. Please double-check responses.
Stew · PY
#!/usr/bin/env python3
"""
stew.py — Stew v0.1 Overnight Processing System

Runs at 05:30 via cron. Reads last 24h of brain dump entries.
Assesses three behavioural pillars. Outputs a concise Morning Brief.

Usage:
    python3 stew.py

Cron (05:30 daily):
    30 5 * * * /usr/bin/python3 /path/to/stew/stew.py >> /path/to/stew/logs/run.log 2>&1
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent

# Input: point this at your live brain_dump_log.jsonl
BRAIN_DUMP_FILE = SCRIPT_DIR / "input" / "brain_dump.jsonl"

# Output
OUTPUT_DIR = SCRIPT_DIR / "output" / "morning_briefs"
LOG_DIR = SCRIPT_DIR / "logs"

# Window for delta load (hours)
DELTA_HOURS = 24

# Drift detection window (days)
DRIFT_WINDOW_DAYS = 7

# Drift threshold: how many entries on a theme before it's a drift flag
DRIFT_THRESHOLD = 3

# Max lines in the brief (enforced by trimming)
MAX_BRIEF_LINES = 12

# Max priorities
MAX_PRIORITIES = 3


# ---------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------

def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"stew_{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ]
    )


# ---------------------------------------------------------------------
# STAGE 2 — DELTA LOADER
# ---------------------------------------------------------------------

def load_entries(hours: int = DELTA_HOURS) -> list[dict]:
    """Load entries from the last N hours."""
    if not BRAIN_DUMP_FILE.exists():
        logging.warning(f"Brain dump file not found: {BRAIN_DUMP_FILE}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    entries = []

    with open(BRAIN_DUMP_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts_raw = entry.get("timestamp", "")
                if not ts_raw:
                    continue
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                if ts >= cutoff:
                    entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue

    logging.info(f"Delta loader: {len(entries)} entries in last {hours}h")
    return entries


def load_entries_window(days: int = DRIFT_WINDOW_DAYS) -> list[dict]:
    """Load entries from the last N days (for drift detection)."""
    return load_entries(hours=days * 24)


# ---------------------------------------------------------------------
# STAGE 3 — PILLAR SIGNAL EXTRACTOR
# ---------------------------------------------------------------------

# Keyword sets for each pillar
RELATIONSHIP_KEYWORDS = {
    "jodie", "wife", "anniversary", "vow", "wedding", "date", "dinner",
    "conversation", "connection", "together", "partner", "family", "kids",
    "listen", "quality time", "us", "we "
}

PHYSICAL_KEYWORDS = {
    "training", "gym", "run", "running", "workout", "exercise", "protein",
    "strava", "walk", "cycling", "swim", "weights", "steps", "km", "5k",
    "10k", "electrolyte", "nutrition", "diet", "body fat", "belly", "measurement",
    "kmart vest", "running vest", "garmin", "pace"
}

MENTAL_KEYWORDS = {
    "avoidance", "frustration", "frustrated", "stuck", "overwhelm", "overwhelmed",
    "anxious", "anxiety", "distracted", "procrastinat", "drift", "unfocused",
    "scattered", "behind", "late", "can't", "cannot", "worried", "stress",
    "temazepam", "temazapan", "sleep", "tired", "exhausted", "wired"
}

# Drift themes: patterns that indicate rabbit-hole / distraction territory
DRIFT_THEME_KEYWORDS = {
    "system_building": {
        "agent", "orchestrat", "pipeline", "workflow", "automat", "framework",
        "architecture", "module", "scaffold", "refactor", "abstract"
    },
    "open_source_hoarding": {
        "github", "github.com", "repo", "clone", "star", "fork"
    },
    "tool_collecting": {
        "tool", "service", "platform", "api", "integration", "setup", "install",
        "deploy", "configure"
    }
}


def _text_lower(entry: dict) -> str:
    return (entry.get("input", "") + " " + str(entry.get("result", {}).get("signals", []))).lower()


def _keyword_hit(text: str, keywords: set) -> bool:
    return any(kw in text for kw in keywords)


def _count_category(entries: list[dict], category: str) -> int:
    return sum(1 for e in entries if e.get("result", {}).get("category") == category)


def assess_pillars(entries_24h: list[dict], entries_7d: list[dict]) -> dict:
    """
    Assess the three core pillars and detect drift themes.

    Returns:
        {
          "relationship": {"status": "on_track"|"needs_attention", "signal": str},
          "mental":       {"status": "on_track"|"needs_attention", "signal": str},
          "physical":     {"status": "on_track"|"needs_attention", "signal": str},
          "drift_flags":  [str]
        }
    """
    result = {
        "relationship": {"status": "needs_attention", "signal": "No signal in last 24h"},
        "mental":       {"status": "on_track",        "signal": "No friction detected"},
        "physical":     {"status": "needs_attention", "signal": "No signal in last 24h"},
        "drift_flags":  []
    }

    # --- RELATIONSHIP ---
    rel_hits = [e for e in entries_24h if _keyword_hit(_text_lower(e), RELATIONSHIP_KEYWORDS)]
    if rel_hits:
        sample = rel_hits[0].get("input", "")[:80]
        result["relationship"] = {
            "status": "on_track",
            "signal": f"Active signal — '{sample}'"
        }
    else:
        result["relationship"] = {
            "status": "needs_attention",
            "signal": "No relationship-oriented entries in last 24h"
        }

    # --- PHYSICAL ---
    phys_hits = [e for e in entries_24h if _keyword_hit(_text_lower(e), PHYSICAL_KEYWORDS)]
    if phys_hits:
        sample = phys_hits[0].get("input", "")[:80]
        result["physical"] = {
            "status": "on_track",
            "signal": f"Active signal — '{sample}'"
        }
    else:
        result["physical"] = {
            "status": "needs_attention",
            "signal": "No physical/training entries in last 24h"
        }

    # --- MENTAL ---
    mental_hits = [e for e in entries_24h if _keyword_hit(_text_lower(e), MENTAL_KEYWORDS)]
    if mental_hits:
        sample = mental_hits[0].get("input", "")[:80]
        result["mental"] = {
            "status": "needs_attention",
            "signal": f"Friction signal — '{sample}'"
        }
    else:
        result["mental"] = {
            "status": "on_track",
            "signal": "No friction or avoidance signals detected"
        }

    # --- DRIFT DETECTION (7-day window) ---
    for theme_name, theme_keywords in DRIFT_THEME_KEYWORDS.items():
        count = sum(1 for e in entries_7d if _keyword_hit(_text_lower(e), theme_keywords))
        if count >= DRIFT_THRESHOLD:
            result["drift_flags"].append(f"{theme_name} ({count} hits in 7d)")

    logging.info(f"Pillar assessment: rel={result['relationship']['status']}, "
                 f"mental={result['mental']['status']}, phys={result['physical']['status']}, "
                 f"drift={result['drift_flags']}")

    return result


# ---------------------------------------------------------------------
# STAGE 4 — PRIORITY GENERATOR
# ---------------------------------------------------------------------

PRIORITY_TEMPLATES = {
    "relationship_action": [
        "Check in with Jodie today — not logistics, actual connection.",
        "Carve out 20 minutes of undivided time with Jodie this evening.",
        "Send Jodie a message that has nothing to do with tasks or plans.",
    ],
    "physical_action": [
        "Get the training session done before anything else today.",
        "Log your nutrition before the day runs away. Protein first.",
        "Movement before screens. Non-negotiable.",
    ],
    "mental_action": [
        "Name the thing you've been avoiding. Then do it first.",
        "One hour of deep work before you open anything reactive.",
        "If you're feeling scattered, write it out before acting on it.",
    ],
    "drift_containment": [
        "You're in a system-building loop. Close the tabs. Finish something.",
        "Stop collecting repos. Pick one and actually use it.",
        "Tool curiosity is fine — hoarding is drift. Ship something.",
    ],
    "general_focus": [
        "Three things done well beats ten things started.",
        "Block your first 90 minutes. No Telegram, no feeds.",
    ]
}


def _weakest_pillars(assessment: dict) -> list[str]:
    """Return pillars that need attention, ordered by priority."""
    pillars = ["relationship", "physical", "mental"]
    return [p for p in pillars if assessment[p]["status"] == "needs_attention"]


def generate_priorities(assessment: dict) -> list[str]:
    """
    Generate up to MAX_PRIORITIES behavioural priority statements.
    At least one must address the weakest pillar.
    """
    priorities = []
    weak = _weakest_pillars(assessment)

    # 1. Address weakest pillar first
    if "relationship" in weak:
        priorities.append(PRIORITY_TEMPLATES["relationship_action"][0])
    if "physical" in weak and len(priorities) < MAX_PRIORITIES:
        priorities.append(PRIORITY_TEMPLATES["physical_action"][0])
    if "mental" in weak and len(priorities) < MAX_PRIORITIES:
        priorities.append(PRIORITY_TEMPLATES["mental_action"][0])

    # 2. If drift detected, add containment (replaces a general slot)
    if assessment["drift_flags"] and len(priorities) < MAX_PRIORITIES:
        priorities.append(PRIORITY_TEMPLATES["drift_containment"][0])

    # 3. Fill remaining with general focus if needed
    if len(priorities) == 0:
        priorities.append(PRIORITY_TEMPLATES["general_focus"][0])

    if len(priorities) < MAX_PRIORITIES and not assessment["drift_flags"]:
        priorities.append(PRIORITY_TEMPLATES["general_focus"][1])

    # Hard cap
    priorities = priorities[:MAX_PRIORITIES]

    logging.info(f"Generated {len(priorities)} priorities")
    return priorities


# ---------------------------------------------------------------------
# STAGE 5 — MORNING BRIEF BUILDER
# ---------------------------------------------------------------------

PILLAR_STATUS_ICONS = {
    "on_track": "✓",
    "needs_attention": "⚠"
}


def build_brief(date: datetime, assessment: dict, priorities: list[str], entry_count: int) -> str:
    """Build the morning brief string. Enforces ≤ MAX_BRIEF_LINES."""
    lines = []

    date_str = date.strftime("%A %d %B %Y")
    lines.append(f"🥘 Stew Morning Brief — {date_str}")
    lines.append("")

    # Pillar summary
    lines.append("🎯 Today's Alignment")
    for pillar in ["relationship", "mental", "physical"]:
        data = assessment[pillar]
        icon = PILLAR_STATUS_ICONS[data["status"]]
        label = pillar.capitalize()
        # Keep signal short
        signal = data["signal"]
        if len(signal) > 70:
            signal = signal[:67] + "..."
        lines.append(f"  {icon} {label}: {signal}")

    lines.append("")

    # Priorities
    lines.append("🔹 Priority Moves")
    for i, p in enumerate(priorities, 1):
        lines.append(f"  {i}. {p}")

    # Containment notice (if drift)
    if assessment["drift_flags"]:
        lines.append("")
        lines.append("🔸 Containment Notice")
        flags_str = ", ".join(assessment["drift_flags"])
        lines.append(f"  Drift pattern active: {flags_str}")
        lines.append(f"  Finish before you start something new.")

    lines.append("")
    lines.append(f"  {entry_count} entries processed from last 24h.")

    # Enforce line cap
    if len(lines) > MAX_BRIEF_LINES:
        lines = lines[:MAX_BRIEF_LINES]
        lines[-1] = "  [trimmed]"

    return "\n".join(lines)


def write_brief(brief_text: str, date: datetime) -> Path:
    """Write brief to output directory. Returns path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / f"morning_brief_{date.strftime('%Y-%m-%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(brief_text)
        f.write("\n")
    logging.info(f"Brief written to: {filename}")
    return filename


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    setup_logging()
    logging.info("=" * 50)
    logging.info("Stew v0.1 — Starting run")
    logging.info("=" * 50)

    now = datetime.now(timezone.utc)

    # Stage 2: Load entries
    entries_24h = load_entries(hours=DELTA_HOURS)
    entries_7d = load_entries_window(days=DRIFT_WINDOW_DAYS)

    if not entries_24h:
        logging.warning("No entries in last 24h — generating minimal brief")

    # Stage 3: Assess pillars
    assessment = assess_pillars(entries_24h, entries_7d)

    # Stage 4: Generate priorities
    priorities = generate_priorities(assessment)

    # Stage 5: Build and write brief
    brief_text = build_brief(now, assessment, priorities, len(entries_24h))
    brief_path = write_brief(brief_text, now)

    # Print to stdout (captured by cron log)
    print("\n" + brief_text + "\n")
    logging.info("Stew v0.1 — Run complete")

    return brief_path


if __name__ == "__main__":
    main()

