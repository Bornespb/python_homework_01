FROM python:3.13.5-bullseye

WORKDIR /app

COPY . .

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

ENV VIRTUAL_ENV=/opt/venv
RUN uv venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN uv pip install --no-cache -e .

ENTRYPOINT ["python", "-m", "log_analyzer.log_analyzer"]
