from django.core.management.base import BaseCommand

from ingestion.fetchers.runner import run_fetcher
from ingestion.fetchers.veolia_web import VeoliaWebFetcher


class Command(BaseCommand):
    help = "Fetch Veolia's 3-page outage listing and store each page as raw content."

    def handle(self, *args, **options):
        summary = run_fetcher(VeoliaWebFetcher())
        style = self.style.SUCCESS if summary["error"] == 0 else self.style.WARNING
        self.stdout.write(style(str(summary)))
