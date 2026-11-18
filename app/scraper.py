import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
from app.config import settings

ROSTER_PATH = Path("data/rosters.json")

def load_rosters():
    try:
        data = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
        return {"ally": {str(x).strip().casefold() for x in data.get("ally", [])},
                "enemy": {str(x).strip().casefold() for x in data.get("enemy", [])}}
    except (OSError, ValueError, TypeError):
        return {"ally": set(), "enemy": set()}

def classify_guild(name: str, rosters=None) -> str:
    rosters = rosters or load_rosters()
    key = name.strip().casefold()
    if key in rosters["enemy"]: return "enemy"
    if key in rosters["ally"]: return "ally"
    return "unknown"

def parse_time(text: str):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try: return datetime.strptime(text.strip(), fmt)
        except ValueError: pass
    return None

def parse_deaths(html: str):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"], recursive=False)
            if len(cells) < 2: continue
            raw = " ".join(tr.stripped_strings)
            links = [a.get_text(" ", strip=True) for a in tr.find_all("a") if a.get_text(" ", strip=True)]
            if not raw or not links: continue
            victim = links[0].strip()
            if len(victim) > 120 or not re.search(r"[A-Za-z]", victim): continue
            level_match = re.search(r"\b(?:level\s*)?(\d{1,5})\b", raw, re.I)
            level = int(level_match.group(1)) if level_match else None
            date_match = re.search(r"\b(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}(?::\d{2})?|\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\b", raw)
            happened_at = parse_time(date_match.group(1)) if date_match else None
            killer = ", ".join(links[1:]) if len(links) > 1 else None
            key = hashlib.sha256(f"{raw}|{victim}".casefold().encode("utf-8")).hexdigest()
            results.append({"source_key": key, "victim": victim, "level": level, "killer": killer,
                            "happened_at": happened_at, "guild": classify_guild(victim), "raw_text": raw[:2000]})
    return results

async def fetch_deaths():
    headers = {"User-Agent": "DeathRadarAurera/1.0 (+monitoring dashboard)"}
    async with httpx.AsyncClient(timeout=25, follow_redirects=True, headers=headers) as client:
        response = await client.get(settings.deaths_url)
        response.raise_for_status()
    return parse_deaths(response.text)
