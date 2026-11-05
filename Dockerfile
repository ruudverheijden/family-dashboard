FROM python:3.12-alpine3.23
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data CACHE_DIR=/cache
WORKDIR /app
COPY requirements.txt .
# Alpine uses musl (no glibc); require the CVE-2026-85091 zlib security fix.
RUN apk upgrade --no-cache \
    && apk add --no-cache 'zlib>=1.3.2-r1' tzdata \
    && python -m pip install --no-cache-dir --upgrade pip==26.2.2 \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m pip check \
    && python -m pip uninstall --yes pip \
    && addgroup -g 10001 family \
    && adduser -D -u 10001 -G family family \
    && mkdir /data /cache \
    && chown family:family /data /cache
COPY app ./app
COPY LICENSE ./LICENSE
LABEL org.opencontainers.image.licenses="PolyForm-Noncommercial-1.0.0"
LABEL org.opencontainers.image.version="0.3.1"
USER family
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--no-access-log"]
