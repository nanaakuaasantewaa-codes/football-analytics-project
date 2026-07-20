# World Cup Stat Bot

Streamlit app that turns completed FIFA World Cup 2026 matches into
@OptaAnalystUS-style charts + captions, ready to post manually on X.

## Setup (one time)

1. Unzip this folder, open a terminal inside `worldcup_bot/`.

2. Create and activate a virtual environment:

   macOS / Linux:
       python3 -m venv .venv
       source .venv/bin/activate

   Windows (PowerShell):
       python -m venv .venv
       .venv\Scripts\Activate.ps1

   Windows (cmd.exe):
       python -m venv .venv
       .venv\Scripts\activate.bat

   (Requires Python 3.10+. Check with: python --version)

3. Install dependencies:
       pip install --upgrade pip
       pip install requests pandas matplotlib python-dotenv streamlit pillow

4. Open `.env` and replace the placeholder with your real API-Football key:
       FOOTBALL_API_KEY=your_actual_key

5. Verify the key:
       python -c "from api_client import verify_api_key; print(verify_api_key())"

## Running

    python launch.py

or double-click `start.sh` (macOS/Linux) / `start.bat` (Windows).
The UI opens at http://localhost:8501.

## Offline self-test (no API key needed)

    python smoke_test.py

Exercises all 5 analysis types and all 6 chart types with mocked data,
writing sample charts to `output/`.

## Workflow in the UI

1. Sidebar → "Check API key" to confirm your key works.
2. "Load today's fixtures" → note a completed (✅) fixture ID.
3. Enter the fixture ID, pick an analysis type, click "Load Match & Analyse".
4. Pick a ranked candidate → "Generate / Refresh Chart".
5. Download chart.png, copy the caption, post on X manually.

Outputs are also saved to `output/<date>_<TEAMA>_<TEAMB>/chart.png` and
`caption.txt`.

## Windows note

`.vscode/settings.json` points the interpreter at `.venv/bin/python`.
On Windows, change it to: `${workspaceFolder}\\.venv\\Scripts\\python.exe`

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| FOOTBALL_API_KEY not found | .env missing/empty | Open .env, add key, save |
| HTTP 401 | Key invalid/inactive | Check API-Football dashboard |
| No fixture found for ID | Wrong ID | Re-run "Load today's fixtures" |
| Fixture not finished yet | Match in progress | Wait for FT, retry |
| No statistics available | Stats not published yet | Wait 10-15 min after FT |
| ModuleNotFoundError | Venv not activated | Re-run activate script |
| Port 8501 in use | Another Streamlit running | streamlit run ui.py --server.port 8502 |
