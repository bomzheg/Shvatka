FROM python:3.10-buster as builder
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
RUN pip install --no-cache-dir poetry==1.2.0
RUN python3 -m venv $VIRTUAL_ENV
WORKDIR $CODE_PATH
COPY poetry.lock pyproject.toml $CODE_PATH
RUN poetry export -f requirements.txt | /venv/bin/pip install -r /dev/stdin

FROM python:3.10-slim-buster
LABEL maintainer="bomzheg <bomzheg@gmail.com>" \
      description="Shvatka Telegram Bot"
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY shvatka ${CODE_PATH}/shvatka
WORKDIR $CODE_PATH/shvatka
ENTRYPOINT ["python3", "-m", "tgbot"]
