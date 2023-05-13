# Jobcrawler

[Jobcrawler](https://jobcrawler.matthewrkaye.com) is a simple Flask app for keeping tabs on job postings at companies you are interested in. I built it because I didn't know of anything like it, but mostly because I wanted to toy with Flask a bit and get some experience building a web app. Feel free to use it, and [please report any issues you find](https://github.com/mrkaye97/jobcrawler/issues).

## Stack

The app is a [Flask](https://flask.palletsprojects.com/en/2.3.x/) backend with a JS frontend. It uses [Postgres](https://www.postgresql.org/) as a database and is deployed behind a [Gunicorn](https://gunicorn.org/) server on [DigitalOcean](https://www.digitalocean.com/) using [Docker](https://www.docker.com/) via [GitHub Actions](https://github.com/actions). Logs are piped to [Papertrail](https://www.papertrail.com/), and errors flow into [Sentry](https://sentry.io).

## To Do

This project is pretty barebones. In no particular order, things to work on are:

1. Making collaboration possible (check config into Git, add setup instructions, etc.)
2. Improve the scraping methods to allow for scraping of (e.g.) WorkDay or other multi-page sites. Right now, scraping works well for ATS systems like Greenhouse and Lever, but not so well for Workday and similar.
3. Add lots more test coverage.
4. Migrate the frontend to React.
5. Use TypeScript or PureScript instead of vanilla JavaScript.
6. Improve formatting on mobile.

