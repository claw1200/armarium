FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

ENV LIBRARY_ROOT=/library
ENV DATABASE_PATH=/data/catalog.sqlite
RUN mkdir -p /data /library

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
