FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install poetry && poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY . .

EXPOSE 8000
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]