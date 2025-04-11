FROM python:3.13-slim-bookworm

WORKDIR /app

COPY . .

RUN pip install twisted

EXPOSE 5678

CMD ["python", "queueManager.py"]
