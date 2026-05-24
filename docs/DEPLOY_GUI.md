# Deploy with Docker GUI only (no cron, no SSH)

One `docker-compose.yml` runs the tracker continuously. It checks every **15 minutes**, sends Pushover alerts on changes, and uses at most **128 MB RAM**.

## What you need on the NAS

- Docker installed (OMV-Extras **Docker** + **Compose**, or **Portainer**)
- Your GitHub repo published (e.g. `https://github.com/leowildman/WorldCupTracker`)
- Pushover user key + app token

---

## Option A — Portainer (easiest)

1. Open **Portainer** → **Stacks** → **Add stack**.
2. Name: `worldcup-tracker`.
3. **Build method:** Repository.
4. **Repository URL:** `https://github.com/leowildman/WorldCupTracker`
5. **Repository reference:** `main` (or your branch).
6. **Compose path:** `docker-compose.yml`
7. Enable **Authentication** if the repo is private (GitHub username + PAT).
8. Scroll to **Environment variables** and add:
   - `PUSHOVER_USER_KEY` = your user key
   - `PUSHOVER_API_TOKEN` = your app token  
   (Same as `.env` — you do not need a `.env` file on disk if you set these here.)
9. **Deploy the stack**.

Portainer clones the repo, builds the image, and starts the container. Logs: **Containers** → `worldcup-tracker` → **Logs**.

### Edit config later

- **Stacks** → your stack → **Editor** → change `config.yaml` in the repo and **Pull and redeploy**, or  
- On the NAS, edit `config.yaml` in the stack’s folder if you deployed to a bind-mounted path.

Ensure `notifications.enabled: true` in `config.yaml` (already set in the repo default).

---

## Option B — OMV Compose plugin

1. One-time: copy the repo onto a shared folder (File Station → upload zip from GitHub, or clone once).
2. In that folder, create `.env` from `.env.example` and fill in Pushover keys (File Station text editor).
3. OMV **Docker** → **Compose** → **Files** → **Add** → **New**.
4. **Name:** `worldcup-tracker`.
5. **Working directory:** folder containing `docker-compose.yml` (e.g. `docker/WorldCupTracker`).
6. **Compose file:** `docker-compose.yml`.
7. **Save** → **Up** (build + start).

The container should show **running**. Data is stored in `data/` next to the compose file.

---

## Option C — Portainer “Web editor” (no Git on NAS)

1. Download the repo as ZIP from GitHub and extract to a shared folder.
2. Add `.env` with Pushover keys in that folder.
3. Portainer → **Stacks** → **Add** → **Web editor**.
4. Paste the contents of `docker-compose.yml`.
5. Under **Advanced**, set **Working directory** / volume paths to that folder on the host (so `./data` and `./config.yaml` resolve correctly).
6. **Deploy**.

---

## After deploy

- First run may report many `[new]` fixtures (baseline snapshot). Later runs only alert on real changes.
- **Stop:** Stack → Stop in Portainer / OMV.
- **Update:** Stack → **Pull and redeploy** (Portainer + Git) or replace files and **Recreate** (OMV).

## Resource use

| Setting | Value |
|---------|--------|
| Poll interval | 15 min (`900` seconds) |
| RAM limit | 128 MB |
| CPU limit | 0.25 cores |
| Idle usage | Low — mostly sleeping between polls |

To poll every 30 minutes, change the command in the stack editor to:

```yaml
command: ["watch", "--interval", "1800"]
```

---

## No terminal required

You do **not** need cron or `docker compose run` if you use this stack. The GUI starts one container that loops `watch` for you.

Optional: `docker-compose.prod.yml` + cron is for minimal RAM between polls; ignore it if you prefer the GUI workflow above.
