FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libtk8.6 \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

CMD ["python", "main.py"]
