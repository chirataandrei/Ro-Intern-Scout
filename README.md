# internscout

Daily email digest of:

- **SWE / data / quant internships** located in **Romania**
- **Spring weeks**, insight programmes, and other student-entry roles at **quant** firms (London / Amsterdam / US — that is where those programmes run)

Sources: Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee, Teamtailor, Workday, plus **Hipo, eJobs, BestJobs**, and the [Simplify / Pitt CSC](https://github.com/SimplifyJobs/Summer2027-Internships) intern list. The catalog has 300+ companies (FAANG, quant, Romanian product, R&D, telecom, SSC).

## What you get

Every day around 08:00 (Romania time, summer) an email with **new** postings since yesterday. If nothing is new: “0 new, X still open”.

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

`data/seen.json` is updated by the Action after each successful run, so you do not get the same jobs every day.

## Add a company

Edit [`data/companies.json`](data/companies.json):

```json
{
  "name": "UiPath",
  "category": "product",
  "ats": "greenhouse",
  "token": "board-token"
}
```

`ats` can be: `greenhouse`, `lever`, `ashby`, `smartrecruiters`, `workable`, `recruitee`, `teamtailor`, `workday`, `google`, `amazon`, `microsoft`, `meta`, `apple`.

Workday also needs `host` and `site`, for example:

```json
{
  "name": "Adobe",
  "category": "faang",
  "ats": "workday",
  "token": "adobe",
  "host": "adobe.wd5.myworkdayjobs.com",
  "site": "external_experienced"
}
```

The Greenhouse token is the slug in `boards.greenhouse.io/{token}`.

## Tests

```bash
python3 -m unittest tests.test_filters -v
```

## Limits

- No paid LinkedIn / SerpAPI — public sources only
- FAANG / product internships stay filtered to Romania; **quant student programmes** (intern, spring week, insight) are global
- Some career pages (Workday, Microsoft) may return 403/422; Hipo / eJobs / BestJobs / Simplify fill some of the gaps
- Hipo has scheduled maintenance 31 Aug – 4 Sep 2026
