#!/usr/bin/env python3
"""Detect an email address's provider and IMAP settings.

Usage: python3 detect_provider.py name@example.com
Prints JSON. Uses the address's domain, then its MX records (via `dig`, dnspython,
or DNS-over-HTTPS) for custom domains.
"""
import json, subprocess, sys, urllib.request

PROVIDERS = {
    "google":    {"imap_host": "imap.gmail.com", "app_password_url": "https://myaccount.google.com/apppasswords",
                  "notes": "Prefer the Gmail connector (OAuth). IMAP needs 2-Step Verification + app password."},
    "microsoft": {"imap_host": "outlook.office365.com", "app_password_url": "https://account.microsoft.com/security",
                  "notes": "Prefer an Outlook/Microsoft 365 connector. Work accounts often block IMAP."},
    "yahoo":     {"imap_host": "imap.mail.yahoo.com", "app_password_url": "https://login.yahoo.com/account/security",
                  "notes": "Use IMAP with an app password, or a hub connector (e.g. Zapier Yahoo Mail)."},
    "aol":       {"imap_host": "imap.aol.com", "app_password_url": "https://login.aol.com/account/security",
                  "notes": "IMAP with an app password."},
    "icloud":    {"imap_host": "imap.mail.me.com", "app_password_url": "https://appleid.apple.com",
                  "notes": "IMAP with an app-specific password (Sign-In and Security)."},
    "zoho":      {"imap_host": "imap.zoho.com", "app_password_url": "https://accounts.zoho.com",
                  "notes": "Enable IMAP in Zoho Mail settings; use an app password. EU/IN accounts: imap.zoho.eu / imap.zoho.in."},
    "fastmail":  {"imap_host": "imap.fastmail.com", "app_password_url": "https://app.fastmail.com/settings/security/apps",
                  "notes": "IMAP with an app password."},
    "proton":    {"imap_host": "127.0.0.1", "app_password_url": "https://proton.me/mail/bridge",
                  "notes": "Requires Proton Mail Bridge running locally; use the Bridge's host/port/password."},
    "rediff":    {"imap_host": "imap.rediffmail.com", "app_password_url": None,
                  "notes": "IMAP must be enabled in Rediffmail settings."},
}
DOMAINS = {
    "gmail.com": "google", "googlemail.com": "google",
    "outlook.com": "microsoft", "hotmail.com": "microsoft", "live.com": "microsoft", "msn.com": "microsoft",
    "yahoo.com": "yahoo", "ymail.com": "yahoo", "rocketmail.com": "yahoo", "yahoo.co.in": "yahoo", "yahoo.co.uk": "yahoo",
    "aol.com": "aol", "icloud.com": "icloud", "me.com": "icloud", "mac.com": "icloud",
    "zoho.com": "zoho", "zohomail.com": "zoho", "fastmail.com": "fastmail", "fastmail.fm": "fastmail",
    "proton.me": "proton", "protonmail.com": "proton", "pm.me": "proton", "rediffmail.com": "rediff",
}
MX_HINTS = [("google.com", "google"), ("googlemail.com", "google"), ("protection.outlook.com", "microsoft"),
            ("outlook.com", "microsoft"), ("yahoodns.net", "yahoo"), ("aol.com", "aol"), ("icloud.com", "icloud"),
            ("zoho", "zoho"), ("messagingengine.com", "fastmail"), ("protonmail.ch", "proton"), ("rediffmail", "rediff")]

def mx_records(domain):
    try:
        out = subprocess.run(["dig", "+short", "MX", domain], capture_output=True, text=True, timeout=8).stdout
        if out.strip():
            return [l.split()[-1].rstrip(".").lower() for l in out.splitlines() if l.strip()]
    except Exception:
        pass
    try:
        import dns.resolver  # type: ignore
        return [str(r.exchange).rstrip(".").lower() for r in dns.resolver.resolve(domain, "MX")]
    except Exception:
        pass
    for url in (f"https://dns.google/resolve?name={domain}&type=MX",
                f"https://cloudflare-dns.com/dns-query?name={domain}&type=MX"):
        try:
            req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.load(r)
            return [a["data"].split()[-1].rstrip(".").lower() for a in data.get("Answer", [])]
        except Exception:
            continue
    return None  # lookup impossible from this environment

def detect(email):
    domain = email.split("@")[-1].strip().lower()
    provider, mx = DOMAINS.get(domain), []
    if not provider:
        mx = mx_records(domain)
        provider = next((p for m in (mx or []) for hint, p in MX_HINTS if hint in m), None)
    info = dict(PROVIDERS.get(provider, {"imap_host": f"imap.{domain}", "app_password_url": None,
                "notes": "Unknown host: confirm the IMAP server with the user or their email admin."}))
    if mx is None:
        info["notes"] = ("MX lookup is blocked in this environment, so the host is unknown. Look up the domain's MX "
                         "records another way (web search 'MX lookup <domain>') or ask the user who hosts their email "
                         "(Google Workspace, Microsoft 365, Zoho, ...).")
    return {"email": email, "domain": domain, "provider": provider or "unknown-custom-domain" if mx is None else provider or "generic-imap", "mx": mx,
            "imap_port": 1143 if provider == "proton" else 993, **info}

if __name__ == "__main__":
    if len(sys.argv) != 2 or "@" not in sys.argv[1]:
        sys.exit("usage: detect_provider.py name@example.com")
    print(json.dumps(detect(sys.argv[1]), indent=2))
