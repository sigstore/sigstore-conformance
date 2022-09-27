FROM python:3
LABEL maintainer "Alex Cameron <alex.cameron@trailofbits.com>"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "sigstore" ]
