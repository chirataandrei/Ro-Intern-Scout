# internscout

Daily email digest of:

- **SWE / data / quant internships** in **Romania**
- **Remote internships (EU / EMEA)** — fully remote or remote-Europe, never US/Canada
- **Spring weeks** / insight programmes **outside the US and Canada** (UK / EU)

Sources: 28 ATS fetchers (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee, Teamtailor, Workday, Personio, Breezy, Pinpoint, BambooHR, Eightfold, Comeet, iCIMS, SuccessFactors, Join, Rippling, JazzHR, Freshteam, Softgarden, Jobsoid, plus career-page JSON-LD). Aggregators: **Hipo, eJobs, BestJobs, Stagii pe Bune, Undelucram, Juniors.ro, NoFluffJobs**, the [Simplify / Pitt CSC](https://github.com/SimplifyJobs/Summer2027-Internships) intern list, and free EU boards (**Arbeitnow, RemoteOK, Himalayas, Jobicy, We Work Remotely, Landing.jobs**). Blind spots (Wellfound, unknown ATS boards) come from an **Apify** cache, never from a live Apify call during the daily scan.

The catalog is sharded under `internscout/catalog/data/companies/*.json` (666 firms after live ATS probing; candidates without a fetchable board stay in `tools/candidates.json` for rediscovery).

## What you get

Every day around 08:00 (Romania time, summer) an email with **all currently open** matching roles, in three sections: Romania internships, remote-EU internships, spring weeks. New postings since yesterday are marked **NEW**.

## Run locally

```bash
cd ro-intern-scout
python3 -m internscout scan --no-save
```

```bash
cp .env.example .env
# fill in SMTP_USER, SMTP_PASS, EMAIL_TO
python3 -m internscout scan --email
```

Other commands:

```bash
python3 -m internscout apify-refresh --dry-run   # print actor input + estimated cost
python3 -m internscout discover --dry-run
python3 -m internscout probe --limit 5           # ATS slug probe (tools/probe_ats.py)
python3 -m internscout probe --write             # merge live boards into the catalog
```

### Gmail

1. Google Account → [App passwords](https://myaccount.google.com/apppasswords) (2FA must be on)
2. Generate an app password
3. `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER` = your address, `SMTP_PASS` = the app password

## GitHub Actions

**Daily internship digest** (`daily.yml`, 05:00 UTC): scan + email. Needs `SMTP_USER`, `SMTP_PASS`, `EMAIL_TO`.

**Apify refresh** (`apify.yml`, 03:30 / 11:30 / 17:30 UTC): discovery + Wellfound. Needs `APIFY_TOKEN`. Without the secret the job exits 0 and does nothing. Commits `data/apify_cache.json`, `data/apify_state.json`, `data/discovered.json`.

## Apify (blind spots only)

Free plan is **$5/month**. Budget lives in `data/apify_state.json`, capped by `APIFY_MAX_SPEND_PER_MONTH` (default 4.20), `APIFY_MAX_RUNS_PER_MONTH` (90), `APIFY_MIN_HOURS_BETWEEN_RUNS` (6).

- **Discovery** (`apify/google-search-scraper`): `site:` queries for Ashby/Greenhouse/Lever/… boards. New `(ats, token)` pairs go to `data/discovered.json`, get probed, then scanned **for free forever**.
- **Wellfound** (`memo23/wellfound-jobs-scraper`): listings land in `data/apify_cache.json`; `sources/feeds/apify_scout.py` only reads that file.
- The daily scan never calls Apify.

## Add a company

Add a row to the matching shard in [`internscout/catalog/data/companies/`](internscout/catalog/data/companies/) (`product.json`, `ssc.json`, `quant.json`, …). Official careers URLs go in [`official_careers.json`](internscout/catalog/data/official_careers.json); aliases in [`aliases.json`](internscout/catalog/data/aliases.json).

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
    }
  ]
}
```

`ats` can be: `greenhouse`, `lever`, `ashby`, `smartrecruiters`, `workable`, `recruitee`, `teamtailor`, `workday`, `personio`, `breezy`, `pinpoint`, `bamboohr`, `eightfold`, `comeet`, `icims`, `successfactors`, `join`, `rippling`, `jazzhr`, `freshteam`, `softgarden`, `jobsoid`, `careers`, `google`, `amazon`, `microsoft`, `meta`, `apple`.

To probe unknown slugs: `python3 tools/probe_ats.py --write` (uses `tools/candidates.json`).

## Tests

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_catalog.py
```

## Limits

- Internships: Romania **or** remote-EU. In-office roles abroad only keep spring / insight weeks. US and Canada are dropped everywhere.
- Some career pages (Workday, Microsoft) may return 403/422; aggregators and Apify discovery cover some of the gaps
- Hipo has scheduled maintenance 31 Aug – 4 Sep 2026
- Spring-week seasons are typically January–March; in late summer that section is often empty
- Apify is skipped entirely when `APIFY_TOKEN` is unset or the monthly budget is spent
