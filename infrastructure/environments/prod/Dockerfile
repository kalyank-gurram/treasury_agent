FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY /rag/faiss_store /app/services/rag/faiss_store
RUN pip install poetry && poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY . .

EXPOSE 8000
CMD ["uvicorn", "services.treasury_service.app:app", "--host", "0.0.0.0", "--port", "8000"]