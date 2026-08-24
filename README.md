# internscout

Daily email digest of:

- **SWE / data / quant internships** located in **Romania** (company name, title, city, apply URL)
- **Spring weeks** / insight programmes **outside the US and Canada** (UK / EU). Regular internships abroad are ignored.

Sources: Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee, Teamtailor, Workday, Personio, Breezy, Pinpoint, BambooHR, Eightfold, Comeet, iCIMS, SuccessFactors, Join, Rippling, JazzHR, Freshteam, Softgarden, Jobsoid, plus generic career-page JSON-LD. Aggregators: **Hipo, eJobs, BestJobs, Stagii pe Bune, Undelucram, Juniors.ro, NoFluffJobs**, and the [Simplify / Pitt CSC](https://github.com/SimplifyJobs/Summer2027-Internships) intern list.

## What you get

Every day around 08:00 (Romania time, summer) an email with **all currently open** matching roles, Romania first. New postings since yesterday are marked **NEW**.

Aggregator listings (eJobs / Hipo / BestJobs) show the **employer name**, not the board name.

## Run locally

```bash
cd ro-intern-scout
python3 -m internscout scan --no-save
```

Prints currently open roles without marking them as seen.

With email:

```bash
cp .env.example .env
# fill in SMTP_USER, SMTP_PASS, EMAIL_TO
python3 -m internscout scan --email
```

### Gmail

1. Google Account → [App passwords](https://myaccount.google.com/apppasswords) (2FA must be on)
2. Generate an app password
3. `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER` = your address, `SMTP_PASS` = the app password

## GitHub Action (daily robot)

1. Push this repo to GitHub
2. Settings → Secrets and variables → Actions, add:
   - `SMTP_USER`
   - `SMTP_PASS`
   - `EMAIL_TO`
   - optional: `SMTP_HOST` (default `smtp.gmail.com`), `SMTP_PORT` (`587`), `EMAIL_FROM`
3. Actions → **Daily internship digest** → Run workflow, to receive the first digest

`data/seen.json` is updated by the Action after each successful run, so already-seen roles are not marked NEW again.

## Add a company

Edit [`data/companies.json`](data/companies.json):

```json
{
  "name": "NXP",
  "category": "rd",
  "ats": "workday",
  "token": "nxp",
  "host": "nxp.wd3.myworkdayjobs.com",
  "site": "careers",
  "sites": [
    {
      "ats": "workday",
      "token": "nxp",
      "host": "nxp.wd3.myworkdayjobs.com",
      "site": "careers",
      "url": "https://nxp.wd3.myworkdayjobs.com/careers"
    },
    {
      "ats": "careers",
      "host": "https://www.nxp.com/company/about-nxp/careers:CAREERS",
      "url": "https://www.nxp.com/company/about-nxp/careers:CAREERS"
    }
  ],
  "urls": [
    "https://nxp.wd3.myworkdayjobs.com/careers",
    "https://www.nxp.com/company/about-nxp/careers:CAREERS"
  ]
}
```

`sites` is one or more boards where that firm posts jobs (Workday, Greenhouse, Lever, official careers page, …). The scanner fetches each ATS board. `urls` is the public list of those announcement sites.

`ats` can be: `greenhouse`, `lever`, `ashby`, `smartrecruiters`, `workable`, `recruitee`, `teamtailor`, `workday`, `personio`, `breezy`, `pinpoint`, `bamboohr`, `eightfold`, `comeet`, `icims`, `successfactors`, `join`, `rippling`, `jazzhr`, `freshteam`, `softgarden`, `jobsoid`, `careers`, `google`, `amazon`, `microsoft`, `meta`, `apple`.

Workday also needs `host` and `site`. The Greenhouse token is the slug in `job-boards.greenhouse.io/{token}`.

## Tests

```bash
python3 -m unittest tests.test_filters -v
```

## Limits

- No paid LinkedIn / SerpAPI — public sources only
- Internships stay filtered to Romania; **spring weeks** are UK/EU only (US and Canada are dropped)
- Some career pages (Workday, Microsoft) may return 403/422; Hipo / eJobs / BestJobs / Simplify fill some of the gaps
- Hipo has scheduled maintenance 31 Aug – 4 Sep 2026
- Spring-week seasons are typically January–March; in late summer that section is often empty
