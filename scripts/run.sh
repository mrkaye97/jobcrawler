DB_NAME=jobcrawler

echo "SELECT 'CREATE DATABASE $DB_NAME' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec" | psql

export ENV=DEV
poetry run flask db upgrade
poetry run gunicorn app:app \
    --workers 1 \
    --timeout 180 \
    --bind 127.0.0.1:5000 \
    --log-level=info \
    --access-logfile '-'
