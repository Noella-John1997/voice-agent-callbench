FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY callbench ./callbench
COPY scenarios ./scenarios
RUN pip install --no-cache-dir . && useradd -m app
USER app
ENV CALLBENCH_SCENARIO=/app/scenarios/employment_verification.yaml PORT=8000
EXPOSE 8000
# Render / Hugging Face / Railway set $PORT; default 8000 locally
CMD ["sh", "-c", "callbench web --host 0.0.0.0 --port ${PORT}"]
