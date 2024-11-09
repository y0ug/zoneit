FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN pip install poetry && poetry install --no-root --without dev
COPY . /app
RUN poetry install --only-root

EXPOSE 8000

CMD ["poetry", "run", "fastapi", "run", "zoneit" ]
