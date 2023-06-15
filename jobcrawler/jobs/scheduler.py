from apscheduler.schedulers.background import BackgroundScheduler

sched = BackgroundScheduler(timezone="UTC", job_defaults={"max_instances": 4})
