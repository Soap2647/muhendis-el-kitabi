# Tek aşama: bağımlılık yok, bu yüzden requirements.txt yok.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PORT=8080 APP_VERSION=1.2.0
RUN useradd --uid 10001 --no-create-home uygulama
WORKDIR /uygulama
COPY telemetri_api.py saglik.py ./
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=2s --retries=3 \
  CMD ["python", "saglik.py"]
ENTRYPOINT ["python", "telemetri_api.py"]
