FROM python:3
LABEL maintainer "Alex Cameron <alex.cameron@trailofbits.com>"

RUN git clone https://github.com/sigstore/sigstore-python.git && \
    cd sigstore-python && \
    pip install -e .

ENTRYPOINT ["sigstore"]
