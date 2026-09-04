#!/usr/bin/env python3
"""Render docs/index.html - a self-contained static site for GitHub Pages.

Everything shown is read out of data/plumbers.json, which scripts/build_data.py
merges from official CSLB captures plus the curated analysis layer, and which
scripts/validate.py has already proven traces back to those captures.

No external assets, no CDN, no build step beyond the standard library. Content
is server-rendered so the page is fully readable with JavaScript disabled; the
script tag only adds filtering, sorting and search.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
from urllib.parse import urlparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

TIER_META = {
    "recommended": ("First-screen lead", "Call these first to screen. Active license plus direct adjacent-job evidence; exact overflow skill is still unverified."),
    "viable": ("Verified & viable", "Active license verified. Relevant capability is advertised or adjacent, but no exact-job evidence was captured."),
    "conditional": ("Partial fit", "Active license verified, but only suitable for part of this job."),
    "fallback-only": ("Fallback only", "Only relevant if concealed piping must actually be replaced."),
    "wrong-scale": ("Wrong scale", "Clean license, but not a residential service-call business."),
    "unverified": ("Not verified", "No CSLB license could be confirmed. Do not hire on this evidence."),
    "do-not-hire": ("Do not hire", "CSLB license revoked, suspended, inactive, expired or canceled at the verification date."),
    "historical": ("Historical entity", "Superseded or canceled license, kept so permit history can be traced."),
}

STATUS_META = {
    "active": ("ACTIVE", "ok"),
    "suspended": ("SUSPENDED", "bad"),
    "expired": ("EXPIRED", "bad"),
    "canceled": ("CANCELED", "bad"),
    "revoked": ("REVOKED", "bad"),
    "inactive": ("INACTIVE", "bad"),
    "unknown": ("UNKNOWN", "warn"),
    "unverified": ("NOT VERIFIED", "warn"),
}

# CSLB address-of-record zip in the tenant's own neighbourhood (Outer Sunset / Parkside).
OUTER_SUNSET_RE = re.compile(r"\b(94122|94116)(?:-\d{4})?\s*$")

SEV_META = {
    "critical": ("CRITICAL", "bad"),
    "warn": ("CAUTION", "warn"),
    "info": ("NOTE", "info"),
}

FIT_LABELS_ORDER = [
    "snake_shower", "tub_overflow_access", "non_destructive",
    "prewar_galvanized", "camera_inspection", "weekend_emergency",
]

FIT_CELL = {
    "documented": ("Documented", "ok"),
    "documented-adjacent": ("Documented (adjacent)", "ok"),
    "advertised": ("Advertised", "mid"),
    "unknown": ("Unknown", "dim"),
    "no-evidence": ("No evidence", "warn"),
    "no": ("Out of scope", "bad"),
}


def e(text) -> str:
    return html.escape(str(text), quote=True) if text is not None else ""


def badge(text: str, kind: str, title: str = "") -> str:
    t = f' title="{e(title)}"' if title else ""
    return f'<span class="badge b-{kind}"{t}>{e(text)}</span>'


def access_badge(access: str | None) -> str:
    if not access:
        return ""
    if access == "direct":
        return badge("direct capture", "ok", "Fetched straight from the source URL; see the raw capture for its date.")
    if access == "blocked":
        return badge("blocked", "bad", "Could not be fetched from this environment.")
    if access == "manual-review":
        return badge("manual review link", "info", "Provided so you can inspect the live source; no data was extracted from this link.")
    return badge(access.replace("indirect-", "") + " only", "warn",
                 "The underlying platform was not fetched directly. The datum came from a search snippet "
                 "or a directly fetched aggregator and should be manually reviewed.")


def link(url: str, label: str, cls: str = "") -> str:
    if not url:
        return e(label)
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{e(url)}" rel="noopener noreferrer" target="_blank">{e(label)}</a>'


def status_badge(code: str) -> str:
    label, kind = STATUS_META.get(code, (code.upper(), "warn"))
    return badge(label, kind)


def render_license(lic: dict) -> str:
    if not lic.get("number"):
        note = lic.get("note") or lic.get("status_raw") or ""
        return (f'<div class="lic lic-none">{status_badge(lic.get("status_code", "unverified"))}'
                f'<p class="lic-note">{e(note)}</p></div>')
    bond = lic.get("bond") or {}
    rows = [
        ("License number", lic["number"]),
        ("Legal name on license", lic.get("legal_name")),
        ("CSLB status", None),
        ("Entity type", lic.get("entity")),
        ("Classifications", lic.get("classifications")),
        ("Issued", lic.get("issue_date")),
        ("Expires", lic.get("expire_date")),
        ("Contractor's bond", None),
        ("Workers' compensation", None),
        ("CSLB address of record", lic.get("cslb_address")),
        ("CSLB phone of record", lic.get("cslb_phone")),
    ]
    if lic.get("misc"):
        rows.append(("CSLB misc. information", lic["misc"]))
    out = ['<table class="kv">']
    for label, val in rows:
        if label == "CSLB status":
            cell = f'{status_badge(lic["status_code"])} <span class="muted">{e(lic.get("status_raw"))}</span>'
        elif label == "Contractor's bond":
            if bond.get("carrier"):
                parts = [bond["carrier"], bond.get("amount"), f"effective {bond.get('effective')}"]
                cell = e(" / ".join(str(x) for x in parts if x))
                if bond.get("cancellation"):
                    cell += f' <span class="b-bad badge">bond canceled {e(bond["cancellation"])}</span>'
            else:
                cell = '<span class="muted">none on file</span>'
        elif label == "Workers' compensation":
            code = lic.get("workers_comp_code")
            if code == "exempt":
                cell = badge("EXEMPT", "warn", "CSLB records certify no employees.") + \
                       f' <span class="muted">{e(lic.get("workers_comp_raw"))}</span>'
            else:
                cell = badge("insured", "ok") + f' <span class="muted">{e(lic.get("workers_comp_raw"))}</span>'
        else:
            cell = e(val) if val else '<span class="muted">-</span>'
        out.append(f"<tr><th>{e(label)}</th><td>{cell}</td></tr>")
    out.append("</table>")
    cap = ""
    if lic.get("source_url"):
        cap = (f'<p class="prov">{link(lic["source_url"], "Open the official CSLB record", "btn")}'
               f'<span class="muted">captured {e(lic.get("captured_at"))} &middot; '
               f'verbatim copy: <code>{e(lic.get("raw_file"))}</code></span></p>')
    return '<div class="lic">' + "".join(out) + cap + "</div>"


def render_ratings(ratings: list) -> str:
    if not ratings:
        return ('<p class="empty">No public review aggregate could be captured for this business '
                'during this research pass. Its standing here rests on the official CSLB record and '
                'SF permit history only &mdash; screen it by phone.</p>')
    out = ['<ul class="ratings">']
    for r in ratings:
        score = r.get("score")
        count = r.get("count")
        bits = []
        if score:
            bits.append(f'<strong>{e(score)}</strong>')
        if count:
            bits.append(f'{e(count)} reviews')
        label = " &middot; ".join(bits) if bits else "listed"
        note = f' <span class="muted">{e(r["note"])}</span>' if r.get("note") else ""
        out.append(
            f'<li><span class="plat">{e(r.get("platform"))}</span> {label} '
            f'{access_badge(r.get("access"))} {link(r.get("url"), "source", "src")}{note}</li>')
    out.append("</ul>")
    return "".join(out)


def render_evidence(evs: list) -> str:
    if not evs:
        return ""
    out = ['<h4>Captured source evidence</h4><div class="quotes">']
    for ev in evs:
        author = f' &mdash; {e(ev["author"])}' if ev.get("author") else ""
        signals = "".join(f'<span class="chip">{e(s)}</span>' for s in ev.get("job_signals", []))
        out.append(
            f'<blockquote><p>&ldquo;{e(ev["text"])}&rdquo;</p>'
            f'<footer><span class="plat">{e(ev.get("platform"))}</span>{author} '
            f'{access_badge(ev.get("access"))} {link(ev.get("url"), "read at source", "src")}'
            f'<div class="signals">{signals}</div></footer></blockquote>')
    out.append("</div>")
    return "".join(out)


def render_flags(flags: list) -> str:
    if not flags:
        return ""
    out = ['<h4>Flags &amp; irregularities</h4><ul class="flags">']
    for f in flags:
        label, kind = SEV_META.get(f["severity"], (f["severity"].upper(), "info"))
        out.append(f'<li class="f-{kind}">{badge(label, kind)} '
                   f'<strong>{e(f["label"])}</strong><p>{e(f["detail"])}</p></li>')
    out.append("</ul>")
    return "".join(out)


def render_sources(sources: list) -> str:
    out = ['<h4>Source and manual-review links</h4><ul class="sources">']
    for s in sources:
        out.append(
            f'<li><span class="tier t-{e(s.get("tier"))}">{e(s.get("tier"))}</span> '
            f'{link(s.get("url"), s.get("label"))} {access_badge(s.get("access"))}'
            + (f' <code>{e(s["raw"])}</code>' if s.get("raw") else "") + "</li>")
    out.append("</ul>")
    return "".join(out)


def batch_label(code: str) -> str:
    """'2026-09-04-expansion-50-b6' -> '2026-09-04 · 50-entry pass (b6)'."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})-expansion-(\d+)(?:-(b\d+))?$", code or "")
    if not m:
        return code or ""
    date, n, tag = m.groups()
    return f"{date} · {n}-entry pass" + (f" ({tag})" if tag else "")


def render_entry(en: dict, fit_labels: dict) -> str:
    tier = en["tier"]
    tlabel, tdesc = TIER_META[tier]
    kind = {"recommended": "ok", "viable": "mid", "conditional": "mid",
            "fallback-only": "warn", "wrong-scale": "warn", "unverified": "bad",
            "do-not-hire": "bad", "historical": "dim"}[tier]
    lic = en["license"]
    hideable = tier in ("do-not-hire", "unverified", "historical", "wrong-scale")

    contact = []
    if en.get("phone_display"):
        contact.append(f'<span class="c-item"><b>Call</b> {e(en["phone_display"])}</span>')
    if en.get("address_display"):
        contact.append(f'<span class="c-item"><b>At</b> {e(en["address_display"])}</span>')
    if en.get("website"):
        contact.append(f'<span class="c-item"><b>Web</b> {link(en["website"], en["website"].replace("https://", "").rstrip("/"))}</span>')
    if en.get("sf_permits"):
        contact.append(f'<span class="c-item"><b>SF plumbing permits</b> {en["sf_permits"]:,}</span>')

    others = ""
    if en.get("other_licenses"):
        rows = "".join(
            f'<li><code>{e(o["number"])}</code> {e(o.get("legal_name") or "not CSLB-captured")} '
            f'{status_badge(o["status_code"])} <span class="muted">expires {e(o.get("expire_date") or "-")}'
            + (f' &middot; {o["sf_permits"]} SF permits' if o.get("sf_permits") else "")
            + "</span></li>" for o in en["other_licenses"])
        others = f'<h4>Related licenses under this brand</h4><ul class="others">{rows}</ul>'

    fit_cells = "".join(
        f'<tr><th>{e(fit_labels.get(k, k))}</th>'
        f'<td>{badge(FIT_CELL.get(en["job_fit"].get(k, "unknown"), ("Unknown", "dim"))[0], FIT_CELL.get(en["job_fit"].get(k, "unknown"), ("Unknown", "dim"))[1])}</td></tr>'
        for k in FIT_LABELS_ORDER)

    crit = sum(1 for f in en["flags"] if f["severity"] == "critical")
    local = 1 if OUTER_SUNSET_RE.search(lic.get("cslb_address") or "") else 0

    return f"""
<article class="card {kind}{' hidden' if hideable else ''}" id="{e(en['id'])}"
         data-tier="{e(tier)}" data-status="{e(lic.get('status_code'))}"
         data-batch="{e(en.get('research_batch') or '')}"
         data-name="{e(en['display_name'].lower())}" data-fit="{en['fit_score']['percent']}"
         data-permits="{en.get('sf_permits') or 0}" data-crit="{crit}"
         data-local="{local}">
  <header class="card-head">
    <div class="rank">#{en['rank']}</div>
    <div class="titles">
      <h3>{e(en['display_name'])}</h3>
      {f'<p class="dba">CSLB legal name: {e(lic.get("legal_name"))}{" &middot; " + e(en["dba"]) if en.get("dba") else ""}</p>' if lic.get('legal_name') or en.get('dba') else ''}
    </div>
    <div class="head-badges">
      {badge(tlabel, kind)}{status_badge(lic.get('status_code'))}
      {badge("NEW · " + batch_label(en["research_batch"]), "info") if en.get("research_batch") else ""}
      <span class="fit" title="Evidence grade across the three core requirements; advertised scope receives partial credit">job fit {en["fit_score"]["percent"]}%</span>
      {badge(f"{crit} critical", "bad") if crit else ""}
    </div>
  </header>

  <p class="headline">{e(en['headline'])}</p>
  <p class="tier-why muted">{e(tdesc)}</p>
  <div class="contact">{''.join(contact) or '<span class="c-item muted">No contact details captured.</span>'}</div>

  <details {"open" if tier == "recommended" else ""}>
    <summary>Job fit against your requirements</summary>
    <table class="kv fit-table">{fit_cells}</table>
  </details>

  <details {"open" if tier == "recommended" else ""}>
    <summary>CSLB license record <span class="muted">(official government source)</span></summary>
    {render_license(lic)}
    {others}
  </details>

  <details {"open" if tier == "recommended" else ""}>
    <summary>Review aggregate</summary>
    {render_ratings(en['ratings'])}
  </details>

  {'<details open><summary>Detail</summary>' + render_evidence(en['evidence']) + render_flags(en['flags']) + render_sources(en['sources']) + '</details>' if tier == 'recommended' else '<details><summary>Detail, evidence, flags and sources</summary>' + render_evidence(en['evidence']) + render_flags(en['flags']) + render_sources(en['sources']) + '</details>'}
</article>"""


def build_legal(legal: dict) -> str:
    def block(item, heading):
        return f"""
      <div class="law">
        <h4>{e(heading)}</h4>
        <blockquote><p>&ldquo;{e(item['quote'])}&rdquo;</p>
        <footer>{e(item['citation'])} {access_badge(item.get('access'))}
        {link(item['url'], 'official source', 'src')}</footer></blockquote>
        {f'<p class="plain">{e(item["plain_language"])}</p>' if item.get('plain_language') else ''}
      </div>"""

    hab = block(legal["habitability"], legal["habitability"]["title"])
    steps = "".join(block(i, f'Step {i["step"]}. {i["title"]}') for i in legal["tenant_remedies"])
    permits = "".join(block(i, i["title"]) for i in legal["permits"])
    rc = block(legal["rent_control"], legal["rent_control"]["title"])
    ah = block(legal["anti_harassment"], legal["anti_harassment"]["title"])
    tech = block(legal["technique"], legal["technique"]["title"])
    return hab, steps, permits, rc, ah, tech


def build_method(m: dict) -> str:
    steps = "".join(f"<li>{e(s)}</li>" for s in m["pipeline"])
    access = "".join(
        f'<tr><td>{e(r["source"])}</td><td><span class="tier t-{e(r["tier"])}">{e(r["tier"])}</span></td>'
        f'<td>{access_badge(r["access"])}</td><td>{e(r["note"])}</td></tr>'
        for r in m["access_log"])
    tiers = "".join(
        f'<tr><td><span class="tier t-{e(t["tier"])}">{e(t["tier"])}</span></td>'
        f'<td>{e(t["label"])}</td><td>{e(t["weight"])}</td><td>{e(t["examples"])}</td></tr>'
        for t in m["trust_tiers"])
    fitvocab = "".join(
        f'<tr><td>{badge(k, "mid")}</td><td>{e(v)}</td></tr>'
        for k, v in m["scoring"]["job_fit_meaning"].items())
    tiervocab = "".join(
        f'<tr><td>{badge(k, "mid")}</td><td>{e(v)}</td></tr>'
        for k, v in m["scoring"]["tier_meaning"].items())
    unc = "".join(
        f'<tr><td>{e(u["name"])}</td><td>{e(u["license"] or "none found")}</td>'
        f'<td>{e(u["sf_permits"] if u["sf_permits"] is not None else "n/a")}</td><td>{e(u["reason"])}</td></tr>'
        for u in m.get("unverified_candidates", []))
    return steps, access, tiers, fitvocab, tiervocab, unc


def main() -> int:
    doc = json.loads((ROOT / "data" / "plumbers.json").read_text(encoding="utf-8"))
    rep = json.loads((ROOT / "data" / "validation_report.json").read_text(encoding="utf-8"))
    if rep["status"] != "PASS":
        print("Refusing to build: data/validation_report.json is FAIL", file=sys.stderr)
        return 1

    entries = doc["entries"]
    fit_labels = doc["fit_labels"]
    counts = doc["counts"]
    job = doc["job"]

    hireable = [x for x in entries if x["tier"] in ("recommended", "viable", "conditional")]
    not_hireable = [x for x in entries if x["tier"] in ("do-not-hire", "unverified", "wrong-scale", "historical")]
    fallback = [x for x in entries if x["tier"] == "fallback-only"]
    batch_order = [
        ("2026-09-04-expansion-20", "20-entry pass"),
        ("2026-09-04-expansion-50", "50-entry pass"),
        ("2026-09-04-expansion-50-b3", "50-entry pass (b3)"),
        ("2026-09-04-expansion-50-b4", "50-entry pass (b4)"),
        ("2026-09-04-expansion-50-b5", "50-entry pass (b5)"),
        ("2026-09-04-expansion-50-b6", "latest 50-entry pass (b6: Thumbtack / BBB / Outer Sunset)"),
    ]
    batch_summaries = []
    for code, label in batch_order:
        bl = [x for x in entries if x.get("research_batch") == code]
        st: dict[str, int] = {}
        for x in bl:
            c = x["license"].get("status_code") or "?"
            st[c] = st.get(c, 0) + 1
        reviewed = sum(1 for x in bl if x.get("ratings") or x.get("evidence"))
        batch_summaries.append((code, label, bl, st, reviewed))
    expansion = [x for x in entries if x.get("research_batch")]
    expansion_count = sum(len(bl) for _, _, bl, _, _ in batch_summaries)

    criticals = []
    for en in entries:
        for f in en["flags"]:
            if f["severity"] == "critical":
                criticals.append((en, f))

    hab, steps, permits, rc, ah, tech = build_legal(doc["legal"])
    m_steps, m_access, m_tiers, m_fitvocab, m_tiervocab, m_unc = build_method(doc["methodology"])

    alert_rows = "".join(
        f'<tr><td>{link("#" + en["id"], en["display_name"])}</td>'
        f'<td>{status_badge(en["license"].get("status_code"))}</td>'
        f'<td><code>{e(en["license"].get("number") or "none")}</code></td>'
        f'<td>{e(f["label"])}</td><td>{e(f["detail"])}</td></tr>'
        for en, f in criticals)

    cards = "".join(render_entry(en, fit_labels) for en in entries)

    top = hireable[:3]

    def zip_of(addr: str | None) -> str:
        m = re.search(r"\b(\d{5})(?:-\d{4})?\s*$", addr or "")
        return m.group(1) if m else ""

    def review_links(en: dict) -> str:
        """Every review-platform link attached to an entry, labelled by host and access."""
        seen: set[str] = set()
        out = []
        pool = [(r.get("platform"), r.get("url"), r.get("access")) for r in en.get("ratings", [])]
        pool += [(None, s_.get("url"), s_.get("access")) for s_ in en.get("sources", [])
                 if s_.get("tier") == "official-platform"]
        for platform, url, access in pool:
            if not url or url in seen:
                continue
            seen.add(url)
            host = (urlparse(url).hostname or "").replace("www.", "")
            name = {"thumbtack.com": "Thumbtack", "bbb.org": "BBB", "yelp.com": "Yelp",
                    "google.com": "Google", "expertise.com": "Expertise"}.get(host, host)
            suffix = "" if (access or "").startswith("direct") else " (manual check)"
            out.append(link(url, e(name + suffix)))
        return " &middot; ".join(out) or '<span class="muted">none captured</span>'

    def local_cell(en: dict) -> str:
        z = zip_of(en["license"].get("cslb_address"))
        if z in ("94122", "94116"):
            return badge("BASED IN 94122/94116", "ok", "CSLB address of record is in the Outer Sunset / Parkside")
        if z.startswith("941"):
            return badge("SF-based", "mid", f"CSLB address of record zip {z}")
        if z:
            return badge(f"outside SF ({z})", "dim", "Confirm dispatch to 94122 before booking")
        return badge("address n/a", "dim")

    def decision_row(en: dict) -> str:
        lic = en["license"]
        best = ""
        if en.get("ratings"):
            r = en["ratings"][0]
            best = f'{e(r.get("platform"))} <b>{e(r.get("score"))}</b>' + (f' ({e(r.get("count"))})' if r.get("count") else "")
        web = link(en["website"], "website") if en.get("website") else '<span class="muted">no site captured</span>'
        return (f'<tr><td>{link("#" + e(en["id"]), e(en["display_name"]))}<br>'
                f'<span class="muted">{e(en.get("phone_display") or "no phone captured")}</span></td>'
                f'<td>{badge(TIER_META[en["tier"]][0], {"recommended": "ok", "viable": "mid", "conditional": "mid"}[en["tier"]])}'
                f'<br><span class="muted">fit {en["fit_score"]["percent"]}%</span></td>'
                f'<td>{link(lic["source_url"], "CSLB " + e(lic["number"]))} {status_badge(lic["status_code"])}<br>'
                f'<span class="muted">exp. {e(lic.get("expire_date"))}</span></td>'
                f'<td>{local_cell(en)}<br><span class="muted">{e(en.get("sf_permits") or 0)} SF permits</span></td>'
                f'<td>{best or "<span class=muted>no aggregate captured</span>"}<br><span class="muted">{review_links(en)}</span></td>'
                f'<td>{web}</td></tr>')

    # Decision table: every hireable entry that has at least one captured review aggregate or
    # quotation (so the reader can open a real review page), best fit first, capped for readability.
    with_reviews = [x for x in hireable if x.get("ratings") or x.get("evidence")]
    decision_pool = with_reviews[:12]
    # plus every ACTIVE business based in the tenant's own zip codes, whether or not reviews were captured
    local_active = [x for x in hireable if zip_of(x["license"].get("cslb_address")) in ("94122", "94116")]
    decision_rows = "".join(decision_row(x) for x in decision_pool)
    local_rows = "".join(decision_row(x) for x in local_active)

    call_list = "".join(
        f'<li><strong>{e(t["display_name"])}</strong> &mdash; '
        f'{e(t.get("phone_display") or "no phone captured")} '
        f'<span class="muted">CSLB {e(t["license"].get("number"))}, {t["license"]["status_code"].upper()}, '
        f'fit {t["fit_score"]["percent"]}%</span><br><span class="muted">{e(t["headline"])}</span></li>'
        for t in top)

    verified = doc["verified_at"]
    generated = doc["generated_at"]

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verified San Francisco Plumbers &mdash; Stuck Tub Overflow &amp; Slow Shower Drain</title>
<meta name="description" content="A line-by-line verified master list of San Francisco plumbers for a slow bathtub and shower drain with a stuck overflow trip lever in a c.1940 rent-controlled rental. Every license checked against the CSLB, every quote traced to a captured source.">
<style>
:root {{
  --ink:#12171f; --ink2:#3d4756; --muted:#6b7684; --line:#dfe4ea; --line2:#eef1f5;
  --bg:#f6f7f9; --card:#fff; --accent:#0b5fa5; --accent2:#083d6b;
  --ok:#0f7b3f; --okbg:#e8f6ed; --mid:#8a6100; --midbg:#fdf3dc;
  --bad:#a3161c; --badbg:#fdecec; --warn:#8a4b00; --warnbg:#fdf0e2;
  --dim:#6b7684; --dimbg:#eef1f5; --radius:10px;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth;scroll-padding-top:76px}}
body{{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}}
a{{color:var(--accent)}}
a:hover{{color:var(--accent2)}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.82em;
  background:var(--line2);padding:.1em .35em;border-radius:4px;color:var(--ink2)}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 20px}}
h1,h2,h3,h4{{line-height:1.25;margin:0 0 .5em}}
h2{{font-size:1.55rem;margin:0 0 .35em;letter-spacing:-.01em}}
h3{{font-size:1.2rem}}
h4{{font-size:.95rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:1.4em 0 .5em}}
p{{margin:0 0 .8em}}
.muted{{color:var(--muted)}}
.empty{{color:var(--muted);font-style:italic}}

/* header */
header.site{{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.96);
  backdrop-filter:saturate(1.4) blur(8px);border-bottom:1px solid var(--line)}}
header.site .wrap{{display:flex;gap:18px;align-items:center;justify-content:space-between;
  padding-top:10px;padding-bottom:10px;flex-wrap:wrap}}
.brand{{font-weight:700;font-size:1.02rem;letter-spacing:-.01em}}
.brand small{{display:block;font-weight:500;color:var(--muted);font-size:.72rem;letter-spacing:.04em}}
nav.jump{{display:flex;gap:4px;flex-wrap:wrap}}
nav.jump a{{font-size:.8rem;padding:5px 9px;border-radius:6px;text-decoration:none;color:var(--ink2)}}
nav.jump a:hover{{background:var(--line2);color:var(--accent)}}

/* hero */
.hero{{background:linear-gradient(160deg,#0b2540,#0b5fa5);color:#fff;padding:38px 0 34px}}
.hero h1{{font-size:2.05rem;letter-spacing:-.02em;max-width:22ch}}
.hero .lede{{font-size:1.06rem;max-width:70ch;color:#dbe7f3}}
.hero .meta{{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}}
.pill{{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.24);
  padding:6px 12px;border-radius:999px;font-size:.82rem}}
.pill b{{font-variant-numeric:tabular-nums}}

/* stat strip */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0 0}}
.stat{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:var(--radius);padding:12px 14px}}
.stat b{{display:block;font-size:1.6rem;line-height:1.1;font-variant-numeric:tabular-nums}}
.stat span{{font-size:.78rem;color:#c8d8e8}}

section{{padding:34px 0;border-bottom:1px solid var(--line)}}
section > .wrap > p.sub{{color:var(--ink2);max-width:80ch}}

/* job brief */
.brief{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin-top:16px}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px}}
.panel h3{{font-size:1rem;margin-bottom:.5em}}
.panel ul{{margin:.2em 0 0;padding-left:1.15em}}
.panel li{{margin-bottom:.45em}}
.panel.key{{border-left:4px solid var(--accent);background:#f4f9fe}}
.panel.permit{{border-left:4px solid var(--ok);background:var(--okbg)}}

/* alerts */
.alertbox{{background:var(--badbg);border:1px solid #f0c9cb;border-left:4px solid var(--bad);
  border-radius:var(--radius);padding:16px 18px;margin-top:14px}}
.alertbox h3{{color:var(--bad)}}
table{{width:100%;border-collapse:collapse;background:var(--card);
  border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;font-size:.88rem}}
th,td{{text-align:left;padding:9px 11px;border-bottom:1px solid var(--line2);vertical-align:top}}
thead th{{background:#f0f3f7;font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink2)}}
tbody tr:last-child td{{border-bottom:none}}
td p{{margin:0}}

/* badges */
.badge{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.71rem;
  font-weight:700;letter-spacing:.04em;text-transform:uppercase;white-space:nowrap;
  border:1px solid transparent}}
.b-ok{{background:var(--okbg);color:var(--ok);border-color:#bfe3cd}}
.b-mid{{background:var(--midbg);color:var(--mid);border-color:#eeddb0}}
.b-bad{{background:var(--badbg);color:var(--bad);border-color:#f0c9cb}}
.b-warn{{background:var(--warnbg);color:var(--warn);border-color:#f0d6b8}}
.b-info,.b-dim{{background:var(--dimbg);color:var(--dim);border-color:var(--line)}}
.tier{{font-size:.7rem;font-family:ui-monospace,Menlo,monospace;background:var(--line2);
  padding:1px 6px;border-radius:4px;color:var(--ink2);white-space:nowrap}}
.t-official-gov{{background:#e3eefb;color:#0b4d8f;font-weight:700}}
.t-official-platform{{background:#eaf5ec;color:#146c39}}
.t-community{{background:#f6ecfa;color:#7a3a94}}
.t-vendor-self-reported{{background:#fdf1e6;color:#94511a}}
.t-third-party-aggregator{{background:#eef1f5;color:#4a5666}}
.t-tenant-advocacy-org{{background:#e8f4f6;color:#136b78}}
.t-manufacturer{{background:#f2ecff;color:#633c9b}}

/* toolbar */
.toolbar{{position:sticky;top:60px;z-index:40;background:rgba(246,247,249,.97);
  backdrop-filter:blur(6px);padding:12px 0;margin-bottom:16px;border-bottom:1px solid var(--line)}}
.toolbar .row{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.toolbar input[type=search]{{flex:1 1 240px;min-width:200px;padding:9px 12px;font-size:.9rem;
  border:1px solid var(--line);border-radius:8px;background:#fff}}
.toolbar button{{padding:7px 13px;font-size:.8rem;border:1px solid var(--line);background:#fff;
  border-radius:999px;cursor:pointer;color:var(--ink2);font-weight:600}}
.toolbar button:hover{{border-color:var(--accent);color:var(--accent)}}
.toolbar button[aria-pressed=true]{{background:var(--accent);border-color:var(--accent);color:#fff}}
.toolbar select{{padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:.85rem}}
.count{{font-size:.82rem;color:var(--muted);margin-left:auto}}

/* cards */
.card{{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:18px 20px;margin-bottom:14px;border-left:5px solid var(--line)}}
.card.ok{{border-left-color:var(--ok)}}
.card.mid{{border-left-color:#d8b45a}}
.card.warn{{border-left-color:#e0913c}}
.card.bad{{border-left-color:var(--bad);background:#fffafa}}
.card.dim{{border-left-color:var(--dim);opacity:.92}}
.card.hidden{{display:none}}
.card-head{{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap}}
.rank{{font-size:1.35rem;font-weight:800;color:var(--muted);font-variant-numeric:tabular-nums;min-width:46px}}
.titles{{flex:1 1 240px}}
.titles h3{{margin:0}}
.dba{{font-size:.8rem;color:var(--muted);margin:.15em 0 0}}
.head-badges{{display:flex;gap:6px;flex-wrap:wrap;align-items:center}}
.fit{{background:#eef4fb;color:var(--accent2);padding:3px 9px;border-radius:999px;
  font-size:.74rem;font-weight:700;cursor:help}}
.headline{{margin:.7em 0 .3em;font-size:.98rem}}
.tier-why{{font-size:.82rem;margin-bottom:.7em}}
.contact{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:.4em}}
.c-item{{background:var(--line2);border-radius:7px;padding:5px 10px;font-size:.82rem}}
.c-item b{{display:block;font-size:.66rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
details{{border-top:1px solid var(--line2);margin-top:10px;padding-top:8px}}
summary{{cursor:pointer;font-weight:600;font-size:.88rem;color:var(--accent2);padding:3px 0}}
summary:hover{{color:var(--accent)}}
.kv{{font-size:.85rem;margin-top:10px}}
.kv th{{width:34%;background:#fafbfc;font-weight:600;font-size:.78rem;color:var(--ink2);
  text-transform:none;letter-spacing:0}}
.fit-table th{{width:56%}}
.lic-none{{padding:10px 0}}
.lic-note{{font-size:.85rem;color:var(--ink2)}}
.prov{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px;font-size:.78rem}}
.btn{{display:inline-block;background:var(--accent);color:#fff;padding:6px 13px;border-radius:7px;
  text-decoration:none;font-size:.8rem;font-weight:600}}
.btn:hover{{background:var(--accent2);color:#fff}}
ul.ratings{{list-style:none;padding:0;margin:10px 0 0}}
ul.ratings li{{padding:7px 0;border-bottom:1px solid var(--line2);font-size:.87rem}}
ul.ratings li:last-child{{border-bottom:none}}
.plat{{font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;color:var(--ink2)}}
a.src{{font-size:.78rem}}
.quotes{{display:grid;gap:10px;margin-top:8px}}
blockquote{{margin:0;background:#fafbfc;border:1px solid var(--line2);border-left:3px solid var(--accent);
  border-radius:0 8px 8px 0;padding:11px 14px}}
blockquote p{{margin:0 0 .5em;font-size:.92rem}}
blockquote footer{{font-size:.78rem;color:var(--muted);display:flex;gap:7px;align-items:center;flex-wrap:wrap}}
.signals{{display:flex;gap:5px;flex-wrap:wrap;width:100%;margin-top:6px}}
.chip{{background:#eef4fb;color:var(--accent2);font-size:.7rem;padding:2px 8px;border-radius:999px}}
ul.flags{{list-style:none;padding:0;margin:8px 0 0}}
ul.flags li{{padding:9px 12px;border-radius:8px;margin-bottom:8px;font-size:.87rem}}
ul.flags li p{{margin:.3em 0 0;color:var(--ink2)}}
.f-bad{{background:var(--badbg);border:1px solid #f0c9cb}}
.f-warn{{background:var(--warnbg);border:1px solid #f0d6b8}}
.f-info{{background:var(--line2);border:1px solid var(--line)}}
ul.sources{{list-style:none;padding:0;margin:8px 0 0;font-size:.85rem}}
ul.sources li{{padding:7px 0;border-bottom:1px solid var(--line2);display:flex;gap:8px;
  align-items:center;flex-wrap:wrap}}
ul.sources li:last-child{{border-bottom:none}}
ul.others{{margin:8px 0 0;padding-left:1.15em;font-size:.85rem}}
.law{{margin-bottom:16px}}
.law blockquote{{border-left-color:var(--ok)}}
.plain{{font-size:.9rem;background:#fff;border:1px dashed var(--line);border-radius:8px;padding:10px 13px;margin-top:8px}}
ol.steps{{padding-left:1.2em}}
ol.steps li{{margin-bottom:.5em}}
.dl{{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}}
footer.site{{padding:28px 0 46px;color:var(--muted);font-size:.84rem}}
footer.site p{{max-width:90ch}}
.legend{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}}
@media (max-width:640px){{
  .hero h1{{font-size:1.6rem}}
  .rank{{min-width:34px;font-size:1.1rem}}
  .kv th{{width:42%}}
  nav.jump{{display:none}}
  .toolbar{{top:54px}}
}}
@media print{{
  header.site,.toolbar,nav.jump{{display:none}}
  .card.hidden{{display:none}}
  details{{display:block}}
  details > summary{{display:none}}
  details > *{{display:block}}
  body{{background:#fff}}
  .card{{break-inside:avoid;border:1px solid #ccc}}
}}
</style>
</head>
<body>

<header class="site"><div class="wrap">
  <div class="brand">SF Verified Plumbers<small>line-by-line source-checked &middot; {e(verified)}</small></div>
  <nav class="jump" aria-label="Sections">
    <a href="#job">The job</a><a href="#decide">Decision table</a><a href="#alerts">Alerts</a><a href="#list">Master list</a>
    <a href="#matrix">Fit matrix</a><a href="#flags">Irregularities</a><a href="#rights">Tenant rights</a>
    <a href="#permits">Permits</a><a href="#method">Method</a>
  </nav>
</div></header>

<div class="hero"><div class="wrap">
  <h1>San Francisco plumbers verified for one specific job</h1>
  <p class="lede">A bathtub draining at about 20% of normal and a shower at 60&ndash;80%, in a c.1940 house with
  likely original galvanized drain piping, and a bathtub overflow trip lever seized behind a wall with no access
  from below. Every licensed business below was checked against the California Contractors State License Board;
  every published excerpt and rating is tied to a dated capture with its access method disclosed.</p>
  <div class="meta">
    <span class="pill">Verified <b>{e(verified)}</b></span>
    <span class="pill">Generated <b>{e(generated)}</b></span>
    <span class="pill">Validation <b>{e(rep['status'])}</b> &middot; {len(rep['errors'])} errors</span>
    <span class="pill"><b>{counts['raw_capture_files']}</b> raw capture files</span>
  </div>
  <div class="stats">
    <div class="stat"><b>{counts['entries']}</b><span>businesses on the master list</span></div>
    <div class="stat"><b>{expansion_count}</b><span>newly researched entries ({len(batch_order)} passes)</span></div>
    <div class="stat"><b>{counts['cslb_records_captured']}</b><span>CSLB license records checked</span></div>
    <div class="stat"><b>{counts['active_verified_businesses']}</b><span>entries with a verified ACTIVE license</span></div>
    <div class="stat"><b>{len(hireable)}</b><span>hireable screening candidates</span></div>
    <div class="stat"><b>{rep['quotes_verified']}</b><span>source excerpts checked verbatim</span></div>
    <div class="stat"><b>{len(criticals)}</b><span>critical irregularities flagged</span></div>
  </div>
</div></div>

<section id="job"><div class="wrap">
  <h2>The job, stated precisely</h2>
  <p class="sub">{e(job['summary'])}</p>
  <div class="brief">
    <div class="panel key">
      <h3>Hard requirements</h3>
      <ul>{''.join(f'<li>{e(r)}</li>' for r in job['hard_requirements'])}</ul>
    </div>
    <div class="panel">
      <h3>Context that changes the answer</h3>
      <ul>{''.join(f'<li>{e(c)}</li>' for c in job['context'])}</ul>
    </div>
    <div class="panel permit">
      <h3>The permit fact that matters most</h3>
      <p>{e(job['permit_note'])}</p>
      <p>{link('https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_building/0-0-0-85830','SF Building Code &sect;104.2','btn')}</p>
    </div>
  </div>
  <div class="panel" style="margin-top:14px;border-left:4px solid var(--warn);background:var(--warnbg)">
    <h3>Important result: overflow expertise is not proven for any firm</h3>
    <p>No retained review or authoritative contractor source describes safely extracting a seized c.1940
    trip-lever linkage with no access from below. The three names below are the strongest <em>first-screen</em>
    leads, not confirmed overflow specialists. Get the method and no-demolition limit in writing.</p>
  </div>
  <h4>Who to screen first</h4>
  <ol class="steps">{call_list}</ol>

  <div class="panel" style="margin-top:14px" id="decide">
    <h3>Decision table &mdash; verified, reviewable candidates at a glance</h3>
    <p class="muted">The hireable businesses that have at least one captured review page, best evidence first.
    Every row links the business card, its official CSLB record, each review page that was actually opened
    (links marked <em>manual check</em> were not fetched and must be opened by hand) and the business website
    where one was published. &ldquo;BASED IN 94122/94116&rdquo; means the CSLB address of record is in the
    Outer Sunset / Parkside; every other row must be asked whether they dispatch to 94122.</p>
    <table><thead><tr><th>Business</th><th>Tier / fit</th><th>CSLB license</th><th>Locality &amp; SF permits</th><th>Reviews</th><th>Site</th></tr></thead>
    <tbody>{decision_rows}</tbody></table>
    <h4>ACTIVE licenses based in the Outer Sunset / Parkside (94122 / 94116)</h4>
    <p class="muted">Neighbourhood businesses with a current license. Most have no captured review evidence, so they are
    phone-screen candidates rather than leads; locality is a convenience signal, not a skill signal.</p>
    <table><thead><tr><th>Business</th><th>Tier / fit</th><th>CSLB license</th><th>Locality &amp; SF permits</th><th>Reviews</th><th>Site</th></tr></thead>
    <tbody>{local_rows or '<tr><td colspan="6" class="muted">none</td></tr>'}</tbody></table>
  </div>
  <p class="muted">Ask every bidder the same screening question before they quote:
  <em>&ldquo;Have you removed a seized trip-lever linkage through the overflow opening on an old tub? Will you
  snake the shower and stop before opening any wall or replacing concealed piping unless the landlord gives
  separate written authorization?&rdquo;</em> Do not infer experience from a generic bathtub-service category.</p>
  <div class="panel" style="margin-top:14px">
    <h3>Expansion verification passes (2026-09-04)</h3>
    <p class="muted">{expansion_count} additional businesses surfaced from San Francisco plumbing-permit
    records, Thumbtack, BBB and the Outer Sunset permit filers were verified line by line against the official
    CSLB across {len(batch_order)} fixed passes:</p>
    <table><thead><tr><th>Pass</th><th>Entries</th><th>CSLB status breakdown</th><th>Review evidence</th></tr></thead>
    <tbody>{''.join(
        '<tr><td>' + e(label) + '</td><td><b>' + str(len(bl)) + '</b></td><td>'
        + ' &middot; '.join(f'<b>{n}</b> {k}' for k, n in sorted(st.items()))
        + '</td><td>' + ('<b>' + str(rv) + '</b> with captured review evidence' if rv else 'license-verified only')
        + '</td></tr>' for code, label, bl, st, rv in batch_summaries)}
    </tbody></table>
    <p class="muted">Passes b4 and b5 carry no captured review-platform evidence: their 50 businesses each are
    license-verified against the official CSLB only and must be screened by phone. Pass b6 re-opened Thumbtack
    and BBB directly (profiles, ratings, review text and platform licence badges captured verbatim) and added
    every plumbing-permit filer whose own business address is in 94122/94116. Non-hireable entries
    (revoked, suspended, inactive, canceled or expired at the verification date) remain published as
    <em>do-not-hire warnings</em>, because several of these brand names still advertise in San Francisco
    under licenses the state no longer honours. Open each entry's CSLB record before booking. Nothing in
    these passes proves a firm has extracted a seized trip lever without opening a wall.</p>
  </div>
</div></section>

<section id="alerts"><div class="wrap">
  <h2>Critical irregularities found</h2>
  <p class="sub">These include license disqualifications, platform/CSLB conflicts, complaint disclosure and
  entity-history risks. An ACTIVE badge does not erase a listed critical review item; open the source before booking.</p>
  <div class="alertbox">
    <h3>{len(criticals)} critical review items</h3>
    <table><thead><tr><th>Business</th><th>CSLB status</th><th>License</th><th>Finding</th><th>Detail</th></tr></thead>
    <tbody>{alert_rows}</tbody></table>
  </div>
</div></section>

<section id="list"><div class="wrap">
  <h2>Master list &mdash; {counts['entries']} businesses</h2>
  <p class="sub">Includes {len(expansion)} newly researched, de-duplicated entries, marked NEW. Sorted by tier,
  evidence grade and SF permit depth. Non-hireable entries are hidden by default; reveal them to inspect the reason.</p>

  <div class="toolbar"><div class="row">
    <input type="search" id="q" placeholder="Filter by name, license number or DBA&hellip;" aria-label="Search the master list">
    <select id="sort" aria-label="Sort">
      <option value="rank">Default order</option>
      <option value="permits">SF permits (high to low)</option>
      <option value="fit">Job fit (high to low)</option>
      <option value="name">Name (A&ndash;Z)</option>
    </select>
    <span class="count" id="count" role="status" aria-live="polite"></span>
  </div>
  <div class="row" style="margin-top:8px">
    <button data-filter="all" aria-pressed="true">All hireable</button>
    <button data-filter="recommended" aria-pressed="false">First-screen leads</button>
    <button data-filter="new" aria-pressed="false">New ({expansion_count})</button>
    <button data-filter="newb6" aria-pressed="false">Latest 50-entry pass (b6)</button>
    <button data-filter="local" aria-pressed="false">Based in 94122/94116</button>
    <button data-filter="viable" aria-pressed="false">Verified &amp; viable</button>
    <button data-filter="conditional" aria-pressed="false">Partial fit</button>
    <button data-filter="flagged" aria-pressed="false">Flagged / not hireable</button>
    <button data-filter="active" aria-pressed="false">ACTIVE license only</button>
  </div>
  </div>

  <div id="cards">{cards}</div>
</div></section>

<section id="matrix"><div class="wrap">
  <h2>Job-fit matrix</h2>
  <p class="sub">Only businesses with a verified ACTIVE CSLB license are shown. &ldquo;Documented&rdquo; means a
  captured source describes that exact task; &ldquo;documented (adjacent)&rdquo; is similar work on another fixture;
  &ldquo;advertised&rdquo; is service-menu scope only; &ldquo;unknown&rdquo; means ask. None is documented for the exact seized linkage.</p>
  <table><thead><tr><th>Business</th><th>License</th>
  {''.join(f'<th>{e(fit_labels[k])}</th>' for k in FIT_LABELS_ORDER)}</tr></thead><tbody>
  {''.join('<tr><td><a href="#' + e(x['id']) + '">' + e(x['display_name']) + '</a></td><td><code>' + e(x['license'].get('number') or '-') + '</code></td>' + ''.join('<td>' + badge(*FIT_CELL.get(x['job_fit'].get(k, 'unknown'), ('Unknown', 'dim'))) + '</td>' for k in FIT_LABELS_ORDER) + '</tr>' for x in hireable)}
  </tbody></table>
</div></section>

<section id="flags"><div class="wrap">
  <h2>Every flag raised, in one place</h2>
  <p class="sub">Grouped by business. Each flag is grounded in a captured CSLB field, permit row, platform page
  or explicit evidence limitation. Where the source does not establish a cause, the flag says so.</p>
  {''.join('<div class="panel" style="margin-bottom:12px"><h3 style="margin-bottom:.2em">' + link('#' + e(en['id']), e(en['display_name'])) + ' <code>' + e(en['license'].get('number') or 'no license') + '</code> ' + status_badge(en['license'].get('status_code')) + '</h3>' + render_flags(en['flags']).replace('<h4>Flags &amp; irregularities</h4>', '') + '</div>' for en in entries if en['flags'])}
</div></section>

<section id="rights"><div class="wrap">
  <h2>Your rights as a San Francisco tenant</h2>
  <p class="sub">This is a rent-controlled rental, so coordinate repair authority and any expanded scope with the landlord
  or property manager. The cited government text, tenant-advocacy guidance and labelled legal summaries are linked for
  direct review. Not legal advice &mdash; the San Francisco Tenants Union and Housing Rights Committee
  both offer free counselling.</p>
  <h3>Habitability</h3>
  {hab}
  <h3>What you can actually do, in order</h3>
  {steps}
  <h3>Rent control coverage</h3>
  {rc}
  {ah}
</div></section>

<section id="permits"><div class="wrap">
  <h2>Permit rules &mdash; why &ldquo;no opening the walls&rdquo; is also the faster path</h2>
  <p class="sub">San Francisco exempts drain clearing from permitting, and requires a permit the moment covered
  piping is cut into. That makes your constraint the legally simpler one, and it gives you a fast test of whether
  a bidder intends to demolish.</p>
  {permits}
  <h3>Manufacturer guidance for overflow access and drain cabling</h3>
  {tech}
</div></section>

<section id="method"><div class="wrap">
  <h2>Method, provenance and what could not be verified</h2>
  <p class="sub">This project exists because review platforms can contradict the licensing record.
  <code>scripts/validate.py</code> machine-checks every copied license field, published excerpt, rating value and
  legal quotation against its capture; it also enforces the fixed 20- and 50-entry expansion gates (exact
  license sets, status summaries and required irregularity flags) and duplicate gates.</p>

  <h3>Pipeline</h3>
  <ol class="steps">{m_steps}</ol>

  <h3>Validation run</h3>
  <table><tbody>
    <tr><th>Result</th><td>{badge(rep['status'], 'ok' if rep['status'] == 'PASS' else 'bad')}</td></tr>
    <tr><th>Entries</th><td>{rep['entries']}</td></tr>
    <tr><th>CSLB records checked</th><td>{rep['cslb_records_checked']}</td></tr>
    <tr><th>Businesses with a verified ACTIVE license</th><td>{rep['active_verified_businesses']}</td></tr>
    <tr><th>Raw capture files</th><td>{rep['raw_capture_files']}</td></tr>
    <tr><th>Quotes verified verbatim</th><td>{rep['quotes_verified']}</td></tr>
    <tr><th>Rating aggregates checked</th><td>{rep['ratings_verified']}</td></tr>
    <tr><th>Errors</th><td>{len(rep['errors'])}</td></tr>
    <tr><th>Warnings</th><td>{len(rep['warnings'])}</td></tr>
    <tr><th>Report</th><td><code>data/validation_report.json</code></td></tr>
  </tbody></table>

  <h3>Source access log &mdash; including what was blocked</h3>
  <p class="sub">Honesty about how each number was obtained. Anything marked <em>indirect</em> was not fetched
  from the platform itself and must be re-checked by hand before you rely on a specific figure.</p>
  <table><thead><tr><th>Source</th><th>Trust tier</th><th>Access</th><th>Note</th></tr></thead>
  <tbody>{m_access}</tbody></table>

  <h3>Trust tiers</h3>
  <table><thead><tr><th>Tier</th><th>Label</th><th>Weight given</th><th>Examples</th></tr></thead>
  <tbody>{m_tiers}</tbody></table>

  <h3>Scoring vocabulary</h3>
  <table><thead><tr><th>Job-fit value</th><th>Meaning</th></tr></thead><tbody>{m_fitvocab}</tbody></table>
  <table style="margin-top:12px"><thead><tr><th>Tier</th><th>Meaning</th></tr></thead><tbody>{m_tiervocab}</tbody></table>

  <h3>Candidates that could NOT be verified</h3>
  <p class="sub">Listed so you know they were looked at and rejected, not overlooked.</p>
  <table><thead><tr><th>Business</th><th>License</th><th>SF permits</th><th>Why not verified</th></tr></thead>
  <tbody>{m_unc}</tbody></table>

  <h3>Dataset caveat</h3>
  <div class="panel"><p>{e(doc['methodology']['dataset_caveat'])}</p></div>

  <h3>Download the data</h3>
  <p class="sub">The same data that renders this page, in machine-readable form.</p>
  <div class="dl">
    <a class="btn" href="data/master_list.csv" download>master_list.csv</a>
    <a class="btn" href="data/plumbers.json" download>plumbers.json</a>
    <a class="btn" href="data/validation_report.json" download>validation_report.json</a>
    <a class="btn" href="https://github.com/buffedlizard55-lab/PlumbingSF">Source repository</a>
  </div>
</div></section>

<footer class="site"><div class="wrap">
  <p><strong>Verification date: {e(verified)}.</strong> CSLB license statuses change. Re-check any license at
  {link('https://www2.cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx','cslb.ca.gov Check a License')}
  on the day you book.</p>
  <p>This is research, not legal advice or a guarantee of workmanship. It is not an endorsement of any business:
  entries are ranked by verified license status, captured evidence grade, and San Francisco permit history.
  The validator re-checks copied official fields, published excerpts and rating values against files in
  <code>data/raw/</code>. Analytical headlines are conservative summaries, not guarantees of skill.</p>
  <p>Sources: California Contractors State License Board &middot; City &amp; County of San Francisco open data and
  Building Code &middot; California Legislative Information &middot; Better Business Bureau (direct) &middot; Thumbtack (direct)
  &middot; Yelp (indirect snippets / manual links) &middot; Google (manual links / indirect aggregates) &middot; Expertise
  &middot; Oatey/Dearborn &middot; Gerber &middot; San Francisco Tenants Union. Reddit access was blocked and no
  Reddit quotation is used as candidate evidence.</p>
</div></footer>

<script>
(function(){{
  var cards = Array.prototype.slice.call(document.querySelectorAll('#cards .card'));
  var q = document.getElementById('q'), sortSel = document.getElementById('sort');
  var countEl = document.getElementById('count');
  var container = document.getElementById('cards');
  var filter = 'all';
  var HIREABLE = ['recommended','viable','conditional'];

  function matches(c){{
    var t = c.dataset.tier, s = c.dataset.status;
    var okFilter = filter === 'all' ? HIREABLE.indexOf(t) >= 0
      : filter === 'flagged' ? HIREABLE.indexOf(t) < 0
      : filter === 'active' ? s === 'active'
      : filter === 'new' ? (c.dataset.batch || '').indexOf('2026-09-04-expansion') === 0
      : filter === 'newb6' ? c.dataset.batch === '2026-09-04-expansion-50-b6'
      : filter === 'local' ? c.dataset.local === '1'
      : t === filter;
    if (!okFilter) return false;
    var term = (q.value || '').trim().toLowerCase();
    if (!term) return true;
    var hay = (c.dataset.name + ' ' + c.textContent.toLowerCase());
    return hay.indexOf(term) >= 0;
  }}

  function apply(){{
    var shown = 0;
    cards.forEach(function(c){{
      var ok = matches(c);
      c.classList.toggle('hidden', !ok);
      if (ok) shown++;
    }});
    var mode = sortSel.value;
    var sorted = cards.slice().sort(function(a,b){{
      if (mode === 'permits') return (+b.dataset.permits) - (+a.dataset.permits);
      if (mode === 'fit') return (+b.dataset.fit) - (+a.dataset.fit);
      if (mode === 'name') return a.dataset.name.localeCompare(b.dataset.name);
      return (+a.querySelector('.rank').textContent.slice(1)) - (+b.querySelector('.rank').textContent.slice(1));
    }});
    sorted.forEach(function(c){{ container.appendChild(c); }});
    countEl.textContent = shown + ' of ' + cards.length + ' businesses shown';
  }}

  q.addEventListener('input', apply);
  sortSel.addEventListener('change', apply);
  document.querySelectorAll('.toolbar button[data-filter]').forEach(function(b){{
    b.addEventListener('click', function(){{
      document.querySelectorAll('.toolbar button[data-filter]').forEach(function(x){{
        x.setAttribute('aria-pressed', String(x === b));
      }});
      filter = b.dataset.filter;
      apply();
    }});
  }});
  apply();
}})();
</script>
</body></html>
"""

    # Generated interpolation can leave indentation on otherwise empty lines;
    # normalize it so the committed artifact stays diff-clean.
    page = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    (DOCS / "data").mkdir(exist_ok=True)
    for f in ("master_list.csv", "plumbers.json", "validation_report.json"):
        (DOCS / "data" / f).write_bytes((ROOT / "data" / f).read_bytes())
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")

    # The repo's GitHub Pages site may be configured either as
    #   branch=<this branch>, path=/docs   (canonical - docs/index.html is the root)
    # or
    #   branch=main, path=/                (repo root is the site)
    # This stub makes the second configuration work too, at the cost of one
    # redirect hop. It is never served in the first configuration.
    (ROOT / "index.html").write_text("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verified San Francisco Plumbers &mdash; redirecting</title>
<meta http-equiv="refresh" content="0; url=docs/index.html">
<link rel="canonical" href="docs/index.html">
<script>location.replace("docs/index.html" + location.search + location.hash);</script>
<style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f6f7f9;
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#12171f}
.box{text-align:center;padding:32px}
a{color:#0b5fa5;font-weight:600}
code{background:#eef1f5;padding:.15em .4em;border-radius:4px;font-size:.85em}
</style>
</head>
<body>
<div class="box">
<p><strong>Verified San Francisco Plumbers</strong></p>
<p>The site lives at <a href="docs/index.html"><code>docs/index.html</code></a>.</p>
<p>If you are not redirected, <a href="docs/index.html">click here</a>.</p>
</div>
</body>
</html>
""", encoding="utf-8")

    print(f"docs/index.html  {len(page):,} bytes")
    print("index.html       redirect stub for Pages configured at path=/")
    print(f"  {len(hireable)} hireable cards, {len(not_hireable)} flagged, "
          f"{len(fallback)} fallback")
    print(f"  {len(criticals)} critical findings surfaced")
    return 0


if __name__ == "__main__":
    sys.exit(main())
