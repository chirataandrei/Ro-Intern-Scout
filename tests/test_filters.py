import unittest

from internscout.emailer import build_email
from internscout.filters import (
    is_internship,
    is_romania,
    is_spring_week,
    is_student_entry,
    is_tech_role,
    keep_job,
)
from internscout.models import Job


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
        self.assertTrue(is_romania("ROM"))
        self.assertFalse(is_romania("London, United Kingdom"))
        self.assertFalse(is_romania("New York, NY"))

    def test_tech_and_keep(self) -> None:
        self.assertTrue(is_tech_role("IT Internship"))
        self.assertTrue(is_tech_role("Data Science Intern"))
        self.assertFalse(is_tech_role("Sales Internship Employer Branding"))
        self.assertTrue(keep_job(title="Software Engineering Intern", location="Bucharest, Romania"))
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
        self.assertTrue(is_spring_week("Software Engineer - Spring Insight Week"))
        self.assertTrue(is_student_entry("Jane Street Spring Week 2027"))
        self.assertTrue(
            keep_job(
                title="Software Engineer Intern",
                location="London, UK",
                category="quant",
            )
        )
        self.assertTrue(
            keep_job(
                title="Spring Insight Programme",
                location="Amsterdam",
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

    def test_email_mentions_new_count(self) -> None:
        job = Job(
            uid="t:1",
            company="Google",
            category="faang",
            title="Software Engineering Intern",
            location="Bucharest",
            url="https://example.com",
            source="google",
        )
        subject, plain, html_body = build_email([job], [job])
        self.assertIn("1 new", subject)
        self.assertIn("Google", plain)
        self.assertIn("Software Engineering Intern", html_body)


if __name__ == "__main__":
    unittest.main()
