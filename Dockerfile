FROM python:3.14.8-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RUFF_NO_CACHE=true

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements-dev.txt

COPY pyproject.toml *.py ./
COPY tests ./tests

RUN useradd --create-home --uid 10001 app
USER app

CMD ["python", "foo.py", "--help"]
