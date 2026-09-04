#!/usr/bin/env python3
"""Merge the official CSLB captures with the curated analysis layer.

Inputs
------
data/_cslb_extract.json   produced by scripts/extract_cslb.py from verbatim
                          captures of the CSLB "Contractor's License Detail"
                          page. This is the ONLY source of license facts.
data/curation.json        the analytical layer: tiers, job-fit assessment,
                          review evidence pointers, flags, legal citations.
data/raw/sfgov-permit-counts.json
                          SF open-data plumbing permit counts per firm/license.

Outputs
-------
data/plumbers.json        the master list consumed by the site builder.
data/master_list.csv      the same list, flat, for download / spreadsheets.

Nothing in this script invents a fact. Every license field is copied from a
parsed official capture; scripts/validate.py then re-reads that capture and
fails the build if the copy does not match byte for byte.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

TIER_ORDER = {
    "recommended": 0,
    "viable": 1,
    "conditional": 2,
    "fallback-only": 3,
    "wrong-scale": 4,
    "unverified": 5,
    "do-not-hire": 6,
    "historical": 7,
}

FIT_ORDER = {
    "documented": 4,
    "documented-adjacent": 3,
    "advertised": 2,
    "unknown": 1,
    "no-evidence": 0,
    "no": 0,
}

# The two capabilities that the tenant said are non-negotiable.
CORE_FIT_KEYS = ("snake_shower", "tub_overflow_access", "non_destructive")

FIT_LABELS = {
    "snake_shower": "Snake / clear the shower drain",
    "tub_overflow_access": "Tub overflow trip-lever access",
    "prewar_galvanized": "Pre-war galvanized drain piping",
    "camera_inspection": "Drain camera inspection",
    "non_destructive": "Non-destructive (no wall opening)",
    "weekend_emergency": "Weekend / emergency response",
}


def load_permit_counts() -> dict[str, int]:
    """Return {license_number: permit_count} from the SF open-data extract."""
    path = DATA / "raw" / "sfgov-permit-counts.json"
    if not path.exists():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("results") or rows.get("rows") or []
    out: dict[str, int] = {}
    for row in rows:
        lic = str(row.get("license_number") or "").strip()
        if not lic:
            continue
        try:
            count = int(row.get("permit_count") or row.get("count") or 0)
        except (TypeError, ValueError):
            count = 0
        out[lic] = out.get(lic, 0) + count
    return out


def fit_score(job_fit: dict[str, str]) -> dict[str, object]:
    """Score an entry against the tenant's hard requirements."""
    parts = {k: FIT_ORDER.get(job_fit.get(k, "unknown"), 1) for k in CORE_FIT_KEYS}
    total = sum(parts.values())
    max_total = 4 * len(CORE_FIT_KEYS)
    pct = round(100 * total / max_total) if max_total else 0
    return {
        "components": parts,
        "total": total,
        "max": max_total,
        "percent": pct,
        "band": "high" if pct >= 75 else "medium" if pct >= 45 else "low",
    }


def build_entry(curated: dict, cslb: dict, permits: dict[str, int]) -> dict:
    key = curated["key"]
    lic_num = key if key.isdigit() else None

    license_block: dict[str, object]
    if lic_num and lic_num in cslb:
        rec = cslb[lic_num]
        license_block = {
            "number": rec["license_number"],
            "legal_name": rec["legal_name"],
            "status_raw": rec["status_raw"],
            "status_code": rec["status_code"],
            "entity": rec["entity"],
            "classifications": rec["classifications"],
            "issue_date": rec["issue_date"],
            "reissue_date": rec["reissue_date"],
            "expire_date": rec["expire_date"],
            "bond": rec["bond"],
            "workers_comp_code": rec["workers_comp_code"],
            "workers_comp_raw": rec["workers_comp_raw"],
            "cslb_address": rec["cslb_address"],
            "cslb_phone": rec["cslb_phone"],
            "misc": rec["misc"],
            "source_url": rec["source_url"],
            "captured_at": rec["captured_at"],
            "raw_file": rec["raw_file"],
            "verified": True,
        }
    else:
        # Unverified candidate: carry forward the explicitly declared status.
        declared = curated.get("license", {}) or {}
        license_block = {
            "number": declared.get("number"),
            "legal_name": None,
            "status_raw": declared.get("note") or "No CSLB license record captured.",
            "status_code": declared.get("status_code", "unverified"),
            "entity": None,
            "classifications": None,
            "issue_date": None,
            "reissue_date": None,
            "expire_date": None,
            "bond": None,
            "workers_comp_code": None,
            "workers_comp_raw": None,
            "cslb_address": None,
            "cslb_phone": None,
            "misc": None,
            "source_url": None,
            "captured_at": None,
            "raw_file": None,
            "verified": False,
            "note": declared.get("note"),
        }

    # Permit counts: sum the primary license and any sibling licenses.
    # The SF open-data extract is authoritative; the curated figure is kept
    # alongside so scripts/validate.py can detect drift between the two.
    all_lics = [lic_num] if lic_num else []
    all_lics += [str(x) for x in curated.get("other_licenses", []) if str(x).isdigit()]
    permit_total = sum(permits.get(x, 0) for x in all_lics if x)
    permit_curated = curated.get("sf_permits")
    if not permit_total:
        permit_total = permit_curated if permit_curated else None

    other = []
    for n in curated.get("other_licenses", []):
        n = str(n)
        rec = cslb.get(n)
        other.append({
            "number": n,
            "legal_name": rec["legal_name"] if rec else None,
            "status_code": rec["status_code"] if rec else "unverified",
            "expire_date": rec["expire_date"] if rec else None,
            "entity": rec["entity"] if rec else None,
            "raw_file": rec["raw_file"] if rec else None,
            "sf_permits": permits.get(n, 0),
        })

    entry = {
        "id": curated["id"],
        "display_name": curated["display_name"],
        "dba": curated.get("dba"),
        "tier": curated["tier"],
        "headline": curated["headline"],
        "phone_display": curated.get("phone_display"),
        "address_display": curated.get("address_display"),
        "website": curated.get("website"),
        "license": license_block,
        "other_licenses": other,
        "sf_permits": permit_total,
        "sf_permits_curated": permit_curated,
        "job_fit": curated.get("job_fit", {}),
        "fit_score": fit_score(curated.get("job_fit", {})),
        "ratings": curated.get("ratings", []),
        "evidence": curated.get("evidence", []),
        "flags": curated.get("flags", []),
        "sources": curated.get("sources", []),
    }
    return entry


def main() -> int:
    curated = json.loads((DATA / "curation.json").read_text(encoding="utf-8"))
    cslb_path = DATA / "_cslb_extract.json"
    if not cslb_path.exists():
        print("data/_cslb_extract.json missing - run scripts/extract_cslb.py first",
              file=sys.stderr)
        return 1
    cslb = json.loads(cslb_path.read_text(encoding="utf-8"))
    permits = load_permit_counts()

    entries = [build_entry(e, cslb, permits) for e in curated["entries"]]

    # Deterministic ordering: tier first, then job fit, then SF permit depth.
    entries.sort(key=lambda e: (
        TIER_ORDER.get(e["tier"], 99),
        -e["fit_score"]["percent"],
        -(e["sf_permits"] or 0),
        e["display_name"],
    ))
    for i, e in enumerate(entries, start=1):
        e["rank"] = i

    active = [e for e in entries if e["license"]["status_code"] == "active"]

    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verified_at": curated["methodology"]["verified_at"],
        "job": curated["job"],
        "legal": curated["legal"],
        "methodology": curated["methodology"],
        "counts": {
            "entries": len(entries),
            "active_verified_businesses": len(active),
            "cslb_records_captured": len(cslb),
            "raw_capture_files": len([p for p in (DATA / "raw").iterdir()
                                      if p.suffix in (".txt", ".json")]),
            "flagged_not_hireable": len(entries) - len(active),
        },
        "fit_labels": FIT_LABELS,
        "entries": entries,
    }
    (DATA / "plumbers.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Flat CSV mirror of the master list.
    csv_path = DATA / "master_list.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "rank", "business_name", "legal_name_on_license", "tier", "fit_percent",
            "cslb_license", "license_status", "entity", "classifications",
            "issue_date", "expire_date", "bond_carrier", "bond_amount",
            "bond_cancellation", "workers_comp", "cslb_address", "cslb_phone",
            "published_phone", "sf_plumbing_permits", "website",
            "snake_shower", "tub_overflow_access", "non_destructive",
            "prewar_galvanized", "camera_inspection", "weekend_emergency",
            "flag_count", "critical_flags", "cslb_source_url", "raw_capture",
        ])
        for e in entries:
            lic = e["license"]
            bond = lic.get("bond") or {}
            jf = e["job_fit"]
            w.writerow([
                e["rank"], e["display_name"], lic.get("legal_name"), e["tier"],
                e["fit_score"]["percent"], lic.get("number"), lic.get("status_code"),
                lic.get("entity"), lic.get("classifications"), lic.get("issue_date"),
                lic.get("expire_date"), bond.get("carrier"), bond.get("amount"),
                bond.get("cancellation"), lic.get("workers_comp_code"),
                lic.get("cslb_address"), lic.get("cslb_phone"), e.get("phone_display"),
                e.get("sf_permits"), e.get("website"),
                jf.get("snake_shower"), jf.get("tub_overflow_access"),
                jf.get("non_destructive"), jf.get("prewar_galvanized"),
                jf.get("camera_inspection"), jf.get("weekend_emergency"),
                len(e["flags"]),
                "; ".join(f["label"] for f in e["flags"] if f["severity"] == "critical"),
                lic.get("source_url") or "", lic.get("raw_file") or "",
            ])

    print(f"data/plumbers.json  {len(entries)} entries, "
          f"{len(active)} with an ACTIVE CSLB license")
    print(f"data/master_list.csv  {csv_path.stat().st_size:,} bytes")
    for e in entries:
        print(f"  {e['rank']:>2}. [{e['tier']:<13}] {e['display_name'][:44]:<44} "
              f"{str(e['license'].get('number') or '-'):<12} "
              f"{e['license']['status_code']:<9} fit {e['fit_score']['percent']:>3}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
