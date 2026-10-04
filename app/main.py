from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env")
DATA_FILE = Path(os.getenv("DATA_FILE", str(ROOT.parent / "data" / "matches.json")))
GEMMA_API_URL = os.getenv("GEMMA_API_URL", "http://localhost:11434/api/chat")
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma3:4b")
TIMEOUT = float(os.getenv("GEMMA_TIMEOUT_SECONDS", "45"))
PLAYER_FOCUS = os.getenv("PLAYER_FOCUS", "finishing").strip().lower()

app = FastAPI(title="JobiFC", description="A personal football coach for Jobi Anand")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class Match(BaseModel):
    player: str = Field(default="Jobi Anand", max_length=80)
    date: str = Field(default="", max_length=20)
    opponent: str = Field(default="", max_length=80)
    position: str = Field(default="Midfielder", max_length=40)
    minutes: int = Field(ge=1, le=150)
    goals: int = Field(ge=0, le=20)
    assists: int = Field(ge=0, le=20)
    shots: int = Field(ge=0, le=100)
    shots_on_target: int = Field(ge=0, le=100)
    passes_attempted: int = Field(ge=0, le=300)
    passes_completed: int = Field(ge=0, le=300)
    tackles: int = Field(ge=0, le=100)
    self_note: str = Field(default="", max_length=500)

    @classmethod
    def checked(cls, raw: dict[str, Any]) -> "Match":
        match = cls(**raw)
        if match.passes_completed > match.passes_attempted:
            raise ValueError("Completed passes cannot exceed passes attempted.")
        if match.shots_on_target > match.shots:
            raise ValueError("Shots on target cannot exceed total shots.")
        return match


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


def load_matches() -> list[dict[str, Any]]:
    try:
        return json.loads(DATA_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_matches(rows: list[dict[str, Any]]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(rows[-100:], indent=2))


def metrics(m: dict[str, Any]) -> dict[str, float]:
    passes = m["passes_attempted"]
    shots = m["shots"]
    return {
        "pass_accuracy": round(100 * m["passes_completed"] / passes) if passes else 0,
        "shot_accuracy": round(100 * m["shots_on_target"] / shots) if shots else 0,
        "goal_contributions": m["goals"] + m["assists"],
    }


def insights(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"matches": 0, "scores": {}, "focus": "Log a match to get your first coaching insight.", "trend": []}
    latest = rows[-1]
    m = metrics(latest)
    scores = {
        "Passing": min(100, m["pass_accuracy"]),
        "Finishing": min(100, m["shot_accuracy"]),
        "Defending": min(100, latest["tackles"] * 12),
    }
    focus_ids = {"passing": "Passing", "finishing": "Finishing", "defending": "Defending"}
    chosen_id = focus_ids.get(PLAYER_FOCUS)
    selected = chosen_id or min(scores, key=scores.get)
    names = {"Passing": "passing under pressure", "Finishing": "finishing", "Defending": "defensive timing"}
    return {"matches": len(rows), "scores": scores, "focus": names[selected], "trend": rows[-5:], "latest_metrics": m}


async def gemma(prompt: str, system: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(GEMMA_API_URL, json={
                "model": GEMMA_MODEL,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.4},
            })
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "").strip() or None
    except (httpx.HTTPError, ValueError, KeyError):
        return None


def fallback_coach(rows: list[dict[str, Any]]) -> str:
    s = insights(rows)
    if not rows:
        return "Start by logging one match. Add your minutes, passing, shots and a note about how you felt."
    drills = {
        "passing under pressure": "Set up two small gates. Complete 3 sets of 8 passes through alternating gates, scanning before each touch.",
        "finishing": "Take 3 sets of 6 controlled shots at a small target in each corner. Focus on placement before power.",
        "defensive timing": "With a partner or coach, practice 3 sets of 6 approaches: slow down, stay balanced, and guide the attacker away from space.",
    }
    return (f"Your chosen focus is {s['focus']}. Try this: {drills[s['focus']]} "
            "Keep the session comfortable and ask your coach to adapt the drill to your fitness and any injury.")


FOCUS_CONFLICTS = {
    "passing under pressure": re.compile(r"\b(finishing|shots?|shooting|creating chances|creativity|defending|defensive)\b", re.I),
    "finishing": re.compile(r"\b(passing|passes|creating chances|creativity|defending|defensive)\b", re.I),
    "defensive timing": re.compile(r"\b(passing|passes|shot placement|finishing|shooting|creating chances|creativity)\b", re.I),
}


@app.get("/")
def home() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/matches")
def get_matches() -> list[dict[str, Any]]:
    return load_matches()


@app.post("/api/matches")
def add_match(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        match = Match.checked(payload).model_dump()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    rows = load_matches()
    rows.append(match)
    save_matches(rows)
    return {"match": match, "analysis": insights(rows)}


@app.post("/api/import")
async def import_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file.")
    try:
        text = (await file.read()).decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        parsed = [Match.checked({k: (int(v) if k in {"minutes", "goals", "assists", "shots", "shots_on_target", "passes_attempted", "passes_completed", "tackles"} else v) for k, v in row.items()}).model_dump() for row in reader]
    except Exception as exc:
        raise HTTPException(422, f"Could not read match CSV: {exc}") from exc
    if not parsed:
        raise HTTPException(422, "The CSV has no match rows.")
    rows = load_matches() + parsed
    save_matches(rows)
    return {"imported": len(parsed), "analysis": insights(rows)}


@app.get("/api/analysis")
def analysis() -> dict[str, Any]:
    return insights(load_matches())


@app.post("/api/coach")
async def coach(request: ChatRequest) -> dict[str, str]:
    rows = load_matches()
    current_analysis = insights(rows)
    system = ("You are JobiFC, a supportive football practice coach for Jobi Anand. Be specific, concise, encouraging, and use the match data. "
              "The app's current analysis is authoritative: use its exact 'focus' as the single next training focus and suggest a drill for that focus only. Do not discuss or recommend another skill area. "
              "Only state facts present in the match data; do not invent match events or claim an action was crucial. Never diagnose injury or recommend unsafe training. If data is missing, say so. Keep answer under 100 words.")
    prompt = (f"Match data: {json.dumps(rows[-5:])}\nCurrent analysis (follow this focus exactly): {json.dumps(current_analysis)}\n"
              f"The one next focus to use is: {current_analysis['focus']}\nQuestion: {request.question}")
    answer = await gemma(prompt, system)
    if answer:
        conflict = FOCUS_CONFLICTS.get(current_analysis["focus"])
        if conflict and conflict.search(answer):
            return {"answer": fallback_coach(rows), "source": "Grounded coaching fallback (Gemma answer conflicted with the selected focus)"}
        return {"answer": answer, "source": "Gemma"}
    return {"answer": fallback_coach(rows), "source": "Local coaching fallback (Gemma unavailable)"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": GEMMA_MODEL, "provider": "Ollama-compatible API"}
