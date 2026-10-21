# ---------- Etapa 1: construir las dependencias (wheels) ----------
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ---------- Etapa 2: imagen final (solo lo necesario para ejecutar) ----------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=5000
WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY . .
RUN useradd --create-home appuser && mkdir -p /data/uploads && chown -R appuser /app /data
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/v1/health' % os.environ.get('PORT','5000'), timeout=3)" || exit 1

# Equivalente de `prisma migrate deploy` en este proyecto: `alembic upgrade head`.
CMD ["sh", "-c", "alembic upgrade head && exec gunicorn -b 0.0.0.0:${PORT} -w ${WEB_CONCURRENCY:-3} --access-logfile - 'app.main:create_app()'"]
