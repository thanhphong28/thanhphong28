import datetime as dt
import html
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTRAIT_JSON = ROOT / "scripts" / "portrait_data.json"
OUT_SVG = ROOT / "assets" / "neofetch.svg"
USERNAME = os.environ.get("GITHUB_USERNAME", "thanhphong28")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ACCOUNT_CREATED = dt.date(2022, 4, 3)


def compute_uptime(start: dt.date, today: dt.date) -> str:
    years = today.year - start.year
    months = today.month - start.month
    days = today.day - start.day
    if days < 0:
        months -= 1
        prev_month = (today.replace(day=1) - dt.timedelta(days=1)).day
        days += prev_month
    if months < 0:
        years -= 1
        months += 12
    return f"{years}y {months}m {days}d"


def fetch_github_stats() -> dict:
    fallback = {
        "public_repos": 14,
        "total_repos": 17,
        "contributions_year": 147,
        "stars": 1,
    }
    if not GITHUB_TOKEN:
        return fallback
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(ownerAffiliations: OWNER, first: 100) {
          totalCount
          nodes { isPrivate stargazerCount }
        }
        contributionsCollection {
          contributionCalendar { totalContributions }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": USERNAME}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "breeze-neofetch-action",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))["data"]["user"]
        nodes = data["repositories"]["nodes"]
        return {
            "public_repos": sum(1 for n in nodes if not n["isPrivate"]),
            "total_repos": data["repositories"]["totalCount"],
            "contributions_year": data["contributionsCollection"]["contributionCalendar"]["totalContributions"],
            "stars": sum(n["stargazerCount"] for n in nodes),
        }
    except Exception:
        return fallback


def render_svg() -> str:
    portrait = json.loads(PORTRAIT_JSON.read_text(encoding="utf-8"))
    stats = fetch_github_stats()
    today_vn = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=7)).date()
    uptime = compute_uptime(ACCOUNT_CREATED, today_vn)
    synced = today_vn.strftime("%Y-%m-%d")

    # Build crisp TrueColor Terminal Pixel-Block Portrait (chafa / kitty neofetch style)
    portrait_els = [
        '    <rect x="30" y="84" width="316" height="316" rx="10" fill="#1A1E26" stroke="#272C36" stroke-width="1" />'
    ]
    cell = 6.8
    ox = 38.4
    oy = 92.4
    for r_idx, runs in enumerate(portrait["rows_out"]):
        py = oy + r_idx * cell
        for col, span_len, color in runs:
            px = ox + col * cell
            pw = span_len * cell + 0.25
            ph = cell + 0.25
            portrait_els.append(
                f'    <rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="{color}" />'
            )
    ascii_block = "\n".join(portrait_els)

    # Right column neofetch rows
    info_rows = [
        ("section", "thanhphong28@github", None),
        ("rule", "────────────────────────────────────────────────", None),
        ("kv", "Name", "Nguyễn Thanh Phong (Breeze Boy)"),
        ("kv", "Role", "Frontend Software Engineer @ 315 Medical"),
        ("kv", "Impact", "EMR Platform serving ~200 clinics in Vietnam"),
        ("kv", "Lead Exp", "Ex-Team Lead @ VNA Group (5 engineers)"),
        ("kv", "Education", "B.Eng. Software Engineering · Saigon Univ (SGU)"),
        ("kv", "Certs", "Google UX Design · Google AI · TOEIC"),
        ("kv", "Location", "Ho Chi Minh City, Vietnam (GMT+7)"),
        ("spacer", "", None),
        ("sub", "── Live GitHub Telemetry ───────────────────────", None),
        ("kv", "Uptime", f"{uptime}  (since Apr 2022)"),
        ("kv", "Repos", f"{stats['public_repos']} public  ·  {stats['total_repos']} total"),
        ("kv", "Activity", f"{stats['contributions_year']} contributions (past 12 months)"),
        ("kv", "Stack", "React · Next.js · TypeScript · NestJS · Kotlin"),
        ("kv", "Web", "thanhphong28.github.io"),
    ]

    info_els = []
    iy = 96.0
    step = 17.8
    for idx, (kind, k, v) in enumerate(info_rows):
        delay = 0.25 + idx * 0.045
        if kind == "section":
            info_els.append(
                f'    <text x="394" y="{iy:.1f}" class="mono bold fade" style="animation-delay:{delay:.2f}s">'
                f'<tspan fill="#39D353">thanhphong28</tspan><tspan fill="#6E7681">@</tspan>'
                f'<tspan fill="#E6EDF3">github</tspan></text>'
            )
        elif kind == "rule":
            info_els.append(
                f'    <text x="394" y="{iy:.1f}" class="mono muted fade" style="animation-delay:{delay:.2f}s">{k}</text>'
            )
        elif kind == "sub":
            info_els.append(
                f'    <text x="394" y="{iy:.1f}" class="mono sub fade" style="animation-delay:{delay:.2f}s">{k}</text>'
            )
        elif kind == "spacer":
            iy -= 7.0
        elif kind == "kv":
            key_pad = html.escape(f"{k:<11}").replace(" ", "&#160;")
            val_esc = html.escape(v)
            val_cls = "val-hi" if k in ("Role", "Uptime", "Activity") else "val"
            info_els.append(
                f'    <text x="394" y="{iy:.1f}" class="mono fade" style="animation-delay:{delay:.2f}s">'
                f'<tspan class="key">{key_pad}</tspan><tspan class="{val_cls}">{val_esc}</tspan></text>'
            )
        iy += step
    info_block = "\n".join(info_els)

    # Classic macOS Terminal 8-color swatch bar
    swatches = ["#21262D", "#F85149", "#39D353", "#D29922", "#58A6FF", "#BC8CFF", "#39C5CF", "#E6EDF3"]
    swatch_els = "\n".join(
        f'    <rect x="{394 + i * 26}" y="388" width="20" height="12" rx="3" fill="{c}" />'
        for i, c in enumerate(swatches)
    )

    return f"""<svg width="920" height="432" viewBox="0 0 920 432" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="macOS Terminal neofetch for Nguyễn Thanh Phong (Breeze Boy)">
  <defs>
    <linearGradient id="winBar" x1="0" y1="0" x2="0" y2="38" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#1E222A" />
      <stop offset="100%" stop-color="#161920" />
    </linearGradient>
    <clipPath id="winClip">
      <rect x="1" y="1" width="918" height="430" rx="13" />
    </clipPath>
  </defs>

  <style>
    .titlebar {{
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
      font-size: 12.5px;
      font-weight: 500;
      fill: #8B949E;
    }}
    .mono {{
      font-family: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
      font-size: 12.5px;
    }}
    .ascii {{
      font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
      font-size: 11px;
      letter-spacing: 0.4px;
    }}
    .bold {{ font-weight: 700; font-size: 13.5px; }}
    .muted {{ fill: #30363D; }}
    .sub {{ fill: #6E7681; font-size: 12px; }}
    .key {{ fill: #7D8590; font-weight: 600; }}
    .val {{ fill: #C9D1D9; }}
    .val-hi {{ fill: #F0F6FC; font-weight: 600; }}
    .fade {{
      opacity: 0;
      animation: fadeIn 0.35s ease-out forwards;
    }}
    .portrait-fade {{
      opacity: 0;
      animation: fadeIn 0.65s ease-out 0.15s forwards;
    }}
    .cursor {{
      animation: blink 1.05s steps(2, start) infinite;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(3px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes blink {{
      0%, 49% {{ opacity: 1; }}
      50%, 100% {{ opacity: 0; }}
    }}
  </style>

  <g clip-path="url(#winClip)">
    <!-- Terminal Body -->
    <rect x="0" y="0" width="920" height="432" fill="#121418" />

    <!-- macOS Titlebar -->
    <rect x="0" y="0" width="920" height="38" fill="url(#winBar)" />
    <line x1="0" y1="38" x2="920" y2="38" stroke="#252A33" stroke-width="1" />

    <!-- Traffic Lights -->
    <circle cx="22" cy="19" r="6" fill="#FF5F56" />
    <circle cx="42" cy="19" r="6" fill="#FFBD2E" />
    <circle cx="62" cy="19" r="6" fill="#27C93F" />

    <!-- Window Title -->
    <text x="460" y="23" text-anchor="middle" class="titlebar">breezeboy@macbook-pro — zsh — neofetch</text>
    <text x="896" y="23" text-anchor="end" class="mono" style="font-size:10.5px" fill="#484F58">synced {synced}</text>

    <!-- Shell Command Line -->
    <text x="26" y="66" class="mono">
      <tspan fill="#39D353" font-weight="700">➜</tspan>
      <tspan fill="#58A6FF" font-weight="600"> ~</tspan>
      <tspan fill="#E6EDF3"> neofetch --profile</tspan>
    </text>

    <!-- Subtle vertical divider between portrait and specs -->
    <line x1="370" y1="84" x2="370" y2="404" stroke="#1E232B" stroke-width="1" />

    <!-- TrueColor ASCII Portrait -->
    <g class="portrait-fade">
{ascii_block}
    </g>

    <!-- Live Neofetch Readout -->
{info_block}

    <!-- Terminal Palette Swatches -->
{swatch_els}

    <!-- Interactive Blinking Cursor Prompt -->
    <text x="616" y="399" class="mono">
      <tspan fill="#39D353" font-weight="700">➜</tspan>
      <tspan fill="#58A6FF" font-weight="600"> ~</tspan>
      <tspan fill="#6E7681"> _</tspan>
    </text>
    <rect class="cursor" x="653" y="388" width="7" height="13" rx="1.5" fill="#39D353" />
  </g>

  <!-- Crisp macOS Window Hairline Border -->
  <rect x="1" y="1" width="918" height="430" rx="13" stroke="#272B33" stroke-width="1.25" />
</svg>
"""


if __name__ == "__main__":
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    svg = render_svg()
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"Generated {OUT_SVG} ({len(svg)} bytes)")
