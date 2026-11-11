#!/usr/bin/env python3
"""Build docs/index.html: the tracker template with built-in demo data (dates relative to today).
Run from the repo root: python3 scripts/build_demo.py"""
import json, datetime as d, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
tpl = (root / "assets" / "tracker-page.html").read_text()

def apps():
    A = lambda i, ago, co, role, src, st, **kw: dict(id=i, date=f"@{ago}", company=co, role=role, source=src, status=st, portal=kw.pop("portal", None), thread=None, email_ref="Demo email", note=kw.pop("note", None), added=f"@{kw.pop('added', ago)}", **kw)
    return [
        A("a1", 1, "Northwind Labs", "Senior Engineer", "LinkedIn Easy Apply", "interview", portal="https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED", history=[dict(date="@0", **{"from": "applied", "to": "interview"})]),
        A("a2", 2, "Acme Cloud", "Product Engineer", "company site", "action", action=dict(type="assessment", label="Complete the coding assessment", detected="@2", due="@-2", done=False)),
        A("a3", 4, "Brightpath", "Staff Engineer", "Indeed", "applied", portal="https://myjobs.indeed.com/applied"),
        A("a4", 9, "Orbit Systems", "Tech Lead", "company site", "rejected", note="Moved forward with candidates with more people-management experience", history=[dict(date="@3", **{"from": "applied", "to": "rejected"})]),
        A("a5", 14, "Quanta Retail", "Engineering Manager", "Naukri", "rejected", note="Position filled internally", history=[dict(date="@6", **{"from": "applied", "to": "rejected"})]),
        A("a6", 20, "Helio Health", "Principal Engineer", "Referral", "referral", note="Referral from a former colleague; still to apply", action=dict(type="referral_apply", label="Apply through the referral link", detected="@5", due="@3", done=False)),
        A("a7", 35, "Lumen Pay", "Software Architect", "company site", "applied"),
        A("a8", 80, "Vertex AI Co", "Engineering Lead", "LinkedIn Easy Apply", "rejected", note="Role closed", history=[dict(date="@60", **{"from": "applied", "to": "rejected"})]),
    ]

data = dict(config={}, owner_name="Demo", timezone="UTC", updated="@0", window_start="@60", not_found=[], apps=apps())
js = (
    "(function(){const D=" + json.dumps(data) + ";"
    "const sh=s=>{const n=+s.slice(1);const t=new Date();t.setDate(t.getDate()-n);return t.toISOString().slice(0,10)};"
    "const fix=o=>{if(typeof o==='string'&&/^@-?\\d+$/.test(o))return sh(o);if(Array.isArray(o))return o.map(fix);"
    "if(o&&typeof o==='object'){const r={};for(const k in o)r[k]=fix(o[k]);return r}return o};"
    "return Promise.resolve(fix(D));})()"
)
old = 'fetch("data.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error(r.status);return r.json()}).then(d=>{'
assert old in tpl, "template fetch line changed"
page = tpl.replace(old, js + ".then(d=>{")
page = page.replace("<h1>Application Portals</h1>", "<h1>Application Portals <small style=\"font-size:14px;font-weight:500;color:var(--warn)\">(demo with sample data)</small></h1>", 1)
out = root / "docs"; out.mkdir(exist_ok=True)
(out / "index.html").write_text(page)
print("wrote", out / "index.html")
