FROM python:3.11-buster as builder
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
RUN pip3 install --no-cache-dir poetry==1.4.2
RUN python3 -m venv $VIRTUAL_ENV
WORKDIR $CODE_PATH
COPY poetry.lock pyproject.toml ${CODE_PATH}/
RUN python3 -m poetry export -f requirements.txt | $VIRTUAL_ENV/bin/pip install -r /dev/stdin

FROM python:3.11-slim-buster
LABEL maintainer="bomzheg <bomzheg@gmail.com>" \
      description="Shvatka Telegram Bot"
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY . ${CODE_PATH}/shvatka
WORKDIR $CODE_PATH/shvatka
RUN echo $INPUT_VERSION_YAML
RUN echo $steps.yaml.outputs.INPUT_VERSION_YAML
RUN echo $steps.yaml.outputs.VERSION_YAML
RUN echo $INPUT_VERSION_YAML > version.yaml
ENTRYPOINT ["python3", "-m", "shvatka.tgbot"]
