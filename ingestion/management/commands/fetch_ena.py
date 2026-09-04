from django.core.management.base import BaseCommand

from ingestion.fetchers.ena import ENAFetcher
from ingestion.fetchers.runner import run_fetcher


class Command(BaseCommand):
    help = "Fetch ENA's outage info page and store it as raw content."

    def handle(self, *args, **options):
        summary = run_fetcher(ENAFetcher())
        style = self.style.SUCCESS if summary["error"] == 0 else self.style.WARNING
        self.stdout.write(style(str(summary)))
