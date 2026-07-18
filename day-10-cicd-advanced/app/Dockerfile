FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY static/ static/

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD python -c "import requests; requests.get('http://localhost:5000/')" || exit 1

CMD ["python", "app.py"]
