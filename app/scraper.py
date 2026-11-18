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

def normalize_name(name: str) -> str:
    # Roster notes in parentheses are annotations, not part of the in-game name.
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip().casefold()

def classify_guild(name: str, rosters=None) -> str:
    rosters = rosters or load_rosters()
    key = normalize_name(name)
    enemy = {normalize_name(x) for x in rosters["enemy"]}
    ally = {normalize_name(x) for x in rosters["ally"]}
    if key in enemy: return "enemy"
    if key in ally: return "ally"
    return "unknown"

def parse_time(text: str):
    for fmt in ("%d.%m.%Y, %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try: return datetime.strptime(text.strip(), fmt)
        except ValueError: pass
    return None

def parse_deaths(html: str):
    """Parse Aurera's numbered latest-deaths list, not unrelated page tables."""
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    date_re = re.compile(r"\b(\d{2}\.\d{2}\.\d{4},\s*\d{2}:\d{2}:\d{2})\b")
    level_re = re.compile(r"\bno level\s+(\d{1,5})\b", re.I)
    for item in soup.find_all(True):
        raw = " ".join(item.stripped_strings)
        date_matches, level_matches = date_re.findall(raw), level_re.findall(raw)
        # Ancestor wrappers can contain multiple deaths; only accept one-event fragments.
        if len(date_matches) != 1 or len(level_matches) != 1: continue
        links = [a.get_text(" ", strip=True) for a in item.find_all("a") if a.get_text(" ", strip=True)]
        if not links: continue
        victim = links[0].strip()
        if len(victim) > 120: continue
        key = hashlib.sha256(raw.casefold().encode("utf-8")).hexdigest()
        if key in seen: continue
        seen.add(key)
        results.append({"source_key": key, "victim": victim, "level": int(level_matches[0]),
                        "killer": ", ".join(links[1:]) or None,
                        "happened_at": parse_time(date_matches[0]),
                        "guild": classify_guild(victim), "raw_text": raw[:2000]})
    return results

async def fetch_deaths():
    headers = {"User-Agent": "DeathRadarAurera/1.0 (+monitoring dashboard)"}
    async with httpx.AsyncClient(timeout=25, follow_redirects=True, headers=headers) as client:
        response = await client.get(settings.deaths_url)
        response.raise_for_status()
    return parse_deaths(response.text)
