# JobiFC — Your Personal AI Football Coach

**A match reflection and practice companion built for Jobi Anand.** Log a few match stats, work toward Jobi’s stated finishing goal, and ask a coach that can ground its answer in recent match data.

> This is a personal practice aid, not a scouting system, medical tool, or replacement for Jobi's real coach. Its small performance scores are simple indicators from the stats entered, not objective player ratings.

## What it does

- Record match date, opponent, position, minutes, goals, assists, shots, pass completion, tackles, and a short personal note.
- Import match rows from CSV.
- Show a latest-match snapshot and keep the coaching focus aligned with Jobi’s stated priority, finishing by default.
- Ask a football practice question. The backend sends recent match data to an Ollama-compatible Gemma endpoint; if the endpoint is unreachable, it provides a clearly labeled deterministic coaching fallback.
- Keep match data in a local JSON file for the MVP.

## Run locally

Requires Python 3.10+ and (optionally) [Ollama](https://ollama.com/) for Gemma inference.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

For the Gemma path, install Ollama and pull the model configured in `.env.example`:

```bash
ollama pull gemma3:4b
ollama serve
```

Then, in another terminal:

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Without Ollama, the match tracker still works and the coach returns its labeled fallback. Set `GEMMA_API_URL`, `GEMMA_MODEL`, `PLAYER_FOCUS`, and optionally `GEMMA_TIMEOUT_SECONDS` to use another Ollama-compatible endpoint.

## CSV format

The first row must contain these headers: `player,date,opponent,position,minutes,goals,assists,shots,shots_on_target,passes_attempted,passes_completed,tackles`. `self_note` is optional. A ready-to-import two-match example is in `data/sample_matches.csv`.

## Deploying on Render

The app can run as a Render web service, but the model endpoint must be reachable from that service. A model running at `localhost` on your laptop is not reachable by Render. Configure `GEMMA_API_URL` and `GEMMA_MODEL` with a secured, reachable Ollama-compatible Gemma endpoint; keep credentials in Render environment variables. For a demo that does not have a hosted endpoint, the app remains usable and marks the coaching fallback clearly. The provided Render Blueprint does not attach a paid disk, so hosted JSON match history may reset on redeploy or restart. For persistent hosted history, attach a Render disk and point `DATA_FILE` inside its mount path; Render persistent disks are available on paid services. Do not rely on the JSON file for multi-user storage.

A `render.yaml` Blueprint is included. Connect the repository as a Render Blueprint and set `GEMMA_API_URL` to a reachable endpoint in the service environment. The default Ollama URL points to the app container itself and will not connect to Ollama on your laptop.

Suggested Render settings:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

## Architecture

```text
Browser (HTML/CSS/JS)
   ├── POST /api/matches and /api/import ──> FastAPI validation ──> local JSON
   ├── GET /api/analysis ──────────────────> transparent stat calculations
   └── POST /api/coach ────────────────────> recent stats + question
                                               ├── Ollama-compatible Gemma
                                               └── labeled local fallback
```

The model call is isolated in `gemma()` in `app/main.py`. The browser and analysis functions do not depend on a particular model provider, so a hosted or local Gemma endpoint can be swapped without changing the UI.

## Verify

```bash
python -m unittest discover -s tests -v
```

## Demo in 90 seconds

1. Open the app and introduce it as a match reflection tool made for Jobi, not a generic chatbot.
2. Import `data/sample_matches.csv` or enter a match in the form.
3. Point out the latest-match snapshot and explain that its metrics use only the stats Jobi entered.
4. Ask “What should I focus on in my next training session?” Show the source label: Gemma when connected, fallback otherwise.
5. Add one new match and show how the displayed focus changes with the latest stats.

## Challenge story and DEV submission notes

### The person and problem

Jobi Anand is the person this project is for. JobiFC is designed around a small but real gap after a game: remembering what happened is easier than turning scattered match stats into one useful next step. The app gives Jobi a place to record his own performance and reflect on it.

Jobi said finishing is the area he especially wants to improve. After trying the finishing drill, he said it fits him. Don't imply a broader endorsement beyond that feedback.

### Why open innovation matters

The app can run an open-weight Gemma model through a local Ollama endpoint. That makes the model layer inspectable and replaceable, and lets the developer prototype without making the whole product depend on one proprietary chatbot. Recent match stats are supplied as context so the model's advice can respond to Jobi's own match. The local fallback also keeps match logging and basic feedback available when the model is offline.

### Architecture and demo

Use the architecture diagram and five demo steps above. Be transparent in the article about which endpoint actually ran during the demo. If Gemma is not connected, describe the fallback accurately and do not present its output as Gemma-generated.

### Partner categories

- **Gemma:** only claim this category if you run a Gemma model for the demonstrated coaching flow and can show that integration in the code/demo.
- **Render:** only claim this category if you deploy JobiFC on Render and show the live app. Deployment alone should not be described as meaningful model hosting; explain the actual endpoint setup.
- Mention no other partner category unless the final app genuinely uses that partner's technology.

## Project story draft

> My friend Jobi Anand is the reason I built JobiFC. After a match, a player can remember the score but still struggle to turn their own performance into a simple training focus. I wanted to make a small tool that helps Jobi record what happened, notice one area to work on, and ask a coach a grounded follow-up question.
>
> The app combines a lightweight FastAPI backend with a simple browser UI. Its performance snapshot is calculated from the stats Jobi enters. For coaching, the backend can send those stats and Jobi's question to an open-weight Gemma model through Ollama. Keeping that model boundary small means the model can run locally and be replaced without rewriting the rest of the app. When Gemma is unavailable, the app says so and uses a clearly labeled fallback.
>
> The point of using open model tooling is practical: I can see how the model is called, choose where inference happens, and keep the product small enough to adapt around one person's needs. JobiFC is an early prototype, and the next improvement should come from Jobi trying it and telling me which reflection or drill actually helps.
>
> **Before submitting:** add the exact Gemma model/provider used in the demo and the live demo and repository links. Do not claim deployment or model use that did not happen.
