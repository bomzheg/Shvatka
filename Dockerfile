FROM python:3.11-buster AS builder
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
RUN python3 -m venv $VIRTUAL_ENV
WORKDIR $CODE_PATH
COPY lock.txt ${CODE_PATH}/
RUN $VIRTUAL_ENV/bin/pip install -r lock.txt

FROM python:3.11-slim-buster
LABEL maintainer="bomzheg <bomzheg@gmail.com>" \
      description="Shvatka Telegram Bot"
ARG VCS_SHA
ARG BUILD_AT
ENV VIRTUAL_ENV=/opt/venv
ENV CODE_PATH=/code
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY . ${CODE_PATH}/shvatka
WORKDIR $CODE_PATH/shvatka
RUN apt update && apt install -y texlive-latex-base texlive-latex-extra texlive-fonts-recomended texlive-fonts-extra texlive-lang-all latexmk && apt clean && rm -rf /var/lib/apt/lists
RUN echo "{\"vcs_hash\": \"${VCS_SHA}\", \"build_at\": \"${BUILD_AT}\" }" > version.yaml
ENTRYPOINT ["python3", "-m", "shvatka"]
