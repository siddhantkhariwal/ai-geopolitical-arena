FROM python:3.11-slim

# HuggingFace Spaces requires non-root user
RUN useradd -m -u 1000 user
WORKDIR /app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

# Generate default leaderboard at build time
RUN python generate_results.py || true
RUN python generate_claude_results.py || true

# HF Spaces requires port 7860
EXPOSE 7860

USER user

CMD ["uvicorn", "backend.api.server:app", "--host", "0.0.0.0", "--port", "7860"]
