FROM python:3
LABEL maintainer "Alex Cameron <alex.cameron@trailofbits.com>"

RUN cd sigstore-python && \
    pip install .

ENTRYPOINT [ "sigstore" ]
