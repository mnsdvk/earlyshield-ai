FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLECORS=false \
    STREAMLIT_SERVER_PORT=8080

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8080"]
