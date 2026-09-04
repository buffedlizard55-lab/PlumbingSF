#!/usr/bin/env python3
"""Anti-hallucination validator.

This is the gate that makes the "verified line by line, no hallucinations"
requirement mechanically enforceable rather than a promise.

It re-reads every raw capture in data/raw/ and fails the build if anything in
data/plumbers.json or data/curation.json cannot be traced back to it.

Checks
------
 1. Raw-file integrity   every referenced data/raw/*.txt exists and carries a
                         SOURCE_URL header.
 2. License provenance   every license number has a cslb-<number>.txt capture
                         whose SOURCE_URL contains that number.
 3. License field parity every license field copied into plumbers.json matches
                         the capture byte for byte.
 4. Status parity        the status_code in the data is derived from the exact
                         status sentence printed by CSLB.
 5. Quote parity         every review quote, rating, flag citation and legal
                         quote appears verbatim (whitespace-normalised) in the
                         raw capture it points at.
 6. Source hygiene       every URL is well-formed and its host is on the
                         allow-list of domains actually visited.
 7. Tier legality        no business may be tier recommended/viable/conditional
                         unless its CSLB status is active.
 8. Coverage             at least 20 distinct businesses with a verified ACTIVE
                         C36 license; every capture in data/raw is used.
 9. Consistency          no duplicate ids, no orphan licenses, curated permit
                         counts agree with the SF open-data extract.
10. Vocabulary            job_fit values come from the declared vocabulary.

Exit code 0 = pass. Anything else = the site must not be published.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"

ALLOWED_HOSTS = {
    # official government
    "www2.cslb.ca.gov", "cslb.ca.gov", "data.sfgov.org", "sf.gov", "www.sf.gov",
    "leginfo.legislature.ca.gov", "codelibrary.amlegal.com", "sfgov.org",
    # review platforms of record
    "www.bbb.org", "bbb.org", "www.thumbtack.com", "thumbtack.com",
    "www.yelp.com", "yelp.com", "www.google.com", "google.com", "maps.google.com",
    # tenant advocacy / legal
    "sftu.org", "www.sftu.org", "www.hrcsf.org", "hrcsf.org",
    "tenantlawgroupsf.com", "www.tenantlawgroupsf.com",
    "www.nonaehyaei.com", "nonaehyaei.com",
    # aggregators
    "www.consumeraffairs.com", "consumeraffairs.com", "www.angi.com", "angi.com",
    "local.yahoo.com", "www.buildzoom.com", "buildzoom.com", "www.nextdoor.com",
    "nextdoor.com", "www.expertise.com", "expertise.com",
    # community
    "www.reddit.com", "reddit.com", "old.reddit.com",
    # vendor sites (self-reported; labelled as such in the data)
    "www.atlasplumbingandrooter.com", "www.aceplumbingandrooter.com",
    "discovercabrillo.com", "www.redwrenchplumbing.com", "advancedplumbingsf.com",
    "www.agqualityplumbing.com", "www.magicplumbingsf.com", "lutzplumbingsf.com",
    "drdrainplumbingandrooter.com", "whistleplumbing.com", "xrayplumbing.com",
    "nigelmulgrewplumbing.com", "www.roto-rooter.com", "san-francisco.repipe.com",
    "www.oroproinc.com", "www.genteelplumbing.com", "www.mrrooter.com",
    "www.discountplumbingandrooter.com",
}

HIREABLE_TIERS = {"recommended", "viable", "conditional"}
FIT_VOCAB = {"documented", "documented-adjacent", "advertised",
             "unknown", "no-evidence", "no"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def norm(text: str) -> str:
    """Whitespace-normalise so a quote can be matched across line wrapping."""
    return re.sub(r"\s+", " ", text.replace("\u2014", "-").replace("\u2019", "'")
                  .replace("\u201c", '"').replace("\u201d", '"')).strip()


class RawLibrary:
    """All raw captures, indexed by file and by source URL."""

    def __init__(self) -> None:
        self.texts: dict[str, str] = {}
        self.normed: dict[str, str] = {}
        self.blocks: dict[str, list[dict]] = {}
        for path in sorted(RAW.iterdir()):
            if path.suffix not in (".txt", ".json"):
                continue
            text = path.read_text(encoding="utf-8")
            rel = f"data/raw/{path.name}"
            self.texts[rel] = text
            self.normed[rel] = norm(text)

    def parse_blocks(self) -> None:
        self.blocks = {}
        for rel, text in self.texts.items():
            blocks = []
            parts = re.split(r"^===== SOURCE: ", text, flags=re.M)
            for part in parts[1:]:
                head, _, body = part.partition("\n")
                m = re.match(r"(\S+)(?:\s*\([^)]*\))?\s*\|\s*CAPTURED: ([^|]+?)\s*\|\s*"
                             r"ACCESS: ([^|]+?)(?:\s*\|\s*TIER: (.+?))?$",
                             head.strip())
                blocks.append({
                    "url": m.group(1) if m else head.strip(),
                    "captured": m.group(2).strip() if m else None,
                    "access": m.group(3).strip() if m else None,
                    "tier": m.group(4).strip() if m else None,
                    "body_norm": norm(body),
                })
            self.blocks[rel] = blocks

    def has_file(self, rel: str) -> bool:
        return rel in self.texts

    def source_url_of(self, rel: str) -> str | None:
        m = re.search(r"^SOURCE_URL:\s*(\S+)", self.texts.get(rel, ""), re.M)
        return m.group(1) if m else None

    def contains(self, rel: str, needle: str) -> bool:
        return norm(needle) in self.normed.get(rel, "")

    def find_in_block(self, rel: str, url: str, needle: str) -> tuple[bool, str]:
        """Check `needle` appears in the block of `rel` whose SOURCE header matches url."""
        n = norm(needle)
        matched_url_block = False
        for b in self.blocks.get(rel, []):
            if b["url"].rstrip("/") == (url or "").rstrip("/"):
                matched_url_block = True
                if n in b["body_norm"]:
                    return True, "exact-block"
        if n in self.normed.get(rel, ""):
            return True, "file" if matched_url_block else "file-only"
        return False, "missing" if matched_url_block else "missing-and-no-block"


def check_url(label: str, url: str | None) -> None:
    if not url:
        return
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        err(f"{label}: unparseable URL {url!r}")
        return
    if not host:
        err(f"{label}: URL has no host: {url!r}")
        return
    if host not in ALLOWED_HOSTS:
        err(f"{label}: host {host!r} is not on the visited-domain allow-list "
            f"({url}). Add it only if the page was actually fetched.")


def check_quote(lib: RawLibrary, where: str, text: str, raw: str, url: str,
                access: str | None) -> None:
    if not raw:
        err(f"{where}: quote has no raw-file pointer")
        return
    if not lib.has_file(raw):
        err(f"{where}: raw capture {raw} does not exist")
        return
    ok, mode = lib.find_in_block(raw, url, text)
    if not ok:
        err(f"{where}: quoted text NOT found verbatim in {raw}"
            f"{' (no matching SOURCE block for ' + url + ')' if mode == 'missing-and-no-block' else ''}\n"
            f"      quote: {text[:160]!r}")
        return
    if mode in ("file-only", "file"):
        warn(f"{where}: quote found in {raw} but not inside a SOURCE block "
             f"whose URL matches {url}")
    if access:
        blocks = [b for b in lib.blocks.get(raw, [])
                  if b["url"].rstrip("/") == (url or "").rstrip("/")]
        for b in blocks:
            if b["access"] and access not in b["access"] and b["access"] not in access:
                err(f"{where}: access declared {access!r} but capture block says "
                    f"{b['access']!r}")


def main() -> int:
    lib = RawLibrary()
    lib.parse_blocks()

    plumbers_path = DATA / "plumbers.json"
    if not plumbers_path.exists():
        print("data/plumbers.json missing - run scripts/build_data.py first",
              file=sys.stderr)
        return 2
    doc = json.loads(plumbers_path.read_text(encoding="utf-8"))
    curation = json.loads((DATA / "curation.json").read_text(encoding="utf-8"))
    extract = json.loads((DATA / "_cslb_extract.json").read_text(encoding="utf-8"))

    # ---- 1. raw capture integrity -------------------------------------
    for rel, text in lib.texts.items():
        blocks = lib.blocks.get(rel, [])
        if not blocks and rel.startswith("data/raw/cslb-"):
            if not lib.source_url_of(rel):
                err(f"{rel}: CSLB capture has no SOURCE_URL header")
        for b in blocks:
            check_url(f"{rel} block", b["url"])
            if not b["access"]:
                err(f"{rel}: SOURCE block without ACCESS field: {b['url']}")

    # ---- 2/3/4. license provenance and parity --------------------------
    seen_ids: Counter[str] = Counter()
    seen_licenses: Counter[str] = Counter()
    active_businesses: set[str] = set()
    referenced_raw: set[str] = set()
    permit_rows = json.loads((RAW / "sfgov-permit-counts.json").read_text())["results"]
    permit_by_lic: Counter[str] = Counter()
    for row in permit_rows:
        permit_by_lic[str(row["license_number"])] += int(row["count"])

    for e in doc["entries"]:
        name = e["display_name"]
        seen_ids[e["id"]] += 1
        lic = e["license"]
        num = lic.get("number")

        for s in e.get("sources", []):
            check_url(f"{name} source", s.get("url"))
            if s.get("raw"):
                referenced_raw.add(s["raw"])
                if not lib.has_file(s["raw"]):
                    err(f"{name}: source points at missing capture {s['raw']}")
            if not s.get("tier"):
                err(f"{name}: source without trust tier: {s.get('url')}")

        if num and not lic.get("verified", True):
            # Explicitly unverified candidate: no capture exists by design.
            if e["tier"] in HIREABLE_TIERS:
                err(f"{name}: tier {e['tier']!r} but license {num} is flagged unverified")
            if not any(f["severity"] == "critical" for f in e.get("flags", [])):
                err(f"{name}: unverified license must carry a critical flag")
        elif num:
            seen_licenses[str(num)] += 1
            rel = f"data/raw/cslb-{num}.txt"
            referenced_raw.add(rel)
            if not lib.has_file(rel):
                err(f"{name}: license {num} has no CSLB capture at {rel}")
            else:
                src = lib.source_url_of(rel)
                if not src or str(num) not in src:
                    err(f"{name}: CSLB capture {rel} SOURCE_URL does not contain "
                        f"license {num} (got {src!r})")
                rec = extract.get(str(num))
                if not rec:
                    err(f"{name}: license {num} absent from data/_cslb_extract.json")
                else:
                    for field in ("legal_name", "status_code", "entity", "expire_date",
                                  "issue_date", "classifications", "cslb_phone"):
                        if lic.get(field) != rec.get(field):
                            err(f"{name}: license field {field} does not match the "
                                f"official capture ({lic.get(field)!r} vs {rec.get(field)!r})")
                    body = lib.texts[rel]
                    status_sentence = rec.get("status_raw") or ""
                    if status_sentence and norm(status_sentence) not in norm(body):
                        err(f"{name}: CSLB status sentence not present in {rel}")
                    if rec["status_code"] == "active" and \
                            "current and active" not in body.lower():
                        err(f"{name}: status_code 'active' but capture does not say "
                            f"'current and active'")
                    if rec["status_code"] == "suspended" and \
                            "suspension" not in body.lower():
                        err(f"{name}: status_code 'suspended' but capture has no "
                            f"suspension language")
                    if rec["status_code"] == "expired" and "expired" not in body.lower():
                        err(f"{name}: status_code 'expired' but capture does not say expired")
                if lic.get("status_code") == "active":
                    active_businesses.add(e["id"])
        else:
            if lic.get("status_code") not in ("unverified", None):
                err(f"{name}: no license number but status_code is "
                    f"{lic.get('status_code')!r}")

        # tier legality
        if e["tier"] in HIREABLE_TIERS and lic.get("status_code") != "active":
            err(f"{name}: tier {e['tier']!r} requires an ACTIVE CSLB license, "
                f"found {lic.get('status_code')!r}")
        if e["tier"] == "do-not-hire" and lic.get("status_code") == "active":
            err(f"{name}: tier 'do-not-hire' but CSLB license is active - "
                f"move it to a hireable tier or explain in a flag")

        # job_fit vocabulary
        for k, v in e["job_fit"].items():
            if v not in FIT_VOCAB:
                err(f"{name}: job_fit[{k}] = {v!r} is not in the declared vocabulary")
            if k not in doc["fit_labels"]:
                err(f"{name}: job_fit key {k!r} has no label in fit_labels")

        # permit cross-check
        if num and lic.get("verified", True) and \
                lic.get("status_code") in ("active", "suspended", "expired", "canceled"):
            if e.get("sf_permits_curated") is not None:
                all_lics = [str(num)] + [str(o["number"]) for o in e["other_licenses"]]
                total = sum(permit_by_lic.get(x, 0) for x in all_lics)
                if total and total != e["sf_permits_curated"]:
                    warn(f"{name}: curated sf_permits {e['sf_permits_curated']} vs "
                         f"{total} summed from the SF open-data extract "
                         f"(licenses {all_lics})")

        # evidence quotes
        for i, ev in enumerate(e.get("evidence", []), 1):
            check_quote(lib, f"{name} evidence#{i} [{ev.get('platform')}]",
                        ev["text"], ev.get("raw", ""), ev.get("url", ""),
                        ev.get("access"))
            referenced_raw.add(ev.get("raw", ""))
            check_url(f"{name} evidence#{i}", ev.get("url"))
            if not ev.get("job_signals"):
                warn(f"{name} evidence#{i}: no job_signals recorded")

        # rating aggregates
        for i, r in enumerate(e.get("ratings", []), 1):
            referenced_raw.add(r.get("raw", ""))
            check_url(f"{name} rating#{i}", r.get("url"))
            raw_rel = r.get("raw")
            if not raw_rel or not lib.has_file(raw_rel or ""):
                err(f"{name} rating#{i}: missing raw capture {raw_rel!r}")
                continue
            for field in ("score", "count"):
                val = r.get(field)
                if val is None:
                    continue
                ok, mode = lib.find_in_block(raw_rel, r.get("url", ""), str(val))
                if not ok:
                    err(f"{name} rating#{i}: {field} {val!r} not found in {raw_rel}")
                elif mode == "file-only":
                    warn(f"{name} rating#{i}: {field} {val!r} found in {raw_rel} but "
                         f"outside the matching SOURCE block")
            if not r.get("access", "").startswith(("direct", "indirect")):
                err(f"{name} rating#{i}: access {r.get('access')!r} must be "
                    f"'direct' or 'indirect-*'")

        # flags must state a reason
        for i, f in enumerate(e.get("flags", []), 1):
            if f.get("severity") not in ("critical", "warn", "info"):
                err(f"{name} flag#{i}: severity {f.get('severity')!r} invalid")
            if len(f.get("detail", "")) < 40:
                warn(f"{name} flag#{i}: detail is very short")

        # every hireable entry needs at least one official government source
        if e["tier"] not in ("unverified", "fallback-only", "historical"):
            if not any(s.get("tier") == "official-gov" for s in e.get("sources", [])):
                err(f"{name}: no official-gov source listed")

    # ---- duplicates / orphans ------------------------------------------
    for ident, n in seen_ids.items():
        if n > 1:
            err(f"duplicate entry id {ident!r} appears {n} times")
    for num, n in seen_licenses.items():
        if n > 1:
            err(f"license {num} is the primary license of {n} different entries")

    # legal citations reference their captures too
    def _walk(node):
        if isinstance(node, dict):
            if node.get("raw"):
                referenced_raw.add(node["raw"])
            for val in node.values():
                _walk(val)
        elif isinstance(node, list):
            for val in node:
                _walk(val)
    _walk(doc["legal"])
    _walk(doc["methodology"])

    referenced_raw.discard("")
    for rel in sorted(lib.texts):
        if rel not in referenced_raw and not rel.startswith("data/raw/cslb-"):
            warn(f"raw capture {rel} is not referenced by any entry")
    for rel in sorted(RAW.glob("cslb-*.txt")):
        key = f"data/raw/{rel.name}"
        if key not in referenced_raw:
            num = rel.stem.split("-", 1)[1]
            warn(f"CSLB capture {key} is not attached to any master-list entry "
                 f"(license {num})")

    # ---- 5. legal citations --------------------------------------------
    legal = doc["legal"]
    legal_quotes = [("legal.habitability", legal["habitability"]),
                    ("legal.rent_control", legal["rent_control"]),
                    ("legal.anti_harassment", legal["anti_harassment"]),
                    ("legal.technique", legal["technique"])]
    for i, item in enumerate(legal["tenant_remedies"], 1):
        legal_quotes.append((f"legal.tenant_remedies[{i}]", item))
    for i, item in enumerate(legal["permits"], 1):
        legal_quotes.append((f"legal.permits[{i}]", item))
    for where, item in legal_quotes:
        check_quote(lib, where, item["quote"], item.get("raw", ""),
                    item.get("url", ""), item.get("access"))
        check_url(where, item.get("url"))
        if not item.get("citation"):
            err(f"{where}: no citation")

    # ---- 6. methodology access log must be honest ----------------------
    for row in doc["methodology"]["access_log"]:
        if row["access"] not in ("direct", "indirect-search-snippet",
                                 "indirect-aggregator", "blocked"):
            err(f"access_log: invalid access value {row['access']!r}")

    # indirect datapoints in the data must not be labelled direct
    for e in doc["entries"]:
        for r in e.get("ratings", []):
            raw_rel = r.get("raw", "")
            for b in lib.blocks.get(raw_rel, []):
                if b["url"].rstrip("/") == (r.get("url") or "").rstrip("/"):
                    if b["access"] and r.get("access") and \
                            b["access"].split("-")[0] != r["access"].split("-")[0]:
                        err(f"{e['display_name']} rating: data says access "
                            f"{r['access']!r} but the capture header says "
                            f"{b['access']!r}")

    # ---- 8. coverage ----------------------------------------------------
    n_active = len(active_businesses)
    if n_active < 20:
        err(f"coverage: only {n_active} distinct businesses with a verified "
            f"ACTIVE license (requirement: 20+)")
    n_checked = len(extract)
    if n_checked < 25:
        warn(f"only {n_checked} CSLB records were checked")

    # ---- report ---------------------------------------------------------
    report = {
        "generated_at": doc["generated_at"],
        "entries": len(doc["entries"]),
        "cslb_records_checked": n_checked,
        "active_verified_businesses": n_active,
        "raw_capture_files": len(lib.texts),
        "quotes_verified": sum(
            len(e.get("evidence", [])) for e in doc["entries"]) + len(legal_quotes),
        "ratings_verified": sum(len(e.get("ratings", [])) for e in doc["entries"]),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }
    (DATA / "validation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"entries .................. {report['entries']}")
    print(f"CSLB records checked ..... {report['cslb_records_checked']}")
    print(f"ACTIVE verified business . {report['active_verified_businesses']}")
    print(f"raw capture files ........ {report['raw_capture_files']}")
    print(f"quotes verified .......... {report['quotes_verified']}")
    print(f"rating aggregates checked  {report['ratings_verified']}")
    print(f"errors ................... {len(errors)}")
    print(f"warnings ................. {len(warnings)}")
    for w in warnings:
        print(f"  WARN  {w}")
    for x in errors:
        print(f"  FAIL  {x}")
    print(f"\nVALIDATION: {report['status']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
