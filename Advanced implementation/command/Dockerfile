FROM python:3.13-slim-bookworm

WORKDIR /app

COPY . .

RUN pip install twisted && apt-get update && apt-get install -y libreadline-dev

CMD ["python", "commandInterpreter.py"]
