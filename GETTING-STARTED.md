# Getting started

1. **Install the skill.** Claude app: Settings > Skills > Upload skill, pick `job-application-tracker.skill`. Claude Code: copy this folder to `~/.claude/skills/job-application-tracker/`.
2. **Set up.** Tell Claude: "Set up my job application tracker". Give the email address you use for applications.
3. **Connect your mailbox.** Claude detects your provider and picks a method: a native connector (sign in via OAuth), Zapier, or IMAP with an app password. Never paste your real password into chat.
4. **Review the tracker.** Claude scans recent mail and builds a single list with status, dates and candidate-portal links.
5. **Stay updated.** Say "Check my applications" any time, or "Run the tracker daily at 9 am" for a scheduled check that only notifies you on changes or due actions.

Privacy: the skill reads only your own mail and bundles no data. Your tracker (`data.json`) stays with you; don't share the tracker page unless you're fine exposing company names and dates.
