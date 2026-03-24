from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "images"
README_PATH = ROOT / "README.md"
LEETCODE_USERNAME = "GiveMeAJob9"
GRAPHQL_URL = "https://leetcode.com/graphql"
GRAPHQL_QUERY = """
query userProfile($username: String!) {
  allQuestionsCount {
    difficulty
    count
  }
  matchedUser(username: $username) {
    username
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
      totalSubmissionNum {
        difficulty
        count
      }
    }
    profile {
      ranking
      reputation
      starRating
    }
  }
}
""".strip()

CARD_THEMES = {
    "Total Solved": {
        "start": "#f97316",
        "end": "#14b8a6",
        "soft": "#132238",
        "badge": "ALL",
        "caption": "Progress across the full LeetCode pool.",
    },
    "Easy": {
        "start": "#22c55e",
        "end": "#84cc16",
        "soft": "#132a1d",
        "badge": "E",
        "caption": "Keeps the fundamentals sharp.",
    },
    "Medium": {
        "start": "#f59e0b",
        "end": "#f97316",
        "soft": "#2f2008",
        "badge": "M",
        "caption": "Core interview territory and growth lane.",
    },
    "Hard": {
        "start": "#ef4444",
        "end": "#ec4899",
        "soft": "#301019",
        "badge": "H",
        "caption": "Stretch work for deeper problem-solving range.",
    },
}


def fetch_leetcode_stats(username: str) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/{username}/",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }
    payload = {"query": GRAPHQL_QUERY, "variables": {"username": username}}

    response = requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    body = response.json()

    if body.get("errors"):
        raise RuntimeError(f"LeetCode GraphQL returned errors: {body['errors']}")

    data = body.get("data") or {}
    user = data.get("matchedUser")
    if not user:
        raise RuntimeError(f"Could not find public LeetCode profile for '{username}'.")

    total_counts = difficulty_map(data.get("allQuestionsCount"))
    solved_counts = difficulty_map((user.get("submitStatsGlobal") or {}).get("acSubmissionNum"))
    submission_counts = difficulty_map((user.get("submitStatsGlobal") or {}).get("totalSubmissionNum"))
    profile = user.get("profile") or {}

    solved_total = solved_counts.get("All", 0)
    submitted_total = submission_counts.get("All", 0)
    acceptance_rate = (solved_total / submitted_total * 100) if submitted_total else None

    return {
        "username": username,
        "totalSolved": solved_total,
        "totalQuestions": total_counts.get("All", 0),
        "easySolved": solved_counts.get("Easy", 0),
        "totalEasy": total_counts.get("Easy", 0),
        "mediumSolved": solved_counts.get("Medium", 0),
        "totalMedium": total_counts.get("Medium", 0),
        "hardSolved": solved_counts.get("Hard", 0),
        "totalHard": total_counts.get("Hard", 0),
        "acceptanceRate": acceptance_rate,
        "ranking": to_int(profile.get("ranking")),
        "reputation": to_int(profile.get("reputation")),
        "starRating": profile.get("starRating"),
        "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def difficulty_map(entries: list[dict[str, Any]] | None) -> dict[str, int]:
    mapped: dict[str, int] = {}
    for entry in entries or []:
        difficulty = entry.get("difficulty")
        if difficulty:
            mapped[difficulty] = to_int(entry.get("count"), default=0)
    return mapped


def to_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def compact_number(value: int | None) -> str:
    if value is None:
        return "n/a"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def completion_rate(solved: int, total: int) -> float:
    if not total:
        return 0.0
    return solved / total * 100


def progress_bar_width(percent: float, max_width: float, min_width: float) -> float:
    if percent <= 0:
        return 0.0
    return min(max_width, max(max_width * percent / 100, min_width))


def next_milestone(current: int) -> int:
    milestones = [10, 25, 50, 75, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 4000]
    for milestone in milestones:
        if milestone > current:
            return milestone
    step = 500 if current >= 1000 else 100
    return ((current // step) + 1) * step


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def build_progress_card(
    title: str,
    solved: int,
    total: int,
    filename: Path,
    theme: dict[str, str],
) -> None:
    percent = completion_rate(solved, total)
    fill_width = progress_bar_width(percent, max_width=286, min_width=26)
    shine_width = min(fill_width, 122)
    remaining = max(total - solved, 0)
    gradient_id = f"{filename.stem.replace('-', '_')}_gradient"
    panel_id = f"{filename.stem.replace('-', '_')}_panel"
    glow_id = f"{filename.stem.replace('-', '_')}_glow"
    safe_title = escape(title)
    safe_caption = escape(theme["caption"])

    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="440" height="172" viewBox="0 0 440 172" role="img" aria-labelledby="{filename.stem}_title {filename.stem}_desc">
  <title id="{filename.stem}_title">{safe_title} progress card</title>
  <desc id="{filename.stem}_desc">{safe_title}: {solved} solved out of {total} total problems.</desc>
  <defs>
    <linearGradient id="{panel_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0d1728" />
      <stop offset="100%" stop-color="#09111d" />
    </linearGradient>
    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{theme['start']}" />
      <stop offset="100%" stop-color="{theme['end']}" />
    </linearGradient>
    <filter id="{glow_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="18" result="blur" />
      <feColorMatrix
        in="blur"
        type="matrix"
        values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.35 0"
      />
    </filter>
    <pattern id="{filename.stem}_pattern" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#223048" stroke-width="1" opacity="0.35" />
    </pattern>
  </defs>
  <rect width="440" height="172" rx="26" fill="#050b15" />
  <rect x="1" y="1" width="438" height="170" rx="25" fill="url(#{panel_id})" stroke="#1f2c43" />
  <rect x="1" y="1" width="438" height="170" rx="25" fill="url(#{filename.stem}_pattern)" />
  <circle cx="364" cy="28" r="62" fill="{theme['start']}" opacity="0.16" filter="url(#{glow_id})" />
  <circle cx="410" cy="148" r="70" fill="{theme['end']}" opacity="0.08" />
  <rect x="24" y="24" width="64" height="64" rx="22" fill="{theme['soft']}" stroke="#243149" />
  <text x="56" y="63" fill="white" font-size="28" font-weight="700" text-anchor="middle" font-family="SFMono-Regular,Consolas,Monaco,monospace">{escape(theme['badge'])}</text>
  <text x="104" y="40" fill="#7dd3fc" font-size="11" font-weight="700" letter-spacing="1.2" font-family="SFMono-Regular,Consolas,Monaco,monospace">LIVE METRIC</text>
  <text x="104" y="66" fill="#f8fafc" font-size="24" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{safe_title}</text>
  <rect x="346" y="24" width="70" height="30" rx="15" fill="#101a2d" stroke="{theme['end']}" stroke-opacity="0.45" />
  <text x="381" y="44" fill="#f8fafc" font-size="13" font-weight="700" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif">{percent:.2f}%</text>
  <text x="104" y="104" fill="#ffffff" font-size="32" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{solved:,}</text>
  <text x="184" y="104" fill="#94a3b8" font-size="18" font-family="Segoe UI,Arial,sans-serif">/ {total:,}</text>
  <rect x="104" y="120" width="286" height="14" rx="7" fill="#162338" />
  <rect x="104" y="120" width="{fill_width:.2f}" height="14" rx="7" fill="url(#{gradient_id})" />
  <rect x="104" y="120" width="{shine_width:.2f}" height="14" rx="7" fill="#ffffff" opacity="0.16" />
  <rect x="24" y="140" width="96" height="28" rx="14" fill="#0f1a2d" stroke="#233149" />
  <text x="72" y="158" fill="#e2e8f0" font-size="11" font-weight="700" text-anchor="middle" font-family="SFMono-Regular,Consolas,Monaco,monospace">{remaining:,} LEFT</text>
  <text x="132" y="158" fill="#9fb0c8" font-size="12.5" font-family="Segoe UI,Arial,sans-serif">{safe_caption}</text>
</svg>
    """
    write_text(filename, svg)


def build_dashboard(data: dict[str, Any], filename: Path) -> None:
    total_percent = completion_rate(data["totalSolved"], data["totalQuestions"])
    easy_percent = completion_rate(data["easySolved"], data["totalEasy"])
    medium_percent = completion_rate(data["mediumSolved"], data["totalMedium"])
    hard_percent = completion_rate(data["hardSolved"], data["totalHard"])
    acceptance = "n/a" if data["acceptanceRate"] is None else f"{data['acceptanceRate']:.2f}%"
    ranking_compact = compact_number(data["ranking"])
    next_target = next_milestone(data["totalSolved"])
    to_target = max(next_target - data["totalSolved"], 0)

    rows = [
        dashboard_row("Easy", data["easySolved"], data["totalEasy"], easy_percent, 132, CARD_THEMES["Easy"]),
        dashboard_row("Medium", data["mediumSolved"], data["totalMedium"], medium_percent, 218, CARD_THEMES["Medium"]),
        dashboard_row("Hard", data["hardSolved"], data["totalHard"], hard_percent, 304, CARD_THEMES["Hard"]),
    ]

    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="920" height="404" viewBox="0 0 920 404" role="img" aria-labelledby="dashboard_title dashboard_desc">
  <title id="dashboard_title">LeetCode dashboard for {escape(data['username'])}</title>
  <desc id="dashboard_desc">A visual summary of solved problems, completion percentages, acceptance rate, and ranking.</desc>
  <defs>
    <linearGradient id="dashboard_bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06111f" />
      <stop offset="50%" stop-color="#0b1428" />
      <stop offset="100%" stop-color="#111827" />
    </linearGradient>
    <linearGradient id="dashboard_accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f97316" />
      <stop offset="100%" stop-color="#14b8a6" />
    </linearGradient>
    <linearGradient id="dashboard_card" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b1526" />
      <stop offset="100%" stop-color="#09111d" />
    </linearGradient>
    <pattern id="dashboard_grid" width="26" height="26" patternUnits="userSpaceOnUse">
      <path d="M 26 0 L 0 0 0 26" fill="none" stroke="#1e293b" stroke-width="1" opacity="0.32" />
    </pattern>
    <filter id="dashboard_glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="20" result="blur" />
      <feColorMatrix
        in="blur"
        type="matrix"
        values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.30 0"
      />
    </filter>
  </defs>
  <rect width="920" height="404" rx="30" fill="url(#dashboard_bg)" />
  <rect width="920" height="404" rx="30" fill="url(#dashboard_grid)" />
  <circle cx="760" cy="54" r="92" fill="#f97316" opacity="0.12" filter="url(#dashboard_glow)" />
  <circle cx="842" cy="316" r="120" fill="#14b8a6" opacity="0.08" filter="url(#dashboard_glow)" />
  <rect x="22" y="22" width="876" height="360" rx="26" fill="#081120" fill-opacity="0.82" stroke="#213149" />

  <text x="42" y="58" fill="#f8fafc" font-size="29" font-weight="700" font-family="Segoe UI,Arial,sans-serif">LeetCode Progress Dashboard</text>
  <text x="42" y="82" fill="#93a4bd" font-size="14" font-family="Segoe UI,Arial,sans-serif">@{escape(data['username'])} | official GraphQL source | rendered as custom SVG</text>

  <rect x="646" y="38" width="100" height="28" rx="14" fill="#0f1b30" stroke="#24344d" />
  <text x="696" y="56" fill="#dbeafe" font-size="11.5" font-weight="700" text-anchor="middle" font-family="SFMono-Regular,Consolas,Monaco,monospace">OFFICIAL DATA</text>
  <rect x="758" y="38" width="118" height="28" rx="14" fill="#0f1b30" stroke="#24344d" />
  <text x="817" y="56" fill="#d1fae5" font-size="11.5" font-weight="700" text-anchor="middle" font-family="SFMono-Regular,Consolas,Monaco,monospace">AUTO REFRESH</text>

  <rect x="42" y="112" width="392" height="238" rx="28" fill="url(#dashboard_card)" stroke="#22314a" />
  <circle cx="334" cy="152" r="62" fill="#f97316" opacity="0.14" filter="url(#dashboard_glow)" />
  <circle cx="364" cy="270" r="72" fill="#14b8a6" opacity="0.08" />

  <text x="66" y="144" fill="#8fa2bb" font-size="12" letter-spacing="1.2" font-family="SFMono-Regular,Consolas,Monaco,monospace">TOTAL SOLVED</text>
  <rect x="304" y="126" width="108" height="46" rx="18" fill="#0f1a2d" stroke="#24344d" />
  <text x="358" y="146" fill="#8fa2bb" font-size="11" letter-spacing="0.8" text-anchor="middle" font-family="SFMono-Regular,Consolas,Monaco,monospace">GLOBAL RANK</text>
  <text x="358" y="164" fill="#ffffff" font-size="22" font-weight="700" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif">{ranking_compact}</text>

  <text x="66" y="210" fill="#ffffff" font-size="60" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{data['totalSolved']:,}</text>
  <text x="196" y="210" fill="#94a3b8" font-size="24" font-family="Segoe UI,Arial,sans-serif">/ {data['totalQuestions']:,}</text>
  <text x="66" y="240" fill="#dbe5f4" font-size="18" font-family="Segoe UI,Arial,sans-serif">{total_percent:.2f}% of all public LeetCode problems completed</text>

  <rect x="66" y="258" width="306" height="18" rx="9" fill="#162339" />
  <rect x="66" y="258" width="{progress_bar_width(total_percent, max_width=306, min_width=30):.2f}" height="18" rx="9" fill="url(#dashboard_accent)" />
  <rect x="66" y="258" width="{min(progress_bar_width(total_percent, max_width=306, min_width=30), 120):.2f}" height="18" rx="9" fill="#ffffff" opacity="0.16" />

  <rect x="66" y="294" width="148" height="46" rx="18" fill="#0f1b30" stroke="#24344d" />
  <text x="84" y="314" fill="#8fa2bb" font-size="11" letter-spacing="0.8" font-family="SFMono-Regular,Consolas,Monaco,monospace">NEXT TARGET</text>
  <text x="84" y="331" fill="#ffffff" font-size="22" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{next_target:,}</text>
  <text x="150" y="331" fill="#9fb0c8" font-size="13" font-family="Segoe UI,Arial,sans-serif">{to_target:,} to go</text>

  <rect x="228" y="294" width="144" height="46" rx="18" fill="#0f1b30" stroke="#24344d" />
  <text x="246" y="314" fill="#8fa2bb" font-size="11" letter-spacing="0.8" font-family="SFMono-Regular,Consolas,Monaco,monospace">ACCEPTANCE</text>
  <text x="246" y="331" fill="#ffffff" font-size="22" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{acceptance}</text>

  <text x="474" y="110" fill="#93a4bd" font-size="13" letter-spacing="1" font-family="SFMono-Regular,Consolas,Monaco,monospace">DIFFICULTY BREAKDOWN</text>

  {''.join(rows)}
  <text x="42" y="378" fill="#7f91aa" font-size="12.5" font-family="Segoe UI,Arial,sans-serif">Last refresh: {escape(data['lastUpdated'])} | Generated automatically by Python + GitHub Actions.</text>
</svg>
    """
    write_text(filename, svg)


def dashboard_row(label: str, solved: int, total: int, percent: float, y: int, theme: dict[str, str]) -> str:
    fill_width = progress_bar_width(percent, max_width=126, min_width=18)
    remaining = max(total - solved, 0)
    gradient_id = f"{label.lower()}_dashboard_gradient"
    return f"""
  <defs>
    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{theme['start']}" />
      <stop offset="100%" stop-color="{theme['end']}" />
    </linearGradient>
  </defs>
  <rect x="474" y="{y}" width="386" height="66" rx="22" fill="#0c1729" stroke="#22314a" />
  <rect x="492" y="{y + 18}" width="62" height="32" rx="16" fill="#101b30" stroke="{theme['end']}" stroke-opacity="0.30" />
  <text x="523" y="{y + 39}" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle" font-family="SFMono-Regular,Consolas,Monaco,monospace">{escape(label.upper())}</text>
  <text x="574" y="{y + 30}" fill="#f8fafc" font-size="18" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{solved:,} solved</text>
  <text x="574" y="{y + 52}" fill="#91a3bd" font-size="13.5" font-family="Segoe UI,Arial,sans-serif">{remaining:,} remaining of {total:,}</text>
  <rect x="716" y="{y + 22}" width="126" height="12" rx="6" fill="#152239" />
  <rect x="716" y="{y + 22}" width="{fill_width:.2f}" height="12" rx="6" fill="url(#{gradient_id})" />
  <text x="842" y="{y + 56}" fill="{theme['end']}" font-size="15" font-weight="700" text-anchor="end" font-family="Segoe UI,Arial,sans-serif">{percent:.2f}%</text>
    """


def build_readme_section(data: dict[str, Any]) -> str:
    rows = [
        ("Easy", data["easySolved"], data["totalEasy"]),
        ("Medium", data["mediumSolved"], data["totalMedium"]),
        ("Hard", data["hardSolved"], data["totalHard"]),
        ("Total", data["totalSolved"], data["totalQuestions"]),
    ]

    table_rows = "\n".join(
        f"""<tr>
  <td>{label}</td>
  <td><b>{solved:,}</b></td>
  <td>{total:,}</td>
  <td>{completion_rate(solved, total):.2f}%</td>
</tr>"""
        for label, solved, total in rows
    )

    return f"""<!-- LEETCODE_STATS:START -->
<div align="center">
  <img src="./images/leetcode_dashboard.svg" width="100%" alt="LeetCode dashboard" />
</div>

<div align="center">
  <img src="./images/total_solved.svg" width="49%" alt="Total solved progress" />
  <img src="./images/easy_solved.svg" width="49%" alt="Easy solved progress" />
</div>
<div align="center">
  <img src="./images/medium_solved.svg" width="49%" alt="Medium solved progress" />
  <img src="./images/hard_solved.svg" width="49%" alt="Hard solved progress" />
</div>

<table>
  <tr>
    <th>Difficulty</th>
    <th>Solved</th>
    <th>Total</th>
    <th>Completion</th>
  </tr>
  {table_rows}
</table>

<p align="center">
  <sub>Last refresh: {escape(data['lastUpdated'])} | Source: official LeetCode GraphQL | Synced via GitHub Actions</sub>
</p>
<!-- LEETCODE_STATS:END -->"""


def update_readme(data: dict[str, Any]) -> None:
    start_marker = "<!-- LEETCODE_STATS:START -->"
    end_marker = "<!-- LEETCODE_STATS:END -->"
    new_section = build_readme_section(data)

    if README_PATH.exists():
        content = README_PATH.read_text(encoding="utf-8")
    else:
        content = "# LeetCode Dashboard\n"

    if start_marker in content and end_marker in content:
        start_index = content.index(start_marker)
        end_index = content.index(end_marker) + len(end_marker)
        updated = content[:start_index] + new_section + content[end_index:]
    else:
        updated = content.rstrip() + "\n\n" + new_section + "\n"

    README_PATH.write_text(updated, encoding="utf-8")


def generate_assets(data: dict[str, Any]) -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    build_progress_card(
        "Total Solved",
        data["totalSolved"],
        data["totalQuestions"],
        IMAGES_DIR / "total_solved.svg",
        CARD_THEMES["Total Solved"],
    )
    build_progress_card(
        "Easy",
        data["easySolved"],
        data["totalEasy"],
        IMAGES_DIR / "easy_solved.svg",
        CARD_THEMES["Easy"],
    )
    build_progress_card(
        "Medium",
        data["mediumSolved"],
        data["totalMedium"],
        IMAGES_DIR / "medium_solved.svg",
        CARD_THEMES["Medium"],
    )
    build_progress_card(
        "Hard",
        data["hardSolved"],
        data["totalHard"],
        IMAGES_DIR / "hard_solved.svg",
        CARD_THEMES["Hard"],
    )
    build_dashboard(data, IMAGES_DIR / "leetcode_dashboard.svg")


def main() -> None:
    print(f"[INFO] Fetching LeetCode stats for {LEETCODE_USERNAME} from official GraphQL...")
    data = fetch_leetcode_stats(LEETCODE_USERNAME)
    generate_assets(data)
    update_readme(data)
    print("[INFO] README and SVG dashboard updated successfully.")


if __name__ == "__main__":
    main()
