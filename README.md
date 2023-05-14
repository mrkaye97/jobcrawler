# Jobcrawler

[Jobcrawler](https://jobcrawler.matthewrkaye.com) is a simple Flask app for keeping tabs on job postings at companies you are interested in. I built it because I didn't know of anything like it, but mostly because I wanted to toy with Flask a bit and get some experience building a web app. Feel free to use it, and [please report any issues you find](https://github.com/mrkaye97/jobcrawler/issues).

## Stack

The app is a [Flask](https://flask.palletsprojects.com/en/2.3.x/) backend with a JS frontend. It uses [Postgres](https://www.postgresql.org/) as a database and is deployed behind a [Gunicorn](https://gunicorn.org/) server on [DigitalOcean](https://www.digitalocean.com/) using [Docker](https://www.docker.com/) via [GitHub Actions](https://github.com/actions). Logs are piped to [Papertrail](https://www.papertrail.com/), and errors flow into [Sentry](https://sentry.io).

## Running the Project

If you're interested in running the project locally, you can do it in a few simple steps.

First, you'll need to have Python 3.9+ installed on your machine. Once you do, you can run the following to set up the virtualenv for the project.

```bash
## From the root of the project
cd jobcrawler

python3 -m venv flaskenv

. flaskenv/bin/activate

## Install the dependencies into the venv
pip3 install -r requirements.txt

## Restart the venv, just in case
deactivate
. flaskenv/bin/activate
```

Next, you'll need to create a `.env` at the root level, which will be picked up when you boot the app.

```bash
touch .env

echo "DATABASE_URL=postgresql://localhost/jobcrawler" >> .env
echo "ENV=DEV" >> .env
```

Finally, you can boot the app.

```bash
. scripts/run.sh
```

There are some additional items you can add to your `.env` that will slightly alter your local app's behavior.

1. Setting `DEV_AUTOLOGIN=True` will attempt to automatically log you in when you're running locally, to save you the hassle of needing to log in every time you boot the app.
2. Setting `DEV_USER_EMAIL={Some Email}` will use the specified email to log you in if `DEV_AUTOLOGIN` is set to `True`
3. Setting `DEV_IS_ADMIN_USER=True` will allow you to act as an admin, which grants you permission to see the Admin UI and access a couple of other admin features, like being able to manually kick off a scraping job or an email job run.

## Tests

The project is tested with `pytest`. Tests live in the `tests` directory and are split up into unit tests and integration tests. Once you are able to successfully boot the app, you can run the tests by running `. scripts/test.sh`

## To Do

This project is pretty barebones. In no particular order, things to work on are:

1. Making collaboration possible (check config into Git, add setup instructions, etc.)
2. Improve the scraping methods to allow for scraping of (e.g.) WorkDay or other multi-page sites. Right now, scraping works well for ATS systems like Greenhouse and Lever, but not so well for Workday and similar.
3. Add lots more test coverage.
4. Migrate the frontend to React.
5. Use TypeScript or PureScript instead of vanilla JavaScript.
6. Improve formatting on mobile.

