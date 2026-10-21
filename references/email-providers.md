# Connecting a mailbox

The tracker needs read access to the user's email. Start from the address they give you, work out the provider, then pick the best connection method available in this agent.

## 1. Detect the provider

Run `scripts/detect_provider.py <email>`. It checks the domain and its MX records and prints JSON: `{provider, imap_host, imap_port, app_password_url, notes}`.

| Signal | Provider |
|---|---|
| `@gmail.com`, `@googlemail.com`, or MX `*.google.com` / `*.googlemail.com` (Google Workspace) | Google |
| `@outlook.com`, `@hotmail.*`, `@live.*`, `@msn.com`, or MX `*.mail.protection.outlook.com` (Microsoft 365) | Microsoft |
| `@yahoo.*`, `@ymail.com`, `@rocketmail.com`, or MX `*.yahoodns.net` | Yahoo |
| `@aol.com`, or MX `*.aol.com` | AOL (Yahoo infrastructure) |
| `@icloud.com`, `@me.com`, `@mac.com`, or MX `*.icloud.com` | iCloud |
| `@zoho.*`, or MX `*.zoho.*` | Zoho |
| `@fastmail.*`, or MX `*.messagingengine.com` | Fastmail |
| `@proton.me`, `@protonmail.*`, or MX `*.protonmail.ch` | Proton (IMAP only through Proton Mail Bridge) |
| `@rediffmail.com` | Rediffmail |
| anything else | Generic IMAP (ask the user for the host, or try `imap.<domain>`) |

Custom domains (e.g. `name@company.com`) are usually hosted by Google or Microsoft. The MX records tell you which.

## 2. Pick a connection method (first one that works)

**A. A native mail connector in this agent (best).**
- Google: a Gmail connector (`mcp__Gmail__*` or similar).
- Microsoft: an Outlook / Microsoft 365 connector (Graph mail tools).
- Look at the agent's loaded and deferred tools first. If none is found, search the connector registry (in Claude: `SearchMcpRegistry` with e.g. ["outlook","email","mail"]) and offer it with `SuggestConnectors`. The user connects it through the OAuth sign-in on the card, and no password is shared.
- A connector must belong to the provider the user named. Don't offer Gmail to an Outlook user.

**B. An integration hub connector** (Zapier, Make, etc.) that has the user's provider as an app, e.g. Zapier → Yahoo Mail / IMAP "Find Email". Use its read/search action, after the user connects their account inside the hub.

**C. IMAP with an app password** (works for almost every provider: Yahoo, AOL, iCloud, Zoho, Fastmail, Rediff, Proton via Bridge, self-hosted). Walk the user through it:
1. Turn on 2-step verification for the account (most providers require it before app passwords).
2. Create an app password for "Mail" / "Claude job tracker":
   - Yahoo: Account Info › Account security › Generate app password (https://login.yahoo.com/account/security)
   - AOL: Account security › Generate app password (https://login.aol.com/account/security)
   - iCloud: appleid.apple.com › Sign-In and Security › App-Specific Passwords
   - Zoho: accounts.zoho.com › Security › App Passwords (and enable IMAP in Zoho Mail settings)
   - Fastmail: Settings › Privacy & Security › App passwords (IMAP access)
   - Google (if no connector): myaccount.google.com/apppasswords (needs 2-Step Verification)
   - Microsoft personal accounts: account.microsoft.com/security › Advanced security › App passwords. Microsoft 365 work accounts often block IMAP and app passwords; use method A.
   - Proton: install Proton Mail Bridge and use its local IMAP host, port and password.
3. Store the password as an **environment secret** in the agent (e.g. `MAIL_APP_PASSWORD`), with `MAIL_USER` and `MAIL_IMAP_HOST`. Never write it into data.json, the tracker page, notes, memory or chat logs. If the user pastes it into chat, use it for the session only and recommend they move it to a secret.
4. Test with `scripts/imap_search.py --test`.
5. Network note: some sandboxes block outbound IMAP (port 993). If the test can't connect, use method A, B or D.

**D. Forwarding fallback.** If nothing above works, the user sets up an auto-forward filter in their mailbox (subjects/senders like "application", "thank you for applying", known ATS domains) to an address the agent can read, e.g. a Gmail they've connected. Give the exact filter rules for their provider.

Record the result in `config.mail = {address, provider, method: "connector:gmail" | "connector:outlook" | "zapier" | "imap" | "forward", imap_host?}`, then reuse it on every run. If a run can't connect (expired sign-in, revoked app password), notify the user with the fix for their method.

## 3. Searching on each method

Write the searches once as intent, then translate them for the method:

| Intent | Gmail connector | Microsoft Graph / Outlook | IMAP (`imap_search.py`) |
|---|---|---|---|
| since date | `newer_than:Nd` or `after:YYYY/MM/DD` | `received>=YYYY-MM-DD` | `--since YYYY-MM-DD` |
| subject phrase | `subject:("x")` | `subject:"x"` | `--subject "x"` |
| sender domain | `from:(a.com OR b.com)` | `from:a.com OR from:b.com` | `--from a.com --from b.com` |
| body phrase | `"thank you for applying"` | `"thank you for applying"` | `--text "thank you for applying"` |

IMAP has no OR across fields, so run one search per phrase or sender and merge the results by Message-ID.

## 4. Email links in the tracker

- Gmail: `https://mail.google.com/mail/u/0/#all/<threadId>`
- Outlook/Microsoft 365: the message's `webLink` from Graph
- Yahoo, iCloud and IMAP generally have no stable web deep link. Instead, show "Email: <sender> · <subject> · <date>" so the user can search their inbox. Keep the Message-ID in data.json (`thread` field) for de-duplication; don't publish it as a link.
