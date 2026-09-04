from io import StringIO

import pytest
import responses
from django.core.management import call_command

from ingestion.fetchers.ena import ENAFetcher
from ingestion.fetchers.veolia_web import VeoliaWebFetcher
from ingestion.models import Provider, RawContent

pytestmark = pytest.mark.django_db


@responses.activate
def test_fetch_ena_command_creates_raw_row():
    responses.add(responses.GET, ENAFetcher.URL, body="<html>ok</html>", status=200)

    out = StringIO()
    call_command("fetch_ena", stdout=out)

    assert RawContent.objects.filter(provider=Provider.ENA).count() == 1
    assert "ok" in out.getvalue()  # summary dict prints without error


@responses.activate
def test_fetch_veolia_web_command_creates_three_raw_rows():
    fetcher = VeoliaWebFetcher()
    for page in fetcher.PAGES:
        responses.add(
            responses.GET, f"{fetcher.BASE_URL}&page={page}", body=f"<html>{page}</html>", status=200
        )

    call_command("fetch_veolia_web")

    assert RawContent.objects.filter(provider=Provider.VEOLIA_WEB).count() == 3


@responses.activate
def test_fetch_veolia_telegram_command_creates_raw_row():
    responses.add(
        responses.GET, "https://t.me/s/VeoliaJur", body="<div>post</div>", status=200
    )

    call_command("fetch_veolia_telegram")

    assert RawContent.objects.filter(provider=Provider.VEOLIA_TELEGRAM).count() == 1
