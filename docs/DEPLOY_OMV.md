# Deploy on OpenMediaVault (OMV)

**Prefer the GUI?** Use **[DEPLOY_GUI.md](DEPLOY_GUI.md)** — one Compose stack in Portainer/OMV, no cron.

This document is the **optional low-RAM** setup (cron + one-shot `check`). Each run fetches two HTML pages, compares JSON snapshots, and exits.

Typical footprint per run: **~50–120 MB RAM for a few seconds**, then zero.

## 1. Prerequisites

On OMV you need Docker. Common setups:

- **OMV-Extras** → install **Docker** and **Compose** plugins, or
- **Portainer** (optional UI) on the same host

SSH into the NAS as `root` or a user in the `docker` group.

## 2. Install the project

Pick a persistent path on a shared disk, for example:

```bash
sudo mkdir -p /srv/dev-disk-by-label-Pool/docker
cd /srv/dev-disk-by-label-Pool/docker
sudo git clone https://github.com/leowildman/WorldCupTracker.git
cd WorldCupTracker
```

(Use your real pool path — OMV **Shared Folders** shows the mount point.)

Create secrets and edit config:

```bash
cp .env.example .env
nano .env          # PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN
nano config.yaml   # notifications.enabled: true, venues, intervals
```

Build the image once:

```bash
docker compose -f docker-compose.prod.yml build
```

Test a single check:

```bash
docker compose -f docker-compose.prod.yml run --rm tracker check
```

You should see `No changes for …` or fixture diffs. Snapshots live in `./data/`.

## 3. Recommended: cron (lowest resource use)

The container **starts, runs one check, then stops**. Nothing runs between polls.

Edit root’s crontab on OMV:

```bash
sudo crontab -e
```

Add (every **15 minutes** — adjust as you like):

```cron
*/15 * * * * cd /srv/dev-disk-by-label-Pool/docker/WorldCupTracker && docker compose -f docker-compose.prod.yml run --rm tracker check >> /var/log/worldcup-tracker.log 2>&1
```

Replace the `cd` path with your clone directory.

**Polling guidance**

| Interval | Checks/day | Notes |
|----------|------------|--------|
| 15 min   | 96         | Good default for booking openings |
| 30 min   | 48         | Lower load, still reasonable |
| 60 min   | 24         | Fine if you only care about major updates |

Fixture pages rarely change minute-to-minute; 15–30 minutes is enough for World Cup listings.

### OMV scheduled tasks (GUI alternative)

**OMV → System → Scheduled tasks → Add**

- **Type:** User-defined script  
- **Command:** same one-liner as cron (without crontab)  
- **Schedule:** every 15 minutes  

Run as `root` so Docker is available.

## 4. Avoid: always-on `watch` on OMV

```bash
# Higher RAM (~50–100 MB constant) — only use if you need it
docker compose --profile watch up tracker-watch
```

For a home NAS, **cron + `check`** is preferred.

## 5. Resource limits (prod compose file)

`docker-compose.prod.yml` caps CPU and memory during each run:

- **128 MB** RAM limit  
- **0.25 CPU** cores  

That is more than enough; the process usually uses far less.

## 6. Permissions

The container runs as UID **10001**. If `data/` permission errors appear:

```bash
sudo chown -R 10001:10001 data
```

Or on OMV, ensure the shared folder is writable by the Docker user.

## 7. Upgrades

```bash
cd /srv/.../WorldCupTracker
git pull
docker compose -f docker-compose.prod.yml build
```

The next cron run uses the new image. `data/` and `config.yaml` are unchanged.

## 8. Logs

Cron example above appends to `/var/log/worldcup-tracker.log`. Rotate occasionally:

```bash
sudo truncate -s 0 /var/log/worldcup-tracker.log
```

## 9. Pushover / `.env`

`docker-compose.prod.yml` loads `.env` via `env_file`. Keep `.env` only on the NAS (never commit it). `notifications.enabled: true` must be set in `config.yaml`.

## 10. Troubleshooting

| Issue | Fix |
|-------|-----|
| `permission denied` on Docker socket | Run cron as root or add user to `docker` group |
| `compose: command not found` | Use `docker compose` (v2) or install compose plugin |
| No Pushover | Check `.env`, `notifications.enabled`, run `check` manually once |
| False “site broken” alerts | See README — sanity guard; fix parser or wait for site recovery |

## Summary

```text
OMV + Docker + cron every 15 min
  → ~96 short-lived runs/day
  → ~0 CPU/RAM between runs
  → Pushover on fixture or health alerts
```

That is the intended production layout for a NAS.
