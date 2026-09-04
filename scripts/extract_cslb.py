#!/usr/bin/env python3
"""Parse every data/raw/cslb-*.txt capture into a normalized dict.

The captures are verbatim text of the CSLB 'Contractor's License Detail' page
with a small provenance header. This script is the ONLY place license facts are
derived, so data/plumbers.json can be checked against them mechanically.
"""
from __future__ import annotations
import json, re, pathlib, sys

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "_cslb_extract.json"

STATUS_MAP = [
    ("current and active", "active"),
    ("under suspension", "suspended"),
    ("revoked", "revoked"),
    ("inactive", "inactive"),
    ("is expired", "expired"),
    ("was canceled", "canceled"),
    ("canceled", "canceled"),
]


def field(text: str, label: str) -> str | None:
    m = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def parse(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    num = path.stem.split("-", 1)[1]
    lines = [l for l in text.splitlines() if l.strip()]
    header = {l.split(":", 1)[0]: l.split(":", 1)[1].strip()
              for l in lines[:6] if ":" in l and not l.startswith("NOTE")}

    status_raw = field(text, "License Status") or ""
    code = "unknown"
    for needle, c in STATUS_MAP:
        if needle in status_raw:
            code = c
            break

    body = re.search(
        r"Contractor's License Detail for License #\s*\d+\s*\n(.+?)\n(?=Business Phone Number:)",
        text, re.S)
    legal_name = None
    addr_lines: list[str] = []
    if body:
        chunk = [l.strip() for l in body.group(1).splitlines() if l.strip()]
        legal_name = chunk[0] if chunk else None
        addr_lines = chunk[1:]

    wc_raw = field(text, "Workers' Compensation") or ""
    if re.search(r"\bexempt\b", wc_raw, re.I):
        wc = "exempt"
    elif re.search(r"Policy Number|employee service group|insurance", wc_raw, re.I):
        wc = "insured"
    else:
        wc = "unspecified"

    bond_raw = field(text, "Contractor's Bond") or ""
    _amt = re.search(r"Bond Amount:\s*([$][\d,]+)", bond_raw)
    bond = {
        "carrier": (bond_raw.split(",")[0].strip() if bond_raw else None),
        "amount": (_amt.group(1).rstrip(",") if _amt else None),
        "effective": (re.search(r"Effective Date:\s*(\d{2}/\d{2}/\d{4})", bond_raw).group(1)
                      if re.search(r"Effective Date:\s*(\d{2}/\d{2}/\d{4})", bond_raw) else None),
        "cancellation": (re.search(r"Cancellation Date:\s*(\d{2}/\d{2}/\d{4})", bond_raw).group(1)
                         if re.search(r"Cancellation Date:\s*(\d{2}/\d{2}/\d{4})", bond_raw) else None),
    }

    return {
        "license_number": num,
        "legal_name": legal_name,
        "cslb_address": " / ".join(addr_lines),
        "cslb_phone": field(text, "Business Phone Number"),
        "entity": field(text, "Entity"),
        "issue_date": field(text, "Issue Date"),
        "reissue_date": field(text, "Reissue Date"),
        "expire_date": field(text, "Expire Date"),
        "status_raw": status_raw,
        "status_code": code,
        "classifications": field(text, "Classifications"),
        "bond": bond,
        "workers_comp_code": wc,
        "workers_comp_raw": wc_raw,
        "misc": field(text, "Miscellaneous Information"),
        "source_url": header.get("SOURCE_URL"),
        "captured_at": header.get("CAPTURED_AT"),
        "raw_file": f"data/raw/{path.name}",
    }


def main() -> int:
    out = {}
    for p in sorted(RAW.glob("cslb-*.txt"), key=lambda x: int(x.stem.split("-")[1])):
        rec = parse(p)
        out[rec["license_number"]] = rec
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for n, r in sorted(out.items(), key=lambda kv: int(kv[0])):
        print(f"{n:>8}  {r['status_code']:<9} {r['entity'] or '?':<14} "
              f"exp {r['expire_date'] or '?':<10} wc {r['workers_comp_code']:<9} "
              f"{(r['legal_name'] or '?')[:44]}")
    print(f"\n{len(out)} CSLB captures parsed -> {OUT.relative_to(OUT.parents[1])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
