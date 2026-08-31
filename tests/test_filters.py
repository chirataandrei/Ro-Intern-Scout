import json
import unittest

from internscout.emailer import build_email
from internscout.filters import (
    is_america,
    is_internship,
    is_remote_eu,
    is_romania,
    is_spring_week,
    is_student_entry,
    is_tech_role,
    keep_job,
)
from internscout.models import Job
from internscout.sources.feeds.ejobs import jobs_from_nuxt


class FilterTests(unittest.TestCase):
    def test_internship_keywords(self) -> None:
        self.assertTrue(is_internship("Software Engineering Intern"))
        self.assertTrue(is_internship("Internship IT — programare"))
        self.assertTrue(is_internship("Stagiu de practică Python"))
        self.assertTrue(is_internship("Program de internship Backend"))
        self.assertFalse(is_internship("Software Engineer"))
        self.assertFalse(is_internship("Internal Tools Engineer"))
        self.assertFalse(is_internship("International Expansion Manager"))

    def test_romania_locations(self) -> None:
        self.assertTrue(is_romania("Bucharest, Romania"))
        self.assertTrue(is_romania("București"))
        self.assertTrue(is_romania("Cluj-Napoca, RO"))
        self.assertTrue(is_romania("Iasi, Romania"))
        self.assertTrue(is_romania("Odorheiu Secuiesc, Romania"))
        self.assertTrue(is_romania("ROM"))
        self.assertFalse(is_romania("London, United Kingdom"))
        self.assertFalse(is_romania("New York, NY"))

    def test_america_locations(self) -> None:
        self.assertTrue(is_america("Chicago, IL"))
        self.assertTrue(is_america("New York, NY"))
        self.assertTrue(is_america("Remote in USA"))
        self.assertTrue(is_america("Toronto, Canada"))
        self.assertFalse(is_america("London, United Kingdom"))
        self.assertFalse(is_america("Amsterdam"))
        self.assertFalse(is_america("Bucharest, Romania"))

    def test_tech_and_keep(self) -> None:
        self.assertTrue(is_tech_role("IT Internship"))
        self.assertTrue(is_tech_role("Data Science Intern"))
        self.assertFalse(is_tech_role("Sales Internship Employer Branding"))
        self.assertTrue(keep_job(title="Software Engineering Intern", location="Bucharest, Romania"))
        self.assertTrue(keep_job(title="DevOps Intern", location="Bucharest", company="NXP"))
        self.assertFalse(keep_job(title="Software Engineering Intern", location="London, UK"))
        self.assertTrue(
            keep_job(
                title="IT Internship",
                location="Hybrid",
                from_aggregator=True,
                already_romania=True,
            )
        )
        self.assertFalse(
            keep_job(
                title="Sales Internship",
                location="București",
                from_aggregator=True,
                already_romania=True,
            )
        )
        self.assertFalse(
            keep_job(
                title="Conferinta gratuita Angajatori de TOP",
                location="București",
                already_romania=True,
                from_aggregator=True,
            )
        )
        self.assertFalse(
            keep_job(
                title="Internship for Accounting",
                location="Timișoara, Romania",
            )
        )
        self.assertTrue(
            keep_job(
                title="Internship for Software Test Engineer",
                location="Iași, Romania",
            )
        )
        self.assertFalse(
            keep_job(
                title="Programe de internship, trainee sau joburi entry-level in IT",
                location="Romania",
                company="JumpStart - A GenZ Career Hub",
                from_aggregator=True,
            )
        )
        self.assertTrue(is_spring_week("Software Engineer - Spring Insight Week"))
        self.assertTrue(is_spring_week("FutureFocus: Quants"))
        self.assertTrue(is_spring_week("First-Year Trading and Technology Program"))
        self.assertTrue(is_spring_week("Discover Citadel — London"))
        self.assertTrue(is_spring_week("Discover DRW"))
        self.assertTrue(is_spring_week("Maven Minds"))
        self.assertTrue(is_spring_week("Women in Trading Insight Programme"))
        self.assertTrue(is_spring_week("Women in Quant Investing - Spring Insights Day"))
        self.assertTrue(is_spring_week("FTTP"))
        self.assertTrue(
            keep_job(
                title="FutureFocus: Quants",
                location="Amsterdam",
                category="quant",
            )
        )
        self.assertTrue(is_student_entry("Jane Street Spring Week 2027"))
        self.assertFalse(
            keep_job(
                title="Software Engineer Intern",
                location="London, UK",
                category="quant",
            )
        )
        self.assertFalse(
            keep_job(
                title="Software Engineer Intern - C++",
                location="Chicago, IL",
                category="quant",
                company="Akuna Capital",
            )
        )
        self.assertTrue(
            keep_job(
                title="Spring Insight Programme",
                location="Amsterdam",
                category="quant",
            )
        )
        self.assertTrue(
            keep_job(
                title="Jane Street Spring Week 2027",
                location="London, UK",
                category="quant",
            )
        )
        self.assertFalse(
            keep_job(
                title="Spring Insight Programme",
                location="New York, NY",
                category="quant",
            )
        )
        self.assertFalse(
            keep_job(
                title="Software Engineer Intern",
                location="London, UK",
                category="faang",
            )
        )
        self.assertFalse(
            keep_job(
                title="Quantitative Researcher",
                location="New York",
                category="quant",
            )
        )
        self.assertTrue(
            keep_job(
                title="Software Development Internships in Transylvania",
                location="Cluj-Napoca, Romania",
                company="SOFTECH SRL",
                from_aggregator=True,
            )
        )
        self.assertFalse(
            keep_job(
                title="Odorhei Software Development Summer Internship Has Started!",
                location="Romania",
                company="eJobs",
                from_aggregator=True,
            )
        )
        self.assertTrue(
            keep_job(
                title="Software Engineer",
                location="București",
                company="FotoNation",
                from_aggregator=True,
                assume_internship=True,
            )
        )

    def test_remote_eu_locations(self) -> None:
        self.assertTrue(is_remote_eu("Remote - Europe"))
        self.assertTrue(is_remote_eu("EU Remote"))
        self.assertTrue(is_remote_eu("Remote (CET)"))
        self.assertTrue(is_remote_eu("Remote, Germany"))
        self.assertTrue(is_remote_eu("Fully Remote"))
        self.assertTrue(is_remote_eu("Work from anywhere"))
        self.assertFalse(is_remote_eu("Remote - US"))
        self.assertFalse(is_remote_eu("Remote, Worldwide"))
        self.assertFalse(is_remote_eu("London, United Kingdom"))  # no "remote" keyword

    def test_remote_eu_internship_is_kept_but_us_and_non_tech_are_not(self) -> None:
        self.assertTrue(
            keep_job(
                title="Backend Engineering Intern",
                location="Remote - Europe",
                company="Supabase",
            )
        )
        self.assertTrue(
            keep_job(
                title="Software Engineer Internship",
                location="EU Remote",
                company="Mistral AI",
            )
        )
        self.assertFalse(
            keep_job(
                title="Sales Intern",
                location="Remote - Europe",
                company="Some Startup",
            )
        )
        self.assertFalse(
            keep_job(
                title="Backend Engineering Intern",
                location="Remote - US",
                company="Some Startup",
            )
        )
        self.assertFalse(
            keep_job(
                title="Backend Engineering Intern",
                location="London, United Kingdom",
                company="Some Startup",
            )
        )
        # Spring weeks abroad still work without the "remote" keyword.
        self.assertTrue(
            keep_job(
                title="Spring Insight Programme",
                location="Amsterdam",
                category="quant",
            )
        )

    def test_email_lists_company_and_romania_first(self) -> None:
        nxp = Job(
            uid="nxp:1",
            company="NXP",
            category="rd",
            title="DevOps Intern",
            location="Bucharest, Romania",
            url="https://nxp.wd3.myworkdayjobs.com/careers/job/Bucharest/DevOps-Intern_R-10066169",
            source="workday",
        )
        softech = Job(
            uid="ejobs:1",
            company="SOFTECH SRL",
            category="aggregator",
            title="Software Development Internships in Transylvania",
            location="Cluj-Napoca, Romania",
            url="https://www.ejobs.ro/softech",
            source="ejobs",
        )
        spring = Job(
            uid="js:1",
            company="Jane Street",
            category="quant",
            title="Spring Week 2027",
            location="London, UK",
            url="https://example.com/js",
            source="greenhouse",
        )
        subject, plain, html_body = build_email([nxp], [nxp, softech, spring])
        self.assertIn("1 new", subject)
        self.assertIn("Company:  NXP", plain)
        self.assertIn("Company:  SOFTECH SRL", plain)
        self.assertNotIn("Hipo / eJobs / BestJobs", plain)
        self.assertNotIn("Hipo / eJobs / BestJobs", html_body)
        self.assertLess(plain.find("SOFTECH SRL"), plain.find("Jane Street"))
        self.assertLess(html_body.find("NXP"), html_body.find("Jane Street"))
        self.assertIn("/careers/job/Bucharest/", html_body)

    def test_ejobs_nuxt_exposes_company_name(self) -> None:
        payload = [
            None,
            {"id": 2, "title": 3, "company": 4, "locations": 7, "slug": 8},
            1977209,
            "Odorhei Software Development Summer Internship Has Started!",
            {"id": 5, "name": 6, "slug": 9},
            357204,
            "SOFTECH SRL",
            [{"cityId": 10}],
            "odorhei-software-development-summer-internship-has-started",
            "softech-srl",
            279,
            {"name": 12, "id": 13, "faecetType": 14},
            "Odorheiu Secuiesc",
            279,
            "cities",
        ]
        html = '<script id="__NUXT_DATA__">' + json.dumps(payload) + "</script>"
        jobs = jobs_from_nuxt(html)
        self.assertEqual(len(jobs), 1)
        job_id, title, company, location, url = jobs[0]
        self.assertEqual(job_id, "1977209")
        self.assertEqual(company, "SOFTECH SRL")
        self.assertIn("Odorheiu Secuiesc", location)
        self.assertIn("1977209", url)


class WorkdayUrlTests(unittest.TestCase):
    def test_nxp_includes_careers_site(self) -> None:
        from internscout.sources.ats.workday import build_job_url

        url = build_job_url(
            "nxp.wd3.myworkdayjobs.com",
            "careers",
            "/job/Bucharest/DevOps-Intern_R-10066169",
        )
        self.assertEqual(
            url,
            "https://nxp.wd3.myworkdayjobs.com/careers/job/Bucharest/DevOps-Intern_R-10066169",
        )
        self.assertNotEqual(
            url,
            "https://nxp.wd3.myworkdayjobs.com/job/Bucharest/DevOps-Intern_R-10066169",
        )

    def test_does_not_double_site_prefix(self) -> None:
        from internscout.sources.ats.workday import build_job_url

        url = build_job_url(
            "nxp.wd3.myworkdayjobs.com",
            "careers",
            "/careers/job/Bucharest/DevOps-Intern_R-10066169",
        )
        self.assertEqual(
            url,
            "https://nxp.wd3.myworkdayjobs.com/careers/job/Bucharest/DevOps-Intern_R-10066169",
        )


class StagiiPeBuneTests(unittest.TestCase):
    def test_parses_company_title_city(self) -> None:
        from internscout.sources.feeds.stagiipebune import parse_listings

        html = """
        <tbody class="job-table-body company-group">
          <tr>
            <td class="job-row">
              <p class="job-row-title bold">
                <a class="color-emphasis" href="/jobs/veridion/deeptech-engineer-intern-32247">Deeptech Engineer Intern</a>
              </p>
              <p class="job-row-sub">
                <span class="bold"><a class="color-link" href="/company_profile/veridion">Veridion</a></span>
                <span class="muted">· Plătit: 1000 EUR net</span>
                <span class="muted">28 Feb</span>
                <span class="muted">București</span>
              </p>
            </td>
          </tr>
        </tbody>
        """
        jobs = parse_listings(html)
        self.assertEqual(len(jobs), 1)
        job_id, title, company, location, href = jobs[0]
        self.assertEqual(company, "Veridion")
        self.assertEqual(title, "Deeptech Engineer Intern")
        self.assertEqual(location, "București")
        self.assertIn("/jobs/veridion/", href)


class CatalogSiteTests(unittest.TestCase):
    def test_every_company_has_announcement_urls(self) -> None:
        from internscout.catalog.loader import load_companies_raw

        raw = load_companies_raw()
        self.assertGreaterEqual(len(raw), 400)
        missing = [row["name"] for row in raw if not row.get("urls")]
        self.assertEqual(missing, [])
        names = {row["name"] for row in raw}
        self.assertIn("Accesa", names)
        self.assertIn("AROBS", names)
        self.assertIn("Nagarro", names)
        self.assertIn("Barclays", names)
        self.assertIn("Canonical", names)

    def test_new_ats_are_registered(self) -> None:
        from internscout.career_sites import board_public_url
        from internscout.sources.registry import FETCHERS

        for ats in ("join", "rippling", "jazzhr", "freshteam", "softgarden", "jobsoid"):
            self.assertIn(ats, FETCHERS)
        self.assertEqual(board_public_url("join", "n26"), "https://join.com/companies/n26")
        self.assertEqual(board_public_url("rippling", "rippling"), "https://ats.rippling.com/rippling/jobs")
        self.assertEqual(board_public_url("jazzhr", "acme"), "https://acme.applytojob.com/")
        self.assertEqual(board_public_url("freshteam", "acme"), "https://acme.freshteam.com/jobs")
        self.assertEqual(board_public_url("jobsoid", "bunnyshell"), "https://bunnyshell.jobsoid.com/")

    def test_nxp_and_bosch_have_multiple_sites(self) -> None:
        from internscout.catalog.loader import load_companies_raw
        from internscout.models import Company

        raw = load_companies_raw()
        by_name = {row["name"]: Company.from_dict(row) for row in raw}
        nxp = by_name["NXP"]
        self.assertGreaterEqual(len(nxp.sites), 2)
        nxp_urls = " ".join(str(site.get("url") or "") for site in nxp.sites)
        self.assertIn("nxp.wd3.myworkdayjobs.com/careers", nxp_urls)
        self.assertIn("nxp.com", nxp_urls)
        bosch = by_name["Bosch"]
        self.assertGreaterEqual(len(bosch.sites), 3)
        bosch_urls = " ".join(str(site.get("url") or "") for site in bosch.sites)
        self.assertIn("smartrecruiters.com/BoschGroup", bosch_urls)
        self.assertIn("bosch.ro/cariera", bosch_urls)
        self.assertGreaterEqual(len(bosch.boards()), 2)


class UndelucramTests(unittest.TestCase):
    def test_sitemap_keeps_internships_not_internal_auditor(self) -> None:
        from internscout.sources.feeds.undelucram import intern_job_urls

        xml = """
        <urlset>
          <loc>https://www.undelucram.ro/ro/locuri-de-munca/technical-internship-at-aumovio-tm/96894</loc>
          <loc>https://www.undelucram.ro/ro/locuri-de-munca/quality-manager-certified-internal-auditor-iso-90012015/30278</loc>
          <loc>https://www.undelucram.ro/ro/locuri-de-munca?page=1</loc>
        </urlset>
        """
        urls = intern_job_urls(xml)
        self.assertEqual(len(urls), 1)
        self.assertIn("technical-internship-at-aumovio", urls[0])

    def test_jsonld_exposes_employer_name(self) -> None:
        from internscout.sources.feeds.undelucram import jobs_from_detail

        html = """
        <script type="application/ld+json">
        {
          "@context": "https://schema.org/",
          "@type": "JobPosting",
          "title": "Technical Internship at AUMOVIO (TM)",
          "url": "https://www.undelucram.ro/ro/locuri-de-munca/technical-internship-at-aumovio-tm/96894",
          "hiringOrganization": {"@type": "Organization", "name": "AUMOVIO"},
          "jobLocation": {"@type": "Place", "address": {"addressLocality": "Timisoara", "addressCountry": "Romania"}}
        }
        </script>
        <a href="https://jobs.smartrecruiters.com/AUMOVIO/744000000">Apply</a>
        """
        jobs = jobs_from_detail(html, "https://www.undelucram.ro/ro/locuri-de-munca/technical-internship-at-aumovio-tm/96894")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].company, "AUMOVIO")
        self.assertEqual(jobs[0].title, "Technical Internship at AUMOVIO (TM)")
        self.assertIn("Timisoara", jobs[0].location)
        self.assertIn("smartrecruiters.com/AUMOVIO", jobs[0].url)
        self.assertEqual(jobs[0].source, "undelucram")


class JoinAndNoFluffTests(unittest.TestCase):
    def test_join_company_id_from_html(self) -> None:
        from internscout.sources.ats.join import company_id_from_html

        html = '{"props":{"pageProps":{"company":{"id":106934,"name":"N26"}}}}'
        self.assertEqual(company_id_from_html(html), "106934")

    def test_nofluffjobs_maps_employer_and_city(self) -> None:
        from internscout.sources.feeds.nofluffjobs import jobs_from_postings

        jobs = jobs_from_postings(
            [
                {
                    "id": "java-intern-accesa-bucharest",
                    "title": "Java Intern",
                    "name": "Accesa",
                    "location": {
                        "places": [
                            {
                                "city": "Bucharest",
                                "country": {"code": "ROM", "name": "Romania"},
                            }
                        ]
                    },
                }
            ]
        )
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].company, "Accesa")
        self.assertIn("Bucharest", jobs[0].location)
        self.assertIn("Romania", jobs[0].location)
        self.assertIn("/job/java-intern-accesa-bucharest", jobs[0].url)


class ReportCatalogTests(unittest.TestCase):
    def test_new_firms_and_official_sites(self) -> None:
        from internscout.career_sites import official_urls
        from internscout.catalog.loader import load_companies_raw

        names = {row["name"] for row in load_companies_raw()}
        for name in (
            "Visma",
            "Kaseya",
            "Bunnyshell",
            "Elektrobit",
            "Systematic",
            "Stefanini",
            "Computacenter",
            "ADP",
            "Amdocs",
            "Da Vinci Derivatives",
            "GSA Capital",
            "Vector Informatik",
        ):
            self.assertIn(name, names)
        self.assertTrue(any("join.vector.com" in url for url in official_urls("Vector Informatik")))
        self.assertEqual(official_urls("Visma"), ["https://www.visma.com/careers"])
        self.assertTrue(any("gsacapital.com" in url for url in official_urls("GSA Capital")))

        catalog = load_companies_raw()
        bunnyshell = next(row for row in catalog if row["name"] == "Bunnyshell")
        self.assertEqual(bunnyshell["ats"], "jobsoid")
        visma = next(row for row in catalog if row["name"] == "Visma")
        self.assertEqual(visma["ats"], "teamtailor")
        self.assertEqual(visma["token"], "vismacc")

    def test_juniors_card_uses_employer_not_board_name(self) -> None:
        from internscout.sources.feeds.juniors import parse_listings

        html = """
        <div class="job_header">
            <div class="job_header_logo">
                <img src="https://cdn.juniors.ro/uploads/company-logos/betfair.jpg"/>
            </div>
            <div class="job_header_title">
                <h3>Internship Data Engineer - (3 months)</h3>
                <strong>Cluj-Napoca | 2 săptămâni în urmă</strong>
            </div>
            <a id="job_link_14054" href="/jobs/14054">Open</a>
        </div>
        """
        rows = parse_listings(html)
        self.assertEqual(len(rows), 1)
        job_id, title, company, location = rows[0]
        self.assertEqual(job_id, "14054")
        self.assertIn("Internship Data Engineer", title)
        self.assertEqual(company, "Betfair")
        self.assertEqual(location, "Cluj-Napoca")

    def test_teamtailor_json_feed_reads_jobposting_location(self) -> None:
        from internscout.models import Company
        from internscout.sources.ats.teamtailor import fetch_jobs

        feed = {
            "version": "https://jsonfeed.org/version/1.1",
            "items": [
                {
                    "id": "338f6310",
                    "title": "QA Intern @Visma",
                    "url": "https://vismacc.teamtailor.com/jobs/8161880-qa-intern",
                    "date_published": "2026-08-01T00:00:00Z",
                    "_jobposting": {
                        "@type": "JobPosting",
                        "title": "QA Intern @Visma",
                        "url": "https://vismacc.teamtailor.com/jobs/8161880-qa-intern",
                        "jobLocation": [
                            {
                                "@type": "Place",
                                "address": {
                                    "addressLocality": "Iași",
                                    "addressCountry": "RO",
                                    "addressRegion": "Romania",
                                },
                            }
                        ],
                    },
                }
            ],
        }

        class FakeHttp:
            def get_json(self, url: str):
                return 200, feed

            def get(self, url: str, **kwargs):
                return 404, ""

        jobs = fetch_jobs(Company(name="Visma", category="product", ats="teamtailor", token="vismacc"), FakeHttp())
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "QA Intern @Visma")
        self.assertIn("Iași", jobs[0].location)
        self.assertIn("Romania", jobs[0].location)


if __name__ == "__main__":
    unittest.main()
