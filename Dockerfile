FROM python:3.12.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project first
COPY . .

# Install pip requirements directly (simpler approach)
RUN pip install --no-cache-dir \
    alembic==1.14.0 \
    pydantic==2.10.4 \
    pydantic-settings==2.7.0 \
    sqlalchemy==2.0.36 \
    python-dotenv==1.0.1 \
    psycopg2-binary==2.9.10 \
    sqlmodel==0.0.22 \
    pgvector==0.3.6 \
    openai==1.65.2 \
    langchain==0.3.18 \
    langchain-community==0.3.17 \
    docx2txt==0.8 \
    pypdf==5.3.0 \
    streamlit==1.42.2 \
    docling==2.25.0 \
    transformers==4.42.0 \
    tiktoken==0.9.0 \
    unstructured[pdf]==0.16.20

# Expose port
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app

# Run the application
CMD ["streamlit", "run", "frontend/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
