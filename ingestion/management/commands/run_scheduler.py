import logging
import threading
import time

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ingestion.scheduler import Job, start_scheduler

logger = logging.getLogger(__name__)


def _make_guarded_run(command_name: str, enabled_setting_name: str):
    """
    Wrap a fetch management command so the SCHEDULER (only) respects the
    provider's enabled/disabled switch. The job's thread keeps running on
    its normal schedule either way — when disabled, each tick just logs
    and skips the actual fetch, rather than not being scheduled at all.
    That way turning a provider back on only means flipping the env var
    and restarting, not re-architecting anything.
    """

    def run_once() -> None:
        if not getattr(settings, enabled_setting_name):
            logger.info("'%s' is disabled, skipping...", command_name, )
            return
        call_command(command_name)

    return run_once


class Command(BaseCommand):
    help = (
        "Run all Phase 0.5 fetchers forever, each on its own interval. "
        "Providers can be disabled via *_FETCH_ENABLED settings/env "
        "(see .env.example) — the job stays scheduled and logs a skip "
        "message on each tick rather than being removed entirely."
    )

    def handle(self, *args, **options):
        jobs = [
            Job(
                "fetch_ena",
                _make_guarded_run("fetch_ena", "ENA_FETCH_ENABLED"),
                settings.ENA_FETCH_INTERVAL_MINUTES * 60,
            ),
            Job(
                "fetch_veolia_web",
                _make_guarded_run("fetch_veolia_web", "VEOLIA_WEB_FETCH_ENABLED"),
                settings.VEOLIA_WEB_FETCH_INTERVAL_MINUTES * 60,
            ),
            Job(
                "fetch_veolia_telegram",
                _make_guarded_run("fetch_veolia_telegram", "VEOLIA_TELEGRAM_FETCH_ENABLED"),
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
