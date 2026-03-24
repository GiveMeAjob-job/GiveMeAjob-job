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
        "caption": "Overall progress across the full LeetCode problem set.",
    },
    "Easy": {
        "start": "#22c55e",
        "end": "#84cc16",
        "soft": "#132a1d",
        "badge": "E",
        "caption": "Warm-up reps that keep the fundamentals sharp.",
    },
    "Medium": {
        "start": "#f59e0b",
        "end": "#f97316",
        "soft": "#2f2008",
        "badge": "M",
        "caption": "Core interview territory and the main growth lane.",
    },
    "Hard": {
        "start": "#ef4444",
        "end": "#ec4899",
        "soft": "#301019",
        "badge": "H",
        "caption": "Stretch problems that build deeper problem-solving range.",
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


def completion_rate(solved: int, total: int) -> float:
    if not total:
        return 0.0
    return solved / total * 100


def progress_bar_width(percent: float, max_width: float, min_width: float) -> float:
    if percent <= 0:
        return 0.0
    return min(max_width, max(max_width * percent / 100, min_width))


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
    fill_width = progress_bar_width(percent, max_width=280, min_width=24)
    gradient_id = f"{filename.stem.replace('-', '_')}_gradient"
    glow_id = f"{filename.stem.replace('-', '_')}_glow"
    safe_title = escape(title)
    safe_caption = escape(theme["caption"])

    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="420" height="140" viewBox="0 0 420 140" role="img" aria-labelledby="{filename.stem}_title {filename.stem}_desc">
  <title id="{filename.stem}_title">{safe_title} progress card</title>
  <desc id="{filename.stem}_desc">{safe_title}: {solved} solved out of {total} total problems.</desc>
  <defs>
    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{theme['start']}" />
      <stop offset="100%" stop-color="{theme['end']}" />
    </linearGradient>
    <filter id="{glow_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="12" result="blur" />
      <feColorMatrix
        in="blur"
        type="matrix"
        values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.35 0"
      />
    </filter>
  </defs>
  <rect width="420" height="140" rx="22" fill="#081120" />
  <rect x="1" y="1" width="418" height="138" rx="21" fill="#0d172a" stroke="#1f2b45" />
  <circle cx="360" cy="28" r="34" fill="{theme['start']}" opacity="0.18" filter="url(#{glow_id})" />
  <rect x="24" y="24" width="56" height="56" rx="16" fill="{theme['soft']}" />
  <text x="52" y="58" fill="white" font-size="26" font-weight="700" text-anchor="middle" font-family="SFMono-Regular,Consolas,Monaco,monospace">{escape(theme['badge'])}</text>
  <text x="100" y="44" fill="#e2e8f0" font-size="18" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{safe_title}</text>
  <text x="100" y="73" fill="white" font-size="27" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{solved:,}</text>
  <text x="170" y="73" fill="#94a3b8" font-size="16" font-family="Segoe UI,Arial,sans-serif">/ {total:,}</text>
  <text x="380" y="44" fill="{theme['end']}" font-size="16" font-weight="700" text-anchor="end" font-family="Segoe UI,Arial,sans-serif">{percent:.2f}%</text>
  <rect x="100" y="92" width="280" height="14" rx="7" fill="#162237" />
  <rect x="100" y="92" width="{fill_width:.2f}" height="14" rx="7" fill="url(#{gradient_id})" />
  <text x="24" y="122" fill="#94a3b8" font-size="13" font-family="Segoe UI,Arial,sans-serif">{safe_caption}</text>
</svg>
    """
    write_text(filename, svg)


def build_dashboard(data: dict[str, Any], filename: Path) -> None:
    total_percent = completion_rate(data["totalSolved"], data["totalQuestions"])
    easy_percent = completion_rate(data["easySolved"], data["totalEasy"])
    medium_percent = completion_rate(data["mediumSolved"], data["totalMedium"])
    hard_percent = completion_rate(data["hardSolved"], data["totalHard"])
    acceptance = "n/a" if data["acceptanceRate"] is None else f"{data['acceptanceRate']:.2f}%"
    ranking = "n/a" if data["ranking"] is None else f"#{data['ranking']:,}"

    rows = [
        dashboard_row("Easy", data["easySolved"], data["totalEasy"], easy_percent, 112, "#22c55e", "#84cc16"),
        dashboard_row("Medium", data["mediumSolved"], data["totalMedium"], medium_percent, 168, "#f59e0b", "#f97316"),
        dashboard_row("Hard", data["hardSolved"], data["totalHard"], hard_percent, 224, "#ef4444", "#ec4899"),
    ]

    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320" viewBox="0 0 900 320" role="img" aria-labelledby="dashboard_title dashboard_desc">
  <title id="dashboard_title">LeetCode dashboard for {escape(data['username'])}</title>
  <desc id="dashboard_desc">A visual summary of solved problems, completion percentages, acceptance rate, and ranking.</desc>
  <defs>
    <linearGradient id="dashboard_bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#07111f" />
      <stop offset="55%" stop-color="#0b1328" />
      <stop offset="100%" stop-color="#111827" />
    </linearGradient>
    <linearGradient id="dashboard_accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f97316" />
      <stop offset="100%" stop-color="#14b8a6" />
    </linearGradient>
    <pattern id="dashboard_grid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M 28 0 L 0 0 0 28" fill="none" stroke="#1e293b" stroke-width="1" opacity="0.35" />
    </pattern>
  </defs>
  <rect width="900" height="320" rx="28" fill="url(#dashboard_bg)" />
  <rect width="900" height="320" rx="28" fill="url(#dashboard_grid)" />
  <circle cx="774" cy="60" r="74" fill="#f97316" opacity="0.10" />
  <circle cx="842" cy="266" r="94" fill="#14b8a6" opacity="0.08" />
  <rect x="24" y="24" width="852" height="272" rx="24" fill="#0a1324" fill-opacity="0.86" stroke="#1f2b45" />

  <text x="48" y="58" fill="#f8fafc" font-size="28" font-weight="700" font-family="Segoe UI,Arial,sans-serif">LeetCode Progress Dashboard</text>
  <text x="48" y="84" fill="#94a3b8" font-size="14" font-family="Segoe UI,Arial,sans-serif">@{escape(data['username'])} | synced with official LeetCode GraphQL</text>

  <text x="48" y="132" fill="#94a3b8" font-size="14" letter-spacing="1.1" font-family="SFMono-Regular,Consolas,Monaco,monospace">TOTAL SOLVED</text>
  <text x="48" y="182" fill="white" font-size="52" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{data['totalSolved']:,}</text>
  <text x="158" y="182" fill="#94a3b8" font-size="22" font-family="Segoe UI,Arial,sans-serif">/ {data['totalQuestions']:,}</text>
  <rect x="48" y="204" width="320" height="16" rx="8" fill="#162237" />
  <rect x="48" y="204" width="{progress_bar_width(total_percent, max_width=320, min_width=28):.2f}" height="16" rx="8" fill="url(#dashboard_accent)" />
  <text x="48" y="248" fill="#e2e8f0" font-size="18" font-family="Segoe UI,Arial,sans-serif">{total_percent:.2f}% of all public problems completed</text>

  <rect x="48" y="264" width="156" height="48" rx="18" fill="#111c30" stroke="#1f2b45" />
  <text x="64" y="286" fill="#94a3b8" font-size="12" letter-spacing="0.8" font-family="SFMono-Regular,Consolas,Monaco,monospace">ACCEPTANCE</text>
  <text x="64" y="304" fill="white" font-size="22" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{acceptance}</text>

  <rect x="220" y="264" width="200" height="48" rx="18" fill="#111c30" stroke="#1f2b45" />
  <text x="236" y="286" fill="#94a3b8" font-size="12" letter-spacing="0.8" font-family="SFMono-Regular,Consolas,Monaco,monospace">GLOBAL RANK</text>
  <text x="236" y="304" fill="white" font-size="22" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{ranking}</text>

  <text x="470" y="58" fill="#94a3b8" font-size="14" letter-spacing="1" font-family="SFMono-Regular,Consolas,Monaco,monospace">DIFFICULTY BREAKDOWN</text>
  {''.join(rows)}
  <text x="470" y="282" fill="#94a3b8" font-size="13" font-family="Segoe UI,Arial,sans-serif">Last refresh: {escape(data['lastUpdated'])}</text>
  <text x="470" y="302" fill="#64748b" font-size="12" font-family="Segoe UI,Arial,sans-serif">Generated automatically by Python + GitHub Actions.</text>
</svg>
    """
    write_text(filename, svg)


def dashboard_row(label: str, solved: int, total: int, percent: float, y: int, start: str, end: str) -> str:
    fill_width = progress_bar_width(percent, max_width=260, min_width=20)
    gradient_id = f"{label.lower()}_dashboard_gradient"
    return f"""
  <defs>
    <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{start}" />
      <stop offset="100%" stop-color="{end}" />
    </linearGradient>
  </defs>
  <text x="470" y="{y}" fill="#e2e8f0" font-size="18" font-weight="700" font-family="Segoe UI,Arial,sans-serif">{escape(label)}</text>
  <text x="792" y="{y}" fill="#94a3b8" font-size="16" text-anchor="end" font-family="Segoe UI,Arial,sans-serif">{solved:,} / {total:,}</text>
  <rect x="470" y="{y + 18}" width="260" height="14" rx="7" fill="#162237" />
  <rect x="470" y="{y + 18}" width="{fill_width:.2f}" height="14" rx="7" fill="url(#{gradient_id})" />
  <text x="792" y="{y + 31}" fill="{end}" font-size="14" font-weight="700" text-anchor="end" font-family="Segoe UI,Arial,sans-serif">{percent:.2f}%</text>
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
