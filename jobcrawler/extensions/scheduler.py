import warnings

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)

from flask_apscheduler import APScheduler

sched = APScheduler()
