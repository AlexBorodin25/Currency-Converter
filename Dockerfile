FROM ubuntu:latest
LABEL authors="alexb"

ENTRYPOINT ["top", "-b"]

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY currency_converter.py .

CMD ["python", "currency_converter.py"]