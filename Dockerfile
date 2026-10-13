FROM python:3.14.8-slim-trixie

# OPENCV_IO_MAX_IMAGE_PIXELS: 8192x8192 を超える画像は読み込まずにエラーにします(巨大な画像でメモリを使い切らないためです)。
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RUFF_NO_CACHE=true \
    OPENCV_IO_MAX_IMAGE_PIXELS=67108864

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements-dev.txt

COPY pyproject.toml multiqr.py foo.py bar.py baz.py make_samples.py ./
COPY tests ./tests

RUN useradd --create-home --uid 10001 app
USER app

CMD ["python", "foo.py", "--help"]
