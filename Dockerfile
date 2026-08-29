FROM python:3.12-slim

WORKDIR /app

# Install build tools and system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and data assets
COPY . .

# Generate Prisma client for database access
RUN python -m prisma generate --schema prisma/schema.prisma || true

# Standard Cloud Run / container port
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# Run Streamlit on PORT
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]
