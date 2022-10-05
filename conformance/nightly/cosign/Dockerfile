# Reference: https://github.com/sigstore/cosign#developer-installation

FROM golang:1.19
LABEL maintainer "Alex Cameron <alex.cameron@trailofbits.com>"

COPY cosign /tmp/cosign

RUN cd /tmp/cosign && \
    go install ./cmd/cosign/

ENTRYPOINT $(go env GOPATH)/bin/cosign
