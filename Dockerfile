FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer tzdata && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-lock.txt .
RUN pip install -r requirements-lock.txt
COPY bot.py converter.py storage.py ./
CMD ["python", "bot.py"]
