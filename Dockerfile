# syntax=docker/dockerfile:1.7

ARG PYTHON_BASE_REF=python:3.12-slim@sha256:42f1689d6d6b906c7e829f9d9ec38491550344ac9adc01e464ff9a08df1ffb48
FROM ${PYTHON_BASE_REF} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

COPY requirements.lock /app/requirements.lock

RUN python -m venv "${VIRTUAL_ENV}" \
    && pip install --no-cache-dir --no-deps -r /app/requirements.lock \
    && pip check

COPY . /app

# Compatibility path for Windows-style orchestrator subprocess contract.
RUN mkdir -p /app/.venv/Scripts \
    && ln -sf /opt/venv/bin/python /app/.venv/Scripts/python.exe

# Release promotion/rollback is handled by scripts/release_controller.py in CI.
CMD ["python", "main_bot_orchestrator.py"]
