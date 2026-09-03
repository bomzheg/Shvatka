# The order of this file is what the servers pay for. Everything above
# `COPY . ` is decided by lock.txt and weighs ~160 MB; everything below it is
# ~1.5 MB and changes with every commit. Keep it that way — and keep the build
# cache in the registry (see .github/workflows/build.yml), because reinstalling
# the same lock file does not produce the same bytes (pyc timestamps, RECORD
# ordering), so a cache miss is a fresh 160 MB layer to pull for a two-line
# commit.
FROM python:3.13-bookworm AS builder
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
# ship .pyc alongside the .py, otherwise every fresh container compiles the
# whole venv on the first import, which more than doubles the startup time
ENV UV_COMPILE_BYTECODE=1
RUN pip install --no-cache-dir uv
RUN python3 -m venv $VIRTUAL_ENV
WORKDIR $CODE_PATH
COPY lock.txt ${CODE_PATH}/
RUN uv pip install --no-cache --python $VIRTUAL_ENV/bin/python -r lock.txt

FROM python:3.13-slim-bookworm
LABEL maintainer="bomzheg <bomzheg@gmail.com>" \
      description="Shvatka Telegram Bot"
ARG VCS_HASH
ARG VCS_NAME
ARG COMMIT_AT
ARG BUILD_AT
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# fonts-liberation: Liberation Serif has the metrics of Times New Roman, the
# font the keys to print are laid out in
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 fonts-liberation && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
# bake the matplotlib font cache into the image, otherwise every fresh
# container spends seconds on "generated new fontManager" at the first import
RUN python3 -c "from matplotlib import pyplot"
COPY . ${CODE_PATH}/shvatka
WORKDIR $CODE_PATH/shvatka
RUN python3 -m compileall -q ${CODE_PATH}/shvatka/shvatka
RUN echo "{\"vcs_hash\": \"${VCS_HASH}\", \"commit_at\": \"${COMMIT_AT}\", \"vcs_name\": \"${VCS_NAME}\", \"build_at\": \"${BUILD_AT}\" }" > version.yaml
ENTRYPOINT ["python3", "-m", "shvatka"]
