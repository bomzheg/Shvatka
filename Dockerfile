FROM python:3.13-bookworm AS builder
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
RUN python3 -m venv $VIRTUAL_ENV
WORKDIR $CODE_PATH
COPY lock.txt ${CODE_PATH}/
RUN $VIRTUAL_ENV/bin/pip install uv && $VIRTUAL_ENV/bin/uv pip install -r lock.txt

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
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY . ${CODE_PATH}/shvatka
WORKDIR $CODE_PATH/shvatka
RUN echo "{\"vcs_hash\": \"${VCS_HASH}\", \"commit_at\": \"${COMMIT_AT}\", \"branch\": \"${VCS_NAME}\", \"build_at\": \"${BUILD_AT}\" }" > version.yaml
ENTRYPOINT ["python3", "-m", "shvatka"]
