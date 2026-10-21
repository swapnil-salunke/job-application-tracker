# data.json schema

```json
{
  "config": {
    "owner_name": "Alex",
    "owner_email": "alex@example.com",
    "mail": {"address": "alex@yahoo.com", "provider": "yahoo", "method": "imap", "imap_host": "imap.mail.yahoo.com"},
    "timezone": "Europe/London",
    "window_days": 60,
    "tracker_url": "https://claude.ai/artifact/...",
    "notify": ["push"],
    "expected_companies": ["Apple"],
    "reminder_overrides": {"portal_task": 2},
    "follow_ups": false
  },
  "owner_name": "Alex",
  "timezone": "Europe/London",
  "updated": "2026-10-21",
  "last_checked": "2026-10-21T03:04:00Z",
  "window_start": "2026-08-22",
  "not_found": ["Apple"],
  "apps": [
    {
      "id": "a1",
      "date": "2026-10-16",
      "company": "Example Corp",
      "role": "Engineering Manager, Mobile · R12345",
      "source": "company site | LinkedIn Easy Apply | Naukri | Indeed | Talent500 | Referral | Recruiter",
      "status": "applied | action | referral | interview | offer | rejected | withdrawn",
      "portal": "https://example.wd5.myworkdayjobs.com/Careers/userHome",
      "portal_unverified": false,
      "thread": "1a14535b2f5787da  (Gmail thread ID, or the Message-ID on other providers)",
      "email_link": "optional deep link, e.g. an Outlook webLink",
      "email_ref": "optional text for providers without deep links, e.g. 'Workday · Thank you for applying · 16 Oct'",
      "note": null,
      "added": "2026-10-16  (the day the tracker first recorded it; new rows show a 'New' badge for 3 days)",
      "action": {
        "type": "portal_task",
        "label": "Upload ID documents in the candidate portal",
        "detected": "2026-10-16",
        "due": "2026-10-19",
        "last_reminded": null,
        "reminder_count": 0,
        "done": false
      },
      "history": [
        {"date": "2026-10-20", "from": "applied", "to": "interview", "source_thread": "1a15..."}
      ]
    }
  ]
}
```

Notes
- `owner_name`, `timezone` and `window_start` are mirrored at the top level because the page template reads them from there.
- `window_start` = today − `config.window_days`. Recompute it on every run.
- Dates are `YYYY-MM-DD` in the user's timezone. `last_checked` is in UTC.
- `id`s stay stable across runs. Never renumber them.
