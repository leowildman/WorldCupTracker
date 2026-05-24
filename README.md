# World Cup Tracker

Monitor pub and venue pages for **FIFA World Cup 2026** fixtures and detect when new matches appear or **booking availability changes** (for example, “Walk ins only” becoming “Book Now” with a real link).

The first supported source is [Urban Pubs & Bars](https://www.urbanpubsandbars.com/) venue pages, starting with [Bar Kick at The Shoreditch Arms](https://www.urbanpubsandbars.com/world-cup-2026/bar-kick-at-the-shoreditch-arms).

## How detection works

1. **Fetch** each configured venue URL (respectful `User-Agent`, timeout).
2. **Parse** HTML into normalized `Fixture` records (teams, date/time, booking status, links).
3. **Compare** the current list to the last saved snapshot in `data/`.
4. **Report** new fixtures and booking-status changes; then save the new snapshot (previous snapshot archived under `data/<venue>/history/`).

Booking status is derived from on-page cues: a “walk ins only” notice → `walk_ins_only`; a real booking URL without that notice → `bookable`.

## Requirements

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) for dependencies and running commands
- Optional: Docker for containerized runs

## Setup (uv)

```powershell
cd C:\Users\Wildman\Documents\Code\WorldCupTracker
uv sync --extra dev
```

Copy optional environment overrides:

```powershell
copy .env.example .env
```

Edit `config.yaml` to add or change monitored venues.

## CLI

```powershell
# Fetch all venues, diff against snapshots, save state (exit code 2 if changes)
uv run worldcup-tracker check

# List fixtures from last snapshot
uv run worldcup-tracker list

# List from a live fetch (hits the network)
uv run worldcup-tracker list --live

# Diff snapshot vs live without saving
uv run worldcup-tracker diff

# Poll on an interval (seconds)
uv run worldcup-tracker watch --interval 600
```

Options:

- `-c, --config` — path to `config.yaml` (default: project root)
- `-d, --data-dir` — snapshot directory (default: `data/`)
- `-v, --venue` — filter by venue name from config

Environment variables: `WCT_CONFIG`, `WCT_DATA_DIR`, `WCT_USER_AGENT`, `WCT_HTTP_TIMEOUT`.

## Docker

```powershell
docker compose build
docker compose run --rm tracker check
docker compose run --rm tracker list
```

Scheduled polling (15 minutes):

```powershell
docker compose --profile watch up tracker-watch
```

Snapshots are stored in `./data` on the host (mounted volume).

## Tests

Tests use recorded HTML in `tests/fixtures/` and **do not** call the live site:

```powershell
uv run pytest
```

## Project layout

```
config.yaml              # Monitored venues
src/worldcup_tracker/    # Application code
  parsers/               # Site-specific HTML parsers (extensible)
  cli.py                 # Typer CLI
  storage.py             # JSON snapshots in data/
tests/                   # pytest + HTML fixtures
data/                    # Runtime snapshots (gitignored)
```

See [docs/ADDING_VENUES.md](docs/ADDING_VENUES.md) for adding new venue page types.

## Git: first commit and publishing

This repo is ready for an initial commit. If **Git isn’t letting you publish**, work through these common fixes on Windows (PowerShell).

### 1. Create the first commit locally

```powershell
cd C:\Users\Wildman\Documents\Code\WorldCupTracker
git add .
git status
git commit -m "Initial World Cup venue fixture tracker"
```

### 2. Add a remote (GitHub example)

Create an empty repository on GitHub, then:

```powershell
git remote add origin https://github.com/YOUR_USER/WorldCupTracker.git
git branch -M main
```

Verify:

```powershell
git remote -v
```

### 3. Authentication

| Symptom | Fix |
|--------|-----|
| `Authentication failed` / `403` | Use a [Personal Access Token](https://github.com/settings/tokens) (classic: `repo` scope) instead of a password, or sign in with `gh auth login` |
| `Repository not found` | Check remote URL spelling and that the repo exists under your account |
| `Permission denied (publickey)` | Add an SSH key to GitHub or switch remote to HTTPS |
| `failed to push some refs` | Run `git pull origin main --rebase` if the remote has a README/license commit |
| `src refspec main does not match` | Ensure you have at least one commit: `git log` |

Push (only after auth works):

```powershell
git push -u origin main
```

### 4. GitHub CLI alternative

```powershell
gh auth login
gh repo create WorldCupTracker --public --source=. --remote=origin --push
```

We do **not** push from this project automatically; confirm credentials on your machine first.

## License

MIT (add a `LICENSE` file if you publish publicly).
