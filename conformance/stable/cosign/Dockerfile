# Reference: https://github.com/sigstore/cosign#dockerfile

FROM gcr.io/projectsigstore/cosign:v1.13.0 as cosign-bin
LABEL maintainer "Alex Cameron <alex.cameron@trailofbits.com>"

FROM cgr.dev/chainguard/static:latest
COPY --from=cosign-bin /ko-app/cosign /usr/local/bin/cosign

USER root

ENTRYPOINT [ "cosign" ]
