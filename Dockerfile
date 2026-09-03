# The image is assembled from two halves that change at very different rates.
#
#   * `deps` — python, the apt packages and the whole venv: ~160 MB, decided by
#     lock.txt alone. CI publishes it once as `bomzheg/shvatka:deps-<hash>` and
#     every later build starts FROM that exact tag, so the layer the servers
#     already have is the layer the next image points at.
#   * the app on top of it — a few hundred kilobytes, new on every commit.
#
# Why a published tag and not a build cache: reinstalling the very same lock
# file does not produce the very same bytes (pyc timestamps, RECORD ordering,
# apt index), so *any* cache miss — and a branch-scoped CI cache misses often —
# hands the servers a fresh 160 MB layer to pull for a two-line commit. A tag
# cannot miss.
#
# DEPS_IMAGE names that published half. It defaults to the `deps` stage below,
# so a plain `docker build .` still builds the whole thing in one go.
ARG DEPS_IMAGE=deps

FROM python:3.13-bookworm AS venv-builder
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

FROM python:3.13-slim-bookworm AS deps
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# fonts-liberation: Liberation Serif has the metrics of Times New Roman, the
# font the keys to print are laid out in
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 fonts-liberation && \
    rm -rf /var/lib/apt/lists/*
COPY --from=venv-builder $VIRTUAL_ENV $VIRTUAL_ENV
# bake the matplotlib font cache into the image, otherwise every fresh
# container spends seconds on "generated new fontManager" at the first import
RUN python3 -c "from matplotlib import pyplot"

# CODE_PATH, VIRTUAL_ENV and PATH come with DEPS_IMAGE — it is built from the
# `deps` stage above, whichever way it is named here.
FROM ${DEPS_IMAGE} AS app
LABEL maintainer="bomzheg <bomzheg@gmail.com>" \
      description="Shvatka Telegram Bot"
ARG VCS_HASH
ARG VCS_NAME
ARG COMMIT_AT
ARG BUILD_AT
COPY . ${CODE_PATH}/shvatka
WORKDIR ${CODE_PATH}/shvatka
RUN python3 -m compileall -q ${CODE_PATH}/shvatka/shvatka
RUN echo "{\"vcs_hash\": \"${VCS_HASH}\", \"commit_at\": \"${COMMIT_AT}\", \"vcs_name\": \"${VCS_NAME}\", \"build_at\": \"${BUILD_AT}\" }" > version.yaml
ENTRYPOINT ["python3", "-m", "shvatka"]
