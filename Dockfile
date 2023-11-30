FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y python3 python3-pip &&\
    apt-get install -y --no-install-recommends libleptonica-dev && \
    apt-get install -y --no-install-recommends libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev libtesseract-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
