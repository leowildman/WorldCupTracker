# Deploy with Docker GUI (pull image — like Romm)

Romm uses a published image:

```yaml
image: rommapp/romm:latest
```

This project does the same after you push to GitHub:

```yaml
image: ghcr.io/leowildman/worldcup-tracker:latest
```

GitHub Actions builds and publishes that image on every push to `main`. **No `git clone` on the NAS** and **no local build** — Docker only pulls the image.

---

## One-time: publish the image

1. Push this repo to GitHub (`main` branch).
2. Open **Actions** on GitHub → wait for **Publish Docker image** to finish.
3. Under **Packages** you should see `worldcup-tracker`.

If the package is private, in Portainer add a registry: `ghcr.io` with a GitHub PAT (`read:packages`).

---

## Portainer — stack from compose (recommended)

**Stacks** → **Add stack** → **Web editor** → paste:

```yaml
services:
  worldcup-tracker:
    image: ghcr.io/leowildman/worldcup-tracker:latest
    pull_policy: always
    container_name: worldcup-tracker
    restart: unless-stopped
    environment:
      PUSHOVER_USER_KEY: "your_user_key"
      PUSHOVER_API_TOKEN: "your_app_token"
      WCT_CONFIG: /app/config.yaml
      WCT_DATA_DIR: /app/data
    volumes:
      - worldcup-data:/app/data
    command: ["watch", "--interval", "900"]
    mem_limit: 128m
    cpus: 0.25

volumes:
  worldcup-data:
```

Replace the two Pushover values → **Deploy the stack**.

The default `config.yaml` is **inside the image** (Bar Kick + Big Penny, notifications on). To change venues, add a bind mount:

```yaml
    volumes:
      - worldcup-data:/app/data
      - /path/on/nas/config.yaml:/app/config.yaml:ro
```

---

## Portainer — pull from GitHub compose file

**Stacks** → **Add stack** → **Repository**

- URL: `https://github.com/leowildman/WorldCupTracker`
- Compose path: `docker-compose.yml`

That file only references the image (no build step). Add `.env` on the NAS or set env vars in the stack UI.

---

## OMV Docker Compose plugin

1. Create a folder on a shared disk, e.g. `docker/worldcup-tracker/`.
2. Copy `docker-compose.yml` from GitHub (or clone the repo once).
3. Add `.env`:

   ```env
   PUSHOVER_USER_KEY=...
   PUSHOVER_API_TOKEN=...
   ```

4. **Compose** → **Up** — Docker pulls `ghcr.io/leowildman/worldcup-tracker:latest` and starts.

---

## Updates

Pull the new image and recreate the container:

- **Portainer:** Stack → **Pull and redeploy**, or enable **Pull latest image** on the container.
- **OMV:** Compose → **Pull** → **Up** again.

No rebuild on the NAS.

---

## Local development (build from source)

```powershell
copy docker-compose.override.example.yml docker-compose.override.yml
docker compose up -d --build
```

---

## Why it wasn’t like this before

`rommapp/romm:latest` exists on Docker Hub because the Romm authors publish it. This repo only had `build: .` until the GitHub Action published `ghcr.io/leowildman/worldcup-tracker:latest`. After the first successful Action run, you can deploy like any other pull-only stack.
