export DATABASE_URL=postgresql://matt@localhost/jobcrawler-test

export ENV=TEST
poetry run python3 -m pytest $*

unset DATABASE_URL
