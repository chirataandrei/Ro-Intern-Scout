import json
import os
import tempfile
import unittest
from pathlib import Path

from internscout.discover import boards_from_serp, extract_board
from internscout.models import Job
from internscout.net.apify import ApifyState
from internscout.sources.feeds.apify_scout import _to_job


class ExtractBoardTests(unittest.TestCase):
    def test_known_patterns(self) -> None:
        cases = [
            ("https://jobs.ashbyhq.com/supabase?utm=1", "ashby", "supabase"),
            ("https://job-boards.greenhouse.io/grafanalabs/jobs/123", "greenhouse", "grafanalabs"),
            ("https://jobs.lever.co/nexo/abc", "lever", "nexo"),
            ("https://apply.workable.com/payhawk/", "workable", "payhawk"),
            ("https://vinted.recruitee.com/o/intern", "recruitee", "vinted"),
            ("https://deepl.jobs.personio.com/", "personio", "deepl"),
            ("https://bitdefender.breezy.hr/", "breezy", "bitdefender"),
            ("https://mollie.teamtailor.com/jobs", "teamtailor", "mollie"),
            ("https://join.com/companies/qonto/123", "join", "qonto"),
            ("https://ats.rippling.com/n8n/jobs", "rippling", "n8n"),
        ]
        for url, ats, token in cases:
            self.assertEqual(extract_board(url), (ats, token), url)

    def test_unrelated_url(self) -> None:
        self.assertIsNone(extract_board("https://example.com/careers"))

    def test_serp_items(self) -> None:
        items = [
            {"url": "https://jobs.ashbyhq.com/neon"},
            {"organicResults": [{"url": "https://jobs.lever.co/clerk"}]},
            {"url": "https://jobs.ashbyhq.com/neon/job/1"},
        ]
        boards = boards_from_serp(items)
        pairs = {(b["ats"], b["token"]) for b in boards}
        self.assertEqual(pairs, {("ashby", "neon"), ("lever", "clerk")})


class ApifyScoutMappingTests(unittest.TestCase):
    def test_wellfound_payload(self) -> None:
        job = _to_job(
            {
                "id": "wf-99",
                "query_id": "wellfound",
                "title": "Software Engineering Intern",
                "companyName": "Deepstash",
                "location": "Bucharest",
                "workplaceType": "Remote",
                "url": "https://wellfound.com/jobs/99?utm_source=x",
                "postedAt": "2026-08-01",
                "category": "product",
            }
        )
        self.assertIsNotNone(job)
        assert job is not None
        self.assertEqual(job.uid, "apify:wellfound:wf-99")
        self.assertEqual(job.company, "Deepstash")
        self.assertEqual(job.source, "apify")
        self.assertIn("Remote", job.location)
        self.assertNotIn("utm_source", job.url)

    def test_nested_company_and_url_fallback(self) -> None:
        job = _to_job(
            {
                "title": "Intern",
                "startup": {"name": "Planable"},
                "jobUrl": "https://jobs.ashbyhq.com/planable/intern-1",
            }
        )
        self.assertIsNotNone(job)
        assert job is not None
        self.assertEqual(job.company, "Planable")
        self.assertEqual(job.uid, "apify:wellfound:intern-1")


class BudgetGuardTests(unittest.TestCase):
    def test_new_month_resets(self) -> None:
        state = ApifyState(month="2020-01", runs=80, spent_usd=4.0, last_run="2020-01-15T00:00:00+00:00")
        rolled = state.rolled_over()
        self.assertEqual(rolled.runs, 0)
        self.assertEqual(rolled.spent_usd, 0.0)
        ok, _ = rolled.can_run()
        self.assertTrue(ok)

    def test_exhausted_budget_blocks(self) -> None:
        os.environ["APIFY_MAX_SPEND_PER_MONTH"] = "1.00"
        try:
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            state = ApifyState(month=now.strftime("%Y-%m"), runs=1, spent_usd=1.50, last_run="")
            ok, reason = state.can_run(now)
            self.assertFalse(ok)
            self.assertIn("budget", reason)
        finally:
            os.environ.pop("APIFY_MAX_SPEND_PER_MONTH", None)

    def test_cooldown(self) -> None:
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        state = ApifyState(
            month=now.strftime("%Y-%m"),
            runs=1,
            spent_usd=0.1,
            last_run=(now - timedelta(hours=1)).isoformat(),
        )
        os.environ["APIFY_MIN_HOURS_BETWEEN_RUNS"] = "6"
        try:
            ok, reason = state.can_run(now)
            self.assertFalse(ok)
            self.assertIn("cooldown", reason)
            skipped, _ = state.can_run(now, check_cooldown=False)
            self.assertTrue(skipped)
        finally:
            os.environ.pop("APIFY_MIN_HOURS_BETWEEN_RUNS", None)

    def test_save_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "apify_state.json"
            state = ApifyState(month="2026-08", runs=3, spent_usd=1.23456, last_run="2026-08-30T06:00:00+00:00")
            state.save(path)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["runs"], 3)
            self.assertAlmostEqual(loaded["spent_usd"], 1.2346)
            again = ApifyState.load(path)
            self.assertEqual(again.runs, 3)
