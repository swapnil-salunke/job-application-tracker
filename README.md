# Job Application Tracker (Claude skill)

Tracks your job applications from your email inbox. It finds every application (career sites, LinkedIn Easy Apply, Naukri/Indeed, recruiters, referrals), works out each status, keeps a single tracker page with candidate-portal links, detects rejections, interview invites and offers, and reminds you about pending actions. It works with Gmail, Outlook, Yahoo, iCloud, Zoho and custom domains.

No data is bundled in this skill. It reads only your own mail.

**[Download the latest `.skill` file](https://github.com/swapnil-salunke/job-application-tracker/releases/latest/download/job-application-tracker.skill)** · [All releases](https://github.com/swapnil-salunke/job-application-tracker/releases)

## Step-by-step guide

### 1. Install the skill

**Claude app (easiest)**
1. [Download `job-application-tracker.skill`](https://github.com/swapnil-salunke/job-application-tracker/releases/latest/download/job-application-tracker.skill) (always the latest release).
2. Open Claude, go to **Settings > Skills**, and choose **Upload skill**.
3. Select the downloaded file and make sure the skill is switched on.

**Claude Code**
```bash
git clone https://github.com/swapnil-salunke/job-application-tracker.git ~/.claude/skills/job-application-tracker
```

### 2. Start setup
In a new chat, say:

> Set up my job application tracker

Claude asks for the email address you use for job applications.

### 3. Connect your mailbox
Claude detects your email provider and picks the first method that works:

1. **Native connector** (Gmail, Outlook/Microsoft 365). You sign in through the normal OAuth screen. No password is shared.
2. **Integration hub** such as Zapier, after you connect your account there.
3. **IMAP with an app password.** Claude walks you through creating one for your provider and storing it as environment secrets (`MAIL_IMAP_HOST`, `MAIL_USER`, `MAIL_APP_PASSWORD`). Never paste your real password into chat.
4. **Forwarding.** You auto-forward job-related mail to an inbox Claude can read.

Claude confirms the connection with one test search.

### 4. First scan
Claude scans the last 60 days of mail, then builds your tracker: one list with company, role, source, date applied, status, candidate-portal link and any action due.

### 5. Daily use
Ask any time:

- "Check my applications"
- "What are my overdue action items?"
- "Which applications have a candidate portal link?"

### 6. Automate it (optional)
Say "Run the tracker daily at 9 am". The daily check adds new applications, detects status changes and notifies you only when something is new, changed or due.

### 7. Share your tracker (optional)
The tracker contains company names and dates. Share it view-only, and only with people you trust.

## What's inside

| Path | Purpose |
|---|---|
| `SKILL.md` | Instructions Claude follows |
| `scripts/detect_provider.py` | Identifies your email provider |
| `scripts/imap_search.py` | Searches mail over IMAP |
| `references/` | Data schema and provider connection details |
| `assets/tracker-page.html` | Tracker page template |
| `GETTING-STARTED.md` | Short guide for non-technical users |

## License
MIT. See [LICENSE](LICENSE).
