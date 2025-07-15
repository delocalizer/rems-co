# CONFIGURE+DEPLOY.md

## Deploying **rems-co** in a **REMS** stack

This guide explains the path to configure and deploy the **rems-co** service alongside
a running [**REMS**](https://github.com/CSCfi/rems) instance using Docker Compose. 

---

## Prerequisites


You should begin with:

- A working **REMS** stack running via `docker-compose` (see **REMS** project stock [`docker-compose.yml`](https://github.com/CSCfi/rems/blob/master/docker-compose.yml))
- Access to a working COmanage Registry service via API credentials
- `docker` and `docker-compose` installed on your host system
- A valid `.env` file for **rems-co** (see [`example.env`](../resources/example-config/example.env))
- Your **REMS** config file `config.edn`.

---

## 1. Configure **REMS**

Edit the **REMS** `config.edn` file to add the entitlement webhook targets:

```clojure
:entitlements-target {:add "http://rems_co:8080/approve"
                      :remove "http://rems_co:8080/revoke"}
```

💡 Note:
- `rems_co` must match the name of the **rems-co** container created later in your `docker-compose.yml`.
- Port `8080` is the internal listener port that matches the default specified in the **rems-co** [Docker image](../Dockerfile)

Mount the updated `config.edn` into the `rems_app` container using the existing `volumes:` section.

---

## 2. Configure **rems-co**

Create a `.env` file based on `example.env`, and populate it with appropriate values:

```env
COMANAGE_REGISTRY_URL=https://registry.example.org/registry/
COMANAGE_COID=99
COMANAGE_API_USERID=youruser
COMANAGE_API_KEY=yourtoken
...
```

This file will be loaded by Docker Compose and passed into the **rems-co** container via the `env_file:` directive.

---

## 3. Extend `docker-compose.yml`

Add a new service for **rems-co** to your existing Compose file:

```yaml
  rems_co:
    container_name: rems_co
    image: ghcr.io/your-org/rems-co:latest
    ports:
      - "8080:8080"
    env_file:
      - .env
    restart: unless-stopped
```

---

## 4. Deploy and Connect

Start the new container without disrupting the rest of the stack:

```bash
docker compose up -d rems_co
```

Then, restart the **REMS** app so it picks up the updated `config.edn`:

```bash
docker compose up -d --force-recreate --no-deps app
```

---

## Final Checks

- Run `docker compose ps` to verify all containers are up.
- Check `docker compose logs -f rems_co` to ensure **rems-co** is listening.
- Trigger an entitlement action in **REMS** and verify the event is received and processed.

---

## See also

- `resources/example-config` directory in this repo
- [`DEVELOP.md`](./DEVELOP.md) — developer instructions
- [`README.md`](./README.md) — high-level overview
