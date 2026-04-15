FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate results if not present
RUN python generate_results.py || true

EXPOSE 8000

CMD ["uvicorn", "backend.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
