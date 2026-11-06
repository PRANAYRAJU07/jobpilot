FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

# Install dependencies for Celery and Postgres
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright 1.42.0 to match the base image binaries
RUN pip install playwright==1.42.0 pytest-playwright

COPY . /app

CMD ["celery", "-A", "app.main", "worker", "--loglevel=info", "-Q", "browser.application"]
