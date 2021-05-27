FROM python:3.9.5-buster

RUN apt-get update -y && apt-get install curl -y && apt-get clean
RUN pip install poetry

COPY poetry.lock pyproject.toml /app/
WORKDIR /app
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-dev

COPY fun_api fun_api
EXPOSE 8000
ENTRYPOINT ["poetry", "run", "uvicorn", "fun_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "fun_api/logging.conf"]
