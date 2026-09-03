ARG DEPS_IMAGE=deps

FROM python:3.14-bookworm AS venv-builder
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
RUN pip install --no-cache-dir uv
RUN python3 -m venv $VIRTUAL_ENV
WORKDIR $CODE_PATH
COPY lock.txt ${CODE_PATH}/
# ship .pyc alongside the .py, otherwise every fresh container compiles the
# whole venv on the first import, which more than doubles the startup time
RUN uv pip install --no-cache --python $VIRTUAL_ENV/bin/python -r lock.txt && \
    $VIRTUAL_ENV/bin/python -m compileall -q -f \
        --invalidation-mode unchecked-hash $VIRTUAL_ENV/lib

FROM python:3.14-slim-bookworm AS deps
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
