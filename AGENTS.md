# Job Application Tracker

This repo is an agent skill that tracks job applications from the user's email.

When the user asks to set up, refresh or check their job applications, or to schedule a daily check:

1. Read `SKILL.md` in this folder and follow it. It defines the Setup, Refresh and Daily check modes.
2. Use `scripts/` and `references/` as `SKILL.md` directs. Run scripts with `python3`.

Environment notes (this skill was written for Claude, so adapt where needed):
- Mailbox access: if you have no native Gmail/Outlook connector, use IMAP (`scripts/imap_search.py`) with an app password stored in env vars `MAIL_IMAP_HOST`, `MAIL_USER`, `MAIL_APP_PASSWORD`. Never write the password to a file, `data.json` or a reply.
- Tracker storage: there is no Artifact tool outside Claude. Use the local-folder option in `SKILL.md`: keep `job-tracker/data.json` and render `assets/tracker-page.html` to `job-tracker/index.html`.
- Scheduling: use whatever scheduler your environment offers, or tell the user to run the daily check manually or via cron.
