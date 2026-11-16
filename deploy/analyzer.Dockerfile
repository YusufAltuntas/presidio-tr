FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md README_EN.md LICENSE ./
COPY src ./src
# Sürümler uv.lock'tan gelir; imaj her kurulumda aynı bağımlılıklarla çıkar.
RUN uv sync --locked --no-dev --no-editable --extra server

# Servis root yetkisi gerektirmez.
RUN useradd --system --no-create-home app
USER app

EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3000/health')"
CMD ["/app/.venv/bin/uvicorn", "presidio_tr.server:app", "--host", "0.0.0.0", "--port", "3000"]
