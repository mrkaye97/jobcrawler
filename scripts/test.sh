export DATABASE_URL=postgresql://matt@localhost/jobcrawler-test

poetry run python3 -m pytest $*

unset DATABASE_URL
