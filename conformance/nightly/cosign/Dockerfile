# Reference: https://github.com/sigstore/cosign#developer-installation

FROM golang:1.19
LABEL maintainer "Alex Cameron <alex.cameron@trailofbits.com>"

RUN git clone https://github.com/sigstore/cosign && \
    cd cosign && \
    go install ./cmd/cosign/

ENTRYPOINT $(go env GOPATH)/bin/cosign
