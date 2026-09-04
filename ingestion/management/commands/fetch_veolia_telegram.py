from django.core.management.base import BaseCommand

from ingestion.fetchers.runner import run_fetcher
from ingestion.fetchers.veolia_telegram import VeoliaTelegramFetcher


class Command(BaseCommand):
    help = "Fetch Veolia's Telegram channel preview page and store it as raw content."

    def handle(self, *args, **options):
        summary = run_fetcher(VeoliaTelegramFetcher())
        style = self.style.SUCCESS if summary["error"] == 0 else self.style.WARNING
        self.stdout.write(style(str(summary)))
