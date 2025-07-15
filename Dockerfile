FROM python:3.11-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy full project structure before install
COPY pyproject.toml tox.ini ./
COPY src ./src
COPY docs ./docs

# Install production dependencies
RUN pip install --upgrade pip && pip install .[prod]

EXPOSE 8080
ENV PORT=8080

# ! Listening on 0.0.0.0 is ok only in an env we control completely —
# ! otherwise this should be locked down to the source REMS ip
CMD ["uvicorn", "rems_co.main:app", "--host", "0.0.0.0", "--port", "8080"]

