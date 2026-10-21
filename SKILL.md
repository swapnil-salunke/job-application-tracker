---
name: job-application-tracker
description: Track a job seeker's applications from their email inbox. Finds every application (company career sites/ATS, LinkedIn Easy Apply, Naukri/Indeed/other boards, referrals, recruiters), works out each status, keeps a single-list tracker page with candidate-portal links, detects status changes (rejections, interview invites, assessments, offers) and reminds the user about pending actions before and after their deadlines. Use when the user asks to list, track, refresh or check job applications, statuses or candidate portals; to set up a daily application check; or when a scheduled run says to run the job application tracker.
---

# Job Application Tracker

Keeps one tracker of the user's job applications, built only from their email. It works in three modes:

| Mode | When | What it does |
|---|---|---|
| **Setup** | First run, or no tracker exists yet | Connects the mailbox, collects the config, does a full scan, builds the tracker, offers a daily schedule |
| **Refresh** | The user asks to update or check | Incremental scan, then updates the tracker and replies with a summary |
| **Daily check** | A scheduled run | Adds any new applications, detects status changes, checks reminders, updates the tracker, and notifies the user only if something is new, changed or due |

## 0. Connect the mailbox (any provider)

The skill works with any email account: Gmail, Google Workspace, Outlook/Microsoft 365, Yahoo, AOL, iCloud, Zoho, Fastmail, Proton, Rediff or any custom domain. Full details are in `references/email-providers.md`.

1. **Ask for the email address** used for job applications, unless `config.mail` already has it.
2. **Detect the provider:** run `python3 scripts/detect_provider.py <email>`. It checks the domain, then the MX records for custom domains. If DNS is blocked, look the MX up another way or ask the user who hosts their mail.
3. **Choose the connection method,** taking the first that works:
   - **A. Native connector** for that provider, e.g. a Gmail or Outlook/Microsoft 365 connector. Check the loaded and deferred tools first. If none is found, search the connector registry and offer the right connector so the user can sign in through OAuth. No password is shared.
   - **B. Integration hub** (e.g. Zapier, Make) that has the provider's mail app, after the user connects their account there.
   - **C. IMAP with an app password.** Give the user the step-by-step instructions for their provider (2-step verification, then generate an app password at the link the script printed). Have them store it as environment secrets `MAIL_IMAP_HOST`, `MAIL_USER` and `MAIL_APP_PASSWORD`, then test with `python3 scripts/imap_search.py --test`. Never put the password in data.json, the page, memory or a reply.
   - **D. Forwarding.** The user auto-forwards job-related mail to an inbox the agent can read. Give them filter rules for their provider.
4. **Explain the result in plain words:** which provider was detected, which method you're using, and what (if anything) the user must click or create. Then confirm with one test search.
5. **Save** `config.mail = {address, provider, method, imap_host?}` and reuse it on every run. If a later run can't connect (expired sign-in or revoked app password), notify the user with the specific fix.

## 1. Config and state

All state lives in one JSON file, `data.json` (schema in `references/data-schema.md`). Find it in this order:
1. Tracker page published as an Artifact (preferred): `data.json` is a published file of that artifact. Read it with the Artifact tool (`action: "read"`, `url`, `path: "data.json"`), and republish the page with `files: {"data.json": ...}` to the same `url`.
2. No Artifact tool: a local folder the user chose (e.g. `job-tracker/data.json` plus `index.html`). Deliver it as a file.
3. Nothing found: run **Setup**.

The `config` block in `data.json`:
- `owner_name`, `owner_email`: who is applying. Use only to identify their own mail.
- `timezone` (IANA, e.g. `Asia/Kolkata`): used for "today", deadlines and the schedule.
- `window_days` (default 60): how far back the main list goes. Older entries stay in a collapsed section.
- `tracker_url`: the Artifact URL, once published.
- `notify`: `push` and/or `email`. Daily checks notify the user only, never anyone else.
- `expected_companies` (optional): companies the user says they applied to. If no confirmation is found for one, list it under `not_found`.
- `reminder_overrides` (optional): per-action-type deadline changes the user asked for.

**Setup:** infer what you can (the mailbox owner's name and address from the connector, timezone from the environment). Ask only for what you can't infer, using one short question round. In an unattended run, use the defaults and state your assumptions in the notification.

## 2. Scan email

Search through the connection from step 0. The queries below are in Gmail syntax. Translate them for Outlook/Graph or IMAP using the table in `references/email-providers.md`. On IMAP, run one `imap_search.py` call per phrase or sender and merge the results by Message-ID. Full scan: `newer_than:<window_days>d`. Incremental scan: since `last_checked` minus one day of overlap. Page through all results.

1. **LinkedIn Easy Apply:** `subject:("your application was sent to")`. The company is in the subject.
2. **Confirmations:** `("thank you for applying" OR "thanks for applying" OR "application received" OR "received your application" OR "thank you for your application" OR "application submitted" OR "successfully applied")`
3. **ATS senders:** `from:(myworkday.com OR myworkdayjobs.com OR greenhouse.io OR greenhouse-mail.io OR lever.co OR smartrecruiters.com OR successfactors.com OR taleo.net OR icims.com OR ashbyhq.com OR workablemail.com OR oraclecloud.com OR avature.net OR teamtailor-mail.com OR bamboohr.com OR jobvite.com OR phenom.com)`
4. **Job boards:** `from:(naukri.com OR indeed.com OR talent500.co OR instahyre.com OR iimjobs.com OR hirist.tech OR wellfound.com OR cutshort.io OR glassdoor.com OR seek.com OR stepstone.de) (applied OR application)`. Include regional boards for the user's country.
5. **Status changes:** `("unfortunately" OR "not moving forward" OR "other candidates" OR "not been selected" OR "position has been filled" OR "interview" OR "schedule a call" OR "availability" OR "assessment" OR "coding challenge" OR "HackerRank" OR "Codility" OR "offer letter" OR "next steps")`
6. **Actions and referrals:** `("action required" OR "pending task" OR "complete your application" OR "verify your" OR "confirm your email" OR "referred" OR "draft")`

Skip job-alert digests, "jobs similar to…" and "recommended for you" emails, newsletters, marketing, and bare OTP or verification codes. None of these are applications.

For large batches, give parallel subagents about 15 thread IDs each and have them return JSON matching `references/data-schema.md` (one object per application).

## 3. Extract each application

From each confirmation email, read the full content (HTML, so the link targets are visible) and record:
- `company`, `role` (+ req ID), `date`, `source`, `thread` (the email thread ID)
- `status`: `applied` | `action` | `referral` | `interview` | `offer` | `rejected` | `withdrawn`
- `portal`: the candidate portal link (rules below), with `portal_unverified: true` when it was inferred
- `note`: anything the user needs to know (e.g. "Naukri named only 1 of 3 jobs applied that day")

**Merging:** apply later emails to the same application. Match on company + role or req ID, or on the thread. A rejection, interview invite or offer updates the status, and the change goes into `history`. Merge duplicates (e.g. an Indeed Apply and a company confirmation for the same role), and link postings that are the same job under two names (e.g. a staffing firm on LinkedIn vs. the end client).

**Portal link rules. The page is published, so these are mandatory:**
- Give a clean base URL only. Remove query strings, tokens, one-time login/activation/reset paths, application IDs/UUIDs and tracking parameters. Decode tracking redirects to their real destination before cleaning.
- Known patterns:
  - Workday: `https://TENANT.wdN.myworkdayjobs.com/SITE/userHome`
  - SmartRecruiters: `https://jobs.smartrecruiters.com/my-applications`
  - Amazon: `https://account.amazon.jobs/candidate/dashboard/applications`
  - Oracle Recruiting Cloud: `https://HOST/hcmUI/CandidateExperience/en/sites/SITE/my-profile`
  - Teamtailor: `https://COMPANY.teamtailor.com/connect/login`
  - LinkedIn Easy Apply: `https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED`
  - Indeed: `https://myjobs.indeed.com/applied`
  - Naukri: `https://www.naukri.com/myapply/historypage` (unverified)
  - Meta: `https://www.metacareers.com/profile/home/`
- Greenhouse, Ashby, BambooHR, Lever and most boards have no candidate portal. Set `portal: null`.
- Every row also points to its email:
  - Gmail: `https://mail.google.com/mail/u/0/#all/<threadId>`
  - Outlook: the message's Graph `webLink`
  - Providers without stable deep links (Yahoo, iCloud, IMAP): show "sender · subject · date" text instead of a link
  - Store the thread or Message-ID in `thread` for de-duplication.

## 4. Action items and reminders

When an email asks the user to do something, set `status: "action"` and attach:
`action: {type, label, detected, due, last_reminded, done: false}`

Default deadlines (apply any `reminder_overrides` on top):

| `type` | Triggered by | Due |
|---|---|---|
| `verify_email` | Confirm email or profile so the application is visible | detected + 1 day |
| `complete_application` | Draft or partial application, screening questions not answered | detected + 2 days, or before the stated expiry |
| `portal_task` | Documents, IDs, forms, consent to complete in the portal | detected + 3 days |
| `schedule_interview` | Asked for availability or to book a slot | detected + 1 day |
| `assessment` | Coding test, take-home, questionnaire | the stated deadline, else detected + 3 days |
| `referral_apply` | Referral invite, or a referral email that still shows "Apply" | detected + 3 days |
| `recruiter_reply` | Recruiter asked for details, CTC, notice period or a call | detected + 2 days |
| `offer_response` | Offer received | the stated deadline, else detected + 5 days |
| `follow_up` (optional) | Applied 21+ days ago to a high-priority role, no response | applied + 21 days. Use only if the user turned follow-ups on |

**Marking an action done:** clear it (`done: true`, status moves on) when evidence appears. Examples: the user's sent reply in the thread, a completed-application email, an interview confirmation, an assessment-submitted email, or the user saying it's done. Never guess it's done.

**When to remind** (compare in the user's timezone, at most once per action per day):
- due tomorrow or today, and not reminded today: send a "due soon" reminder
- overdue: remind on the first overdue day, then every 2 days, up to 5 reminders. After that, list it under "Still pending" in the summary only.
- Expired (e.g. a 30-day draft window passed): set `status: "rejected"` and `note: "expired"`, and stop reminding.
- Record `last_reminded` and increment `reminder_count` whenever a reminder is sent.

## 5. Daily check: new applications, then status changes

Every daily run does two passes over the mail since `last_checked` (with one day of overlap), in this order.

**Pass 1: find new applications and add them.**
1. Run the application-discovery searches from section 2 (queries 1–4, plus referral, recruiter and draft emails from query 6).
2. For each confirmation, build an application record (section 3) and check it against `apps`:
   - **Duplicate:** the same `thread`/Message-ID, the same company + req ID, or the same company + normalised role within 14 days. Merge it and keep the earliest date. Same-job aliases (a staffing firm's posting vs. the end client, or Indeed Apply vs. the company ATS) also merge, with a note.
   - **Re-application:** the same company and role but more than 30 days after a closed one. Add it as a new row with note "re-applied", and keep the old row.
   - **Otherwise:** a new row with a new stable `id`, `status: "applied"` (or `action`/`referral` if the email asks for something), `added: <today>`, and `history: [{date, from: null, to: <status>}]`.
3. Digest-style sources need extra care:
   - Naukri's "You applied for N jobs" names only one job, so add one row per named job and note how many are unnamed.
   - LinkedIn's "application was sent to <Company>" has no role. Read the email body for the job title. If it isn't there, set `role: null` and note "role not in email".
4. If an email suggests the application isn't finished (OTP to continue, "complete your application", "draft saved"), add or flag it as `action: complete_application`. Don't count it as applied until a completion email arrives.

**Pass 2: detect status changes** on all open applications, including the ones just added. Compare the new statuses against the stored ones. Report:
- 🟢 interview invites, assessments, offers (most important; put these first)
- 🟡 new action items, and due or overdue reminders
- 🔴 rejections and closures
- ➕ new applications added since the last check, with company · role · source

Add each change to the application's `history` (`[{date, from, to, source_thread}]`), then set `last_checked`.

## 6. Build or update the tracker page

Use the template `assets/tracker-page.html`. It loads `data.json` at runtime, so normally only `data.json` changes:
- One combined list, newest first, for the window. Older entries go in a collapsed section. Do not split the list by source.
- A "Needs your action" box at the top, sorted by due date, with overdue items in red.
- Search box and filters: All / In review / Needs action / Closed.
- Each row: date · company (+ source) · role (+ note, + due line) · status pill · portal link + email link.

If you build the page from the Artifact tool, load its page-design guidance first. Publish the HTML with `files: {"data.json": <path>}`, update `config.tracker_url`, and keep the same URL afterwards.

**Verify before every publish.** Serve the page and `data.json` locally and render it headlessly (Playwright or similar). Check that the rows appear and there are no script errors. Define every constant before the code that uses it; a temporal-dead-zone error once left the page blank. Fix any problem before publishing.

## 7. Replies and notifications

- **Interactive:** 3 to 6 short lines covering counts, actions due or overdue, new interviews/offers/rejections and new applications. Don't paste the tracker URL; the app shows a card.
- **Daily check:** notify only when there is a status change, a new application, a new action, or a reminder due today. New applications get one line each ("Added: Visa – Sr Manager SWE (company site)"), or a count if there are more than 5. Lead with the most important item, e.g. "Interview request from Docusign; reply by tomorrow. 2 actions overdue: …". Stay silent when nothing changed.
- If the mail connector is missing or signed out, notify the user that the check couldn't run and which connection to reconnect.

## 8. Daily schedule (setup)

When the user wants daily checks, create a scheduled task with the platform's scheduler (in Claude: the scheduled-task tool `create_trigger`; never in-session cron):
- Time: daily, before the user's requested hour, in their timezone (e.g. `CRON_TZ=Asia/Kolkata 34 8 * * *` for "by 9 am"). Use a minute just before the hour rather than exactly on it.
- The task must have access to the same mail connection: the connector attached to the task, or the IMAP secrets present in its environment.
- The prompt must stand alone: "Run the job application tracker skill in daily-check mode. Tracker: <url>. Owner: <name> <email>. Mail: <provider> via <method>. Timezone: <tz>. If the skill isn't available, follow these steps: <short summary of sections 2–7>. Notify only if something changed or an action is due."
- Tell the user the time it runs, and whether its runs need approval.

## Never
- Apply to jobs, click confirmation/verification links, submit forms, or reply on the user's behalf.
- Send, label, archive or delete emails, or notify anyone other than the user.
- Publish URLs that contain tokens, application IDs, email addresses or one-time codes, or show OTPs anywhere.
- Mark an action done without evidence.
