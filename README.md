
# Job Outreach Bot (Personalized AI Job Email Generator + Gmail Draft Creator)

A Python-based automation tool that:
✔ Parses a job description  
✔ Personalizes a cold outreach email using your resume + writing style  
✔ Generates clean HTML emails  
✔ Creates a Gmail Draft with your resume attached  
✔ Keeps secrets local — no API keys in code  
✔ Helps you scale job searching without losing your personal voice

---

## 🌟 Features

- ✨ Write personalized hiring manager emails
- 🧠 Uses your actual resume text + style profile
- 🔗 Auto-inserts job posting hyperlinks
- 📬 Creates Gmail drafts instead of sending automatically
- 📎 Attaches your resume automatically
- 🎯 Optional job description analysis (finds best-match bullets)
- 🔥 Works with OpenRouter models (Mistral, Llama, etc.)
- 📊 **Batch processing** — Apply to multiple jobs at once
- 🌐 **Google Sheets integration** — Manage jobs & companies centrally
- 🔍 **Contact enrichment** — Hunter.io finds hiring manager emails
- 🏢 **Greenhouse token lookup** — Auto-discovers company Greenhouse boards

---

## 🛠️ Requirements

Install dependencies:

```bash
pip install -r requirements.txt
````

You must be in your virtual environment (`.venv` or `venv`) before running.

---

## 🔐 Setup

### 1️⃣ Create `.env` (not committed to git)

```
OPENROUTER_API_KEY=sk-or-xxxxx
HUNTER_API_KEY=xxxxx
SEARCH_API_KEY=AIzaXXXXXXX (optional, for Greenhouse lookup)
```

### 2️⃣ Configure Gmail API

Follow these steps once:

1. Go to [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Create an **OAuth Desktop Application**
3. Download `credentials.json` to repo root
4. Run the tool once and sign into Google
5. `token.json` will be created automatically

> ⚠ Never commit `.env`, `credentials.json`, or `token.json`.

---

## 📁 Directory Overview

```
job-outreach-bot/
 ├── main.py                          # CLI entrypoint (single email draft)
 ├── export_sheet_to_csv.py           # Download jobs from Google Sheets
 ├── build_job_list.py                # Filter & enrich jobs with contacts
 ├── batch_apply.py                   # Generate drafts for batch of jobs
 ├── requirements.txt                 # dependencies
 ├── jobs/                            # stored job descriptions
 ├── src/
 │   ├── email_generator.py           # AI email writer (OpenRouter)
 │   ├── gmail_client.py              # Gmail OAuth + service setup
 │   ├── gmail_draft.py               # create Gmail draft w/ resume
 │   ├── contact_enricher.py          # Hunter.io contact lookup
 │   ├── get_greenhouse_tokens.py     # Find Greenhouse board tokens
 │   ├── write_companies_to_sheet.py  # Write company data to Sheets
 │   ├── profile.py                   # your resume text for context
 │   ├── style_profile.py             # style profile loader
 │   ├── style_samples/               # previous emails to learn tone
 │   ├── links.py                     # LinkedIn, GitHub, portfolio URLs
 │   ├── job_profile_rules.py         # job title filtering rules
 │   └── scraper.py                   # job description scraper
 └── docs/
     └── Sanyuja_Desai_Resume.pdf
```

---

## 🚀 Usage

### Single Email (Manual)

```bash
python main.py \
  --title "Senior Data Scientist" \
  --url "https://example.com/job" \
  --manager "Sam Lee" \
  --company "Blue Rose Research" \
  --jd_file "jobs/blue_rose_senior_ds_risk.txt" \
  --create_draft \
  --to_email "sam@bluerose.com" \
  --resume_path "docs/Sanyuja_Desai_Resume.pdf"
```

### Batch Processing Pipeline

1. **Export jobs from Google Sheets:**
   ```bash
   python export_sheet_to_csv.py \
     --spreadsheet_id "YOUR_SHEET_ID" \
     --sheet_name "raw_jobs" \
     --output "jobs/raw_jobs.csv"
   ```

2. **Enrich with contacts & filter by title:**
   ```bash
   python build_job_list.py \
     --input "jobs/raw_jobs.csv" \
     --output "jobs/enriched_jobs.csv"
   ```

3. **Generate drafts for all contacts:**
   ```bash
   python batch_apply.py \
     --input "jobs/enriched_jobs.csv" \
     --output_dir "drafts/"
   ```

4. **Lookup Greenhouse tokens for companies:**
   ```bash
   python -m src.get_greenhouse_tokens \
     --spreadsheet_id "YOUR_SHEET_ID" \
     --sheet_name "companies" \
     --limit 100
   ```

**Pipeline Flow:**

Google Sheets (raw jobs) → Export CSV → Filter by title → Enrich with Hunter contacts → Generate personalized emails → Create Gmail drafts → Lookup Greenhouse tokens

---

### What Each Script Does

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `main.py` | Job URL + JD | Gmail draft | Single email (manual) |
| `export_sheet_to_csv.py` | Google Sheets tab | CSV file | Download jobs centrally |
| `build_job_list.py` | CSV jobs | Enriched CSV | Filter by title + add contacts |
| `batch_apply.py` | Enriched CSV | Gmail drafts | Generate & create all drafts |
| `get_greenhouse_tokens.py` | Companies tab | Updated Sheets | Lookup Greenhouse boards |

---

## 🤖 n8n Automation: Populate Raw Jobs from Greenhouse

**Problem:** Manually finding job URLs from each company's Greenhouse board is tedious. Solution: Automate it with n8n!

### The n8n Workflow

This workflow **bridges** your companies data with job postings:

**Trigger:** On-demand or scheduled (e.g., daily)

**Steps:**

1. **Read Companies Tab** from Google Sheets
   - Fetches all companies from the `companies` sheet (with `greenhouse_board_token` column)

2. **For Each Company:**
   - Construct the Greenhouse board URL: `https://boards.greenhouse.io/{token}/jobs`
   - Scrape the job listings page (using HTTP request + HTML parser)
   - Extract job URLs and titles

3. **Write to raw_jobs Sheet**
   - Add new rows to the `raw_jobs` tab with:
     - `company_name`
     - `job_title`
     - `job_url`
     - `date_found`

4. **Deduplicate** 
   - Skip URLs already in the sheet (avoid duplicate entries)

### Workflow Flow

```
Companies Tab (with tokens)
    ↓
n8n Trigger (Schedule/Manual)
    ↓
For each company → Fetch Greenhouse board
    ↓
Parse & extract job listings
    ↓
Format & write to raw_jobs tab
    ↓
✅ raw_jobs populated with fresh job URLs
```

### After n8n Populates raw_jobs

Your Python pipeline automatically takes over:

```
raw_jobs (populated by n8n)
    ↓
export_sheet_to_csv.py (download to CSV)
    ↓
build_job_list.py (filter by title + enrich contacts)
    ↓
batch_apply.py (generate personalized emails)
    ↓
Gmail Drafts created! 📬
```

### n8n Template Setup

**Required Nodes:**

1. **Google Sheets Trigger/Read** - Read companies from `companies` tab
2. **Loop** - For each company
3. **HTTP Request** - Fetch Greenhouse board page
4. **HTML Parser** - Extract job URLs (CSS selector: `a[href*="/jobs/"]`)
5. **Google Sheets Append** - Write new jobs to `raw_jobs` tab
6. **Deduplication Logic** - Check if URL exists before writing

> **Note:** This workflow assumes your `companies` tab has the `greenhouse_board_token` column populated (from `get_greenhouse_tokens.py`)

---

## ✨ Pro Tips

* Add more style samples to `src/style_samples` and your tone gets smarter
* Add more `jobs/<file>.txt` to reuse
* Copy your repo and share with a friend; they can plug their resume + style files

---

## 🔐 Security

This repo intentionally **ignores**:

* `.env`
* `credentials.json`
* `token.json`
* Anything in `/docs/`
* Compiled Python junk (`__pycache__/`)

Your secrets always stay local.

---

## 🧭 Roadmap (Choose what we build next!)

* ✅ Batch email generation + Gmail draft creation
* ✅ Hunter.io contact enrichment
* ✅ Google Sheets job management
* ✅ Greenhouse token auto-discovery
* 🔎 Auto-scrape job board links
* 📊 Track application status in Sheets
* 🔁 Follow-up email sequencer
* 🌐 LinkedIn DM automation
* 🎨 Streamlit/Web UI

If you want any of these, DM your future self:
**“Let’s build X next!”**

---

## 💛 Credits

Designed by **Sanyuja Desai**, who decided she deserved
a smarter & kinder job search experience 😊

Built with:

* Python
* OpenRouter
* Gmail API
* A touch of rebellion 💫


