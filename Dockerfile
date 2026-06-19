FROM python:3.13-bookworm AS builder
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
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
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY . ${CODE_PATH}/shvatka
WORKDIR $CODE_PATH/shvatka
RUN echo "{\"vcs_hash\": \"${VCS_HASH}\", \"commit_at\": \"${COMMIT_AT}\", \"vcs_name\": \"${VCS_NAME}\", \"build_at\": \"${BUILD_AT}\" }" > version.yaml
ENTRYPOINT ["python3", "-m", "shvatka"]
