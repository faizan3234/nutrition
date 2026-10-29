FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /srv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 reliv
COPY app/ ./app/
COPY web/ ./web/
COPY admin/ ./admin/
# Private images and SQLite live in a persisted, non-public folder.
RUN mkdir -p /srv/data/private_learning_images \
    && chown -R reliv:reliv /srv/data
USER reliv
ENV NUTRITION_DB_PATH=/srv/data/nutrition.sqlite3 \
    RELIV_LEARNING_IMAGE_DIR=/srv/data/private_learning_images
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
