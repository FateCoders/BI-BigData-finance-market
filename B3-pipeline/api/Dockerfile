FROM python:3.11-slim

WORKDIR /app

RUN pip install flask duckdb pandas

COPY app.py .

EXPOSE 5001

CMD ["python", "app.py"]