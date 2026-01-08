
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

---

## 🛠️ Installation

### 1. Clone & Set Up Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# or: source .venv/bin/activate  (on macOS/Linux)
```

### 2. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Optional:** Install dev tools (formatting, linting, tests):
```bash
pip install -r requirements-dev.txt
```

---

## 🔐 Setup

### 1️⃣ Create `.env` (not committed to git)

```
OPENROUTER_API_KEY=sk-or-xxxxx
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
 ├── main.py                     # CLI entrypoint
 ├── requirements.txt            # dependencies
 ├── jobs/                       # stored job descriptions
 ├── src/
 │   ├── email_generator.py      # AI email writer
 │   ├── gmail_client.py         # authentication + Gmail service setup
 │   ├── gmail_draft.py          # create a Gmail draft w/ attachment
 │   ├── profile.py              # your resume text for context
 │   ├── style_profile.py        # style profile loader
 │   ├── style_samples/          # previous emails to learn tone
 │   ├── links.py                # LinkedIn, GitHub, portfolio URLs
 └── docs/
     └── Sanyuja_Desai_Resume.pdf
```

---

## 🚀 Usage

Basic example:

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

**What happens:**

* Model analyzes your resume + JD
* Writes a tailored email (no greeting, no signature — the bot adds those)
* Creates a Gmail draft with:
  ✔ Greeting
  ✔ Personalized content
  ✔ Signature
  ✔ Resume attached

You approve & send manually 🎯

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

## 🔧 Troubleshooting

### `OPENROUTER_API_KEY is not set in .env`
- Create `.env` in repo root with `OPENROUTER_API_KEY=sk-or-xxxxx`
- Reload terminal or restart your editor after adding `.env`

### Gmail auth fails (invalid credentials)
- Delete `token.json` and re-run the script
- It will open a browser to re-authenticate
- Make sure `credentials.json` exists and is valid

### `ModuleNotFoundError: No module named 'src'`
- Ensure you're running from repo root: `C:\Users\sanyuja\ML projects\job-outreach-bot\`
- Verify `.venv` is activated

### Email generation returns error
- Check `OPENROUTER_API_KEY` is valid and has quota
- Confirm `job_description` file exists if using `--jd_file`
- Try with a simpler job description (model may timeout on very long JDs)

### Resume file not found
- Ensure `docs/Sanyuja_Desai_Resume.pdf` exists (or pass correct `--resume_path`)
- Check file path is relative to repo root

---

## 🧭 Roadmap (Choose what we build next!)

* 🔎 Auto-scrape job boards (Lever, Greenhouse, Workday)
* 🕵️ Recruiter email finder
* 📊 Log applications to Google Sheets
* 🔁 Follow-up email sequencer
* 🌐 LinkedIn DM automation
* 🎨 Streamlit/Web UI
* 🗃 Batch-apply with filters

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


