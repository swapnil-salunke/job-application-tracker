#!/usr/bin/env python3
"""Read-only IMAP search for the job application tracker.

Credentials come from environment variables only:
  MAIL_IMAP_HOST, MAIL_USER, MAIL_APP_PASSWORD, optional MAIL_IMAP_PORT (default 993)

Examples:
  python3 imap_search.py --test
  python3 imap_search.py --since 2026-08-21 --text "thank you for applying"
  python3 imap_search.py --since 2026-08-21 --from myworkday.com --from greenhouse-mail.io --body
Each criterion flag is searched separately (IMAP has no cross-field OR) and results are
merged by Message-ID. Prints a JSON list: message_id, date, from, subject, snippet,
links (http/https only) and body (with --body). Mailbox is opened read-only, so nothing is
marked read, moved or deleted.
"""
import argparse, email, imaplib, json, os, re, sys
from datetime import datetime
from email.header import decode_header, make_header
from html import unescape

def connect():
    host, user, pwd = os.environ.get("MAIL_IMAP_HOST"), os.environ.get("MAIL_USER"), os.environ.get("MAIL_APP_PASSWORD")
    if not (host and user and pwd):
        sys.exit("Set MAIL_IMAP_HOST, MAIL_USER and MAIL_APP_PASSWORD as environment secrets.")
    m = imaplib.IMAP4_SSL(host, int(os.environ.get("MAIL_IMAP_PORT", "993")), timeout=30)
    m.login(user, pwd)
    return m

def dec(v):
    try:
        return str(make_header(decode_header(v or "")))
    except Exception:
        return v or ""

def body_of(msg):
    plain, html = "", ""
    for part in msg.walk() if msg.is_multipart() else [msg]:
        ctype = part.get_content_type()
        if part.get_filename():
            continue
        try:
            text = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
        except Exception:
            continue
        if ctype == "text/plain" and not plain:
            plain = text
        elif ctype == "text/html" and not html:
            html = text
    links = sorted(set(re.findall(r'href=["\'](https?://[^"\']+)', html)))
    if not plain and html:
        plain = unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", html)))
    return re.sub(r"\s+", " ", plain).strip(), links

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--folder", default="INBOX")
    ap.add_argument("--since", help="YYYY-MM-DD")
    ap.add_argument("--subject", action="append", default=[])
    ap.add_argument("--from", dest="sender", action="append", default=[])
    ap.add_argument("--text", action="append", default=[])
    ap.add_argument("--body", action="store_true", help="include full body text")
    ap.add_argument("--limit", type=int, default=300)
    a = ap.parse_args()
    m = connect()
    if a.test:
        typ, data = m.select(a.folder, readonly=True)
        print(json.dumps({"ok": typ == "OK", "folder": a.folder, "messages": int(data[0]) if typ == "OK" else None}))
        return
    m.select(a.folder, readonly=True)
    base = []
    if a.since:
        base += ["SINCE", datetime.strptime(a.since, "%Y-%m-%d").strftime("%d-%b-%Y")]
    queries = [["SUBJECT", f'"{s}"'] for s in a.subject] + [["FROM", f'"{s}"'] for s in a.sender] + \
              [["TEXT", f'"{s}"'] for s in a.text] or [[]]
    ids = []
    for q in queries:
        typ, data = m.search("UTF-8" if any(ord(c) > 127 for c in " ".join(q)) else None, *(base + q or ["ALL"]))
        if typ == "OK":
            ids += data[0].split()
    seen, out = set(), []
    for i in sorted(set(ids), key=int, reverse=True)[: a.limit]:
        typ, data = m.fetch(i, "(BODY.PEEK[])")
        if typ != "OK" or not data or not isinstance(data[0], tuple):
            continue
        msg = email.message_from_bytes(data[0][1])
        mid = msg.get("Message-ID", f"imap-{i.decode()}").strip()
        if mid in seen:
            continue
        seen.add(mid)
        text, links = body_of(msg)
        row = {"message_id": mid, "date": msg.get("Date"), "from": dec(msg.get("From")),
               "subject": dec(msg.get("Subject")), "snippet": text[:300], "links": links[:40]}
        if a.body:
            row["body"] = text[:20000]
        out.append(row)
    m.logout()
    print(json.dumps(out, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
