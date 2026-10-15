FROM python:3.11-slim
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY rag_data ./rag_data
ENV RAG_DATA_DIR=/srv/rag_data
EXPOSE 8000
# Same image serves the API (default) and runs the RAG indexing pipeline:
#   docker compose run --rm rag-index
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
