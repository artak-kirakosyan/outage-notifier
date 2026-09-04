import threading
import time

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ingestion.scheduler import Job, start_scheduler


class Command(BaseCommand):
    help = (
        "Run all Phase 0.5 fetchers forever, each on its own interval. "
        "This is the container's long-running scheduler process."
    )

    def handle(self, *args, **options):
        jobs = [
            Job(
                "fetch_ena",
                lambda: call_command("fetch_ena"),
                settings.ENA_FETCH_INTERVAL_MINUTES * 60,
            ),
            Job(
                "fetch_veolia_web",
                lambda: call_command("fetch_veolia_web"),
                settings.VEOLIA_WEB_FETCH_INTERVAL_MINUTES * 60,
            ),
            Job(
                "fetch_veolia_telegram",
                lambda: call_command("fetch_veolia_telegram"),
                settings.VEOLIA_TELEGRAM_FETCH_INTERVAL_MINUTES * 60,
            ),
        ]

        for job in jobs:
            self.stdout.write(f"Scheduling {job.name} every {job.interval_seconds // 60} min")

        stop_event = threading.Event()
        threads = start_scheduler(jobs, stop_event)

        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            self.stdout.write("Shutting down scheduler...")
            stop_event.set()
            for thread in threads:
                thread.join(timeout=5)
