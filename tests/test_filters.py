import json
import unittest

from internscout.emailer import build_email
from internscout.filters import (
    is_america,
    is_internship,
    is_romania,
    is_spring_week,
    is_student_entry,
    is_tech_role,
    keep_job,
)
from internscout.models import Job
from internscout.sources.ejobs import jobs_from_nuxt


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
        from internscout.sources.workday import build_job_url

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
        from internscout.sources.workday import build_job_url

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
        from internscout.sources.stagiipebune import parse_listings

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
        from internscout.models import COMPANIES_PATH, Company

        raw = json.loads(COMPANIES_PATH.read_text(encoding="utf-8"))
        self.assertGreater(len(raw), 200)
        missing = [row["name"] for row in raw if not row.get("urls")]
        self.assertEqual(missing, [])

    def test_nxp_and_bosch_have_multiple_sites(self) -> None:
        from internscout.models import COMPANIES_PATH, Company

        raw = json.loads(COMPANIES_PATH.read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    unittest.main()
