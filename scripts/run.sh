DB_NAME=jobcrawler

echo "SELECT 'CREATE DATABASE $DB_NAME' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec" | psql

flask db upgrade

gunicorn app:app \
    --workers 2 \
    --timeout 180 \
    --bind localhost.localdomain:5000 \
    --log-level=info \
    --preload
