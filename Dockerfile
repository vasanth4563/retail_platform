FROM python:3.11-slim

WORKDIR /app

# Non-root user — required by the assessment's Docker rules
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Defaults only — override at `docker run` time with -e for real
# environment-specific values. Never bake real credentials in here.
ENV APP_VERSION=4.2.0
ENV ENVIRONMENT=PRODUCTION
ENV FORCE_HEALTH_FAIL=false
ENV DB_HOST=""

EXPOSE 8081

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request as u,sys; sys.exit(0 if u.urlopen('http://localhost:8081/health').getcode()==200 else 1)" || exit 1

USER appuser

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8081"]
