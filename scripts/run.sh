gunicorn app:app \
    --workers 2 \
    --timeout 180 \
    --bind 127.0.0.1:5000 \
    --log-level=info \
    --preload
