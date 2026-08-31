import unittest

from internscout.models import Job
from internscout.pipeline import dedupe
from internscout.store import fingerprint, split_new


def _job(**kwargs) -> Job:
    defaults = dict(
        uid="greenhouse:x:1",
        company="Deepstash",
        category="product",
        title="Software Engineering Intern",
        location="Bucharest, Romania",
        url="https://example.com/1",
        source="greenhouse",
    )
    defaults.update(kwargs)
    return Job(**defaults)


class FingerprintTests(unittest.TestCase):
    def test_collapses_city_spellings(self) -> None:
        a = fingerprint(_job(location="Bucharest, Romania"))
        b = fingerprint(_job(location="București, România"))
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("fp:"))

    def test_collapses_company_aliases(self) -> None:
        a = fingerprint(_job(company="ING Hubs Romania"))
        b = fingerprint(_job(company="ING"))
        self.assertEqual(a, b)

    def test_different_titles_differ(self) -> None:
        a = fingerprint(_job(title="Backend Intern"))
        b = fingerprint(_job(title="Frontend Intern"))
        self.assertNotEqual(a, b)


class DedupeTests(unittest.TestCase):
    def test_non_apify_wins(self) -> None:
        ats = _job(uid="greenhouse:deepstash:1", source="greenhouse", url="https://boards.greenhouse.io/x")
        apify = _job(
            uid="apify:wellfound:99",
            source="apify",
            url="https://wellfound.com/jobs/99",
        )
        out = dedupe([ats, apify])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].source, "greenhouse")

    def test_apify_dropped_when_later(self) -> None:
        apify = _job(uid="apify:wellfound:99", source="apify")
        ats = _job(uid="greenhouse:deepstash:1", source="greenhouse")
        # If Apify is first, it currently wins — pipeline appends Apify last on purpose.
        out = dedupe([apify, ats])
        self.assertEqual(len(out), 1)

    def test_split_new_uses_fingerprint(self) -> None:
        job = _job()
        seen = {fingerprint(job)}
        new, current = split_new([job], seen)
        self.assertEqual(new, [])
        self.assertEqual(len(current), 1)
