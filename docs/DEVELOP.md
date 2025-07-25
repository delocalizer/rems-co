# REMS–COmanage Developer Guide

This project is a FastAPI-based service that processes entitlement events from REMS and updates COmanage accordingly.

---

## 1. Clone the Repo and Set Up Environment

```bash
git clone https://github.com/delocalizer/rems-co.git
cd rems-co
python -m venv .venv
source .venv/bin/activate
```

---

## 2. Install in Editable Mode

```bash
pip install -e ".[dev]"
```

This installs:
- The project (`rems_co/`) in editable mode
- All dev tools: `pytest`, `mypy`, `black`, `ruff`, etc.

---

## 3. Configuration

Copy [example.env](../resources/example-config/example.env) to `.env` and fill in required values:

```env
COMANAGE_REGISTRY_URL=https://registry.example.org/registry
COMANAGE_API_USERID=api-user
COMANAGE_API_KEY=super-secret-key
COMANAGE_COID=42
CREATE_GROUPS_FOR_RESOURCES=["urn:allowed.org:*"]
```

---

## 4. Run Tests, Linting, Type Checks

### One-liner to run everything:

```bash
tox
```

### Or run them individually:

```bash
tox -e py311    # Unit tests
tox -e lint     # Ruff linter
tox -e format   # Black formatting check
tox -e type     # mypy type checks
```

---

## 5. Run the FastAPI App Locally

Start the service on `localhost:8080`:

```bash
uvicorn rems_co.main:app --reload --host 0.0.0.0 --port 8080
```

This exposes:

- `POST /approve`
- `POST /revoke`

You can test with `curl`, Postman, `httpie` etc.

---

## 6. Run in Docker (optional)

```bash
docker build -t rems-co .
docker run --rm -p 8080:8080 --env-file .env rems-co
```
