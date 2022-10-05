FROM python:3
LABEL maintainer "Alex Cameron <alex.cameron@trailofbits.com>"

COPY sigstore-python /tmp/sigstore-python

RUN cd /tmp/sigstore-python && \
    pip install .

ENTRYPOINT [ "sigstore" ]
