import unittest

from internscout.catalog.loader import VALID_CATEGORIES, load_companies
from internscout.catalog.naming import canonical_name
from internscout.sources.ats.registry import FETCHERS


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.companies = load_companies()

    def test_non_empty(self) -> None:
        self.assertGreaterEqual(len(self.companies), 452)

    def test_unique_canonical_names(self) -> None:
        seen: dict[str, str] = {}
        dupes = []
        for company in self.companies:
            key = canonical_name(company.name)
            if key in seen:
                dupes.append((seen[key], company.name, key))
            else:
                seen[key] = company.name
        self.assertEqual(dupes, [])

    def test_sites_and_ats(self) -> None:
        empty = []
        unknown = []
        bad_cat = []
        for company in self.companies:
            if not company.sites:
                empty.append(company.name)
            if company.category not in VALID_CATEGORIES:
                bad_cat.append((company.name, company.category))
            for board in company.sites:
                ats = str(board.get("ats") or "")
                if ats and ats not in FETCHERS:
                    unknown.append((company.name, ats))
        self.assertEqual(empty, [])
        self.assertEqual(unknown, [])
        self.assertEqual(bad_cat, [])
