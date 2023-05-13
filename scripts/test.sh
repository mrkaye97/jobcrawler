export DATABASE_URL=postgresql://matt@localhost/jobcrawler-test

python3 -m pytest $*

unset DATABASE_URL
