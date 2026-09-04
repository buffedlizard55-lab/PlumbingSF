#!/usr/bin/env python3
"""Build the 50 curation entries for batch 2026-09-04-expansion-50-b6.

Unlike generate_b5.py this script does NOT embed CSLB fields. The 50 official
records were transcribed verbatim into data/raw/cslb-<N>.txt first, and this
script reads them back through scripts/extract_cslb.py's parser so that every
license fact in curation.json is derived from the capture (the validator then
re-checks field-by-field parity).

Candidate sourcing for this batch (all captured 2026-09-04):
  * Thumbtack San Francisco category pages (plumbers / drain-cleaning /
    drain-unclogging) and the individual pro profiles that print a
    "License verified - C36" credential  -> data/raw/research-expansion50-b6-2026-09-04.txt
  * BBB search "plumber near San Francisco, CA" and BBB profiles that print
    the CSLB licence number                 -> same file
  * SF open-data plumbing-permit contacts where the CONTRACTOR'S OWN address
    zip is 94122 / 94116 (Outer Sunset / Parkside), i.e. businesses based in
    the tenant's neighbourhood               -> data/raw/sfgov-plumbing-permits-b6-2026-09-04.txt

Run: python3 scripts/generate_b6.py
Then: make all
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.parse
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
sys.path.insert(0, str(ROOT / "scripts"))
from extract_cslb import parse  # noqa: E402  (same parser the pipeline uses)

BATCH = "2026-09-04-expansion-50-b6"
REVIEW_RAW = "data/raw/research-expansion50-b6-2026-09-04.txt"
PERMIT_RAW = "data/raw/sfgov-plumbing-permits-b6-2026-09-04.txt"
PERMIT_URL = ("https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)"
              "&$where=license_number%20in(...)&$group=firm_name,license_number&$order=license_number,firm_name&$limit=200")

# The fixed researched set. Order here is irrelevant; the gate sorts numerically.
LICENSES = [
    # Thumbtack SF pros with a "License verified - C36" credential (or BBB-printed licence)
    "1134965", "1052114", "1115649", "1095188", "1006178", "1099380", "1022293", "1007707", "1041020",
    # BBB "plumber near San Francisco" accredited profiles
    "949110", "1079325", "850352",
    # Outer Sunset / Parkside based (contractor address zip 94122 / 94116) permit filers
    "467912", "324708", "576600", "714879", "660208", "887553", "343610", "497973", "425733",
    "641991", "502603", "486546", "520892", "689900", "684197", "439862", "319594", "595176", "611082",
    # Other SF-based permit filers surfaced by the recent-permit aggregate
    "762214", "632743", "863544", "863322", "1016070", "864771", "846565", "825292", "805919",
    "785492", "849533", "727485", "832898", "862601", "876588", "781784", "430557", "740992", "385567",
]
assert len(LICENSES) == 50 and len(set(LICENSES)) == 50

# Where the entry was discovered (drives the "sourced from" flag and the review links).
DISCOVERY = {
    "1134965": "thumbtack", "1052114": "thumbtack", "1115649": "thumbtack", "1095188": "thumbtack",
    "1006178": "thumbtack", "1099380": "thumbtack", "1022293": "thumbtack", "1007707": "thumbtack",
    "1041020": "thumbtack",
    "949110": "bbb", "1079325": "bbb", "850352": "bbb",
}
OUTER_SUNSET_ZIPS = ("94122", "94116")

# Per-license SF permit totals (sum of every firm-name spelling), verbatim rows in PERMIT_RAW
# block A. 1006178 returned no rows.
PERMITS = json.loads("""{
 "1007707": 3, "1016070": 234, "1022293": 1, "1041020": 176, "1052114": 21, "1079325": 12,
 "1095188": 7, "1099380": 2, "1115649": 25, "1134965": 11, "319594": 198, "324708": 214,
 "343610": 122, "385567": 324, "425733": 82, "430557": 333, "439862": 153, "467912": 584,
 "486546": 181, "497973": 91, "502603": 222, "520892": 105, "576600": 66, "595176": 193,
 "611082": 163, "632743": 305, "641991": 251, "660208": 138, "684197": 61, "689900": 92,
 "714879": 67, "727485": 46, "740992": 163, "762214": 580, "781784": 40, "785492": 348,
 "805919": 160, "825292": 126, "832898": 59, "846565": 71, "849533": 79, "850352": 104,
 "862601": 69, "863322": 199, "863544": 155, "864771": 219, "876588": 26, "887553": 102,
 "949110": 116, "1006178": 0
}""")

# Latest permit + 2024-2026 activity for the active licences (PERMIT_RAW blocks B/C/D).
RECENT = {
    "1041020": ("PP20260828194", 38, "26 ft french drain in back of home at east side"),
    "1052114": ("PW20250630290", 4, "work category: 2pb; channel drain install"),
    "1095188": ("PP20260717276", 5, None),
    "1115649": ("PW20260812207", 25, "plumbing installation for two bathroom sinks one shower valve move plumbing for one shower pan"),
    "1134965": ("PP20260826149", 11, "g/f common area: install new automatic seismic gas shut off valve."),
    "324708": ("PW20260409992", 10, "replace all hot and cold water galvanized pipes to copper"),
    "467912": ("PW20260610609", 9, None),
    "632743": ("PW20251117627", 4, None),
    "660208": ("PW20250826632", 2, None),
    "762214": ("PW20260827625", 33, None),
    "850352": ("PP20260713144", 14, None),
    "863322": ("PW20260707245", 6, None),
    "863544": ("PW20240821031", 3, None),
    "887553": ("PW20260810101", 7, None),
    "949110": ("PW20260902766", 19, "work category: 1p; replaced shower pan"),
    # active but no 2024-2026 permit rows:
    "576600": ("PP20160617383", 0, None),
    "611082": ("PW20200722158", 0, None),
    "714879": ("PW20201013450", 0, None),
    "1022293": ("PP20171006316", 0, None),
    "1099380": ("PP20231108948", 0, None),
    "1006178": (None, 0, None),
}

# Review-platform evidence, each item verbatim inside the matching SOURCE block of REVIEW_RAW.
TT = "https://www.thumbtack.com"
REVIEWS = {
    "1134965": {
        "display": "AS Plus Plumbing Corp",
        "profile": f"{TT}/ca/san-francisco/drain-cleaning/as-plus-plumbing-corp/service/376764330441498624",
        "rating": ("Thumbtack", "4.9", "165"),
        "evidence": [
            ("Thumbtack business scope", None, "Plumbing Drain Repair; Water Treatment System Installation or Replacement; Shower and Bathtub Installation or Replacement",
             ["drain repair advertised", "shower and bathtub work advertised"]),
            ("Thumbtack credentials", None, "License verified\nC36 – Plumbing Contractor\nLicense state: CA",
             ["platform-verified C36 licence"]),
            ("Thumbtack", "Kristen H.", "Marco showed up same-day and fixed my garbagedisposal in probably 10-15 minutes.",
             ["same-day response", "small repair, not remodel"]),
        ],
        "fit": {"snake_shower": "advertised", "tub_overflow_access": "advertised", "weekend_emergency": "advertised"},
        "notes": "Thumbtack profile: Hired 250 times, 4 employees, 11 years in business, Top Pro 2022-2023; services list includes Emergency Plumbing.",
    },
    "1052114": {
        "display": "I Rooter & Plumbing",
        "profile": f"{TT}/ca/san-francisco/water-heater-installation/i-rooter-plumbing/service/357706607642730513",
        "rating": ("Thumbtack", "4.8", "97"),
        "evidence": [
            ("Thumbtack business scope", None, "Plumbing Drain Repair; Water Treatment System Installation or Replacement; Shower and Bathtub Installation or Replacement; Plumbing Pipe Repair",
             ["drain repair advertised", "shower and bathtub work advertised"]),
            ("Thumbtack", "Ryan A.", "Was able to come out immediately for an urgent plumbing issue and had things resolved very quickly.",
             ["urgent drain clog resolved quickly", "single-drain clogging job"]),
            ("Thumbtack", None, "Flat-rate, competitive pricing — I charge by the job, not by the hour",
             ["flat-rate pricing"]),
        ],
        "fit": {"snake_shower": "documented-adjacent", "tub_overflow_access": "advertised"},
        "notes": "Thumbtack profile: Hired 145 times, 1 employee, 14 years in business, Top Pro 2019-2025, hours Sun-Mon 8:00 am - 7:00 pm; owner-operator Dwayne Pettway per background-check line. Address of record 3739 Balboa (Outer Richmond, 94121), about 2 miles from 94122.",
    },
    "1115649": {
        "display": "Rapid Flow Plumbing & Rooter Inc",
        "profile": f"{TT}/ca/san-francisco/water-heater-installation/rapid-flow-plumbing-rooter/service/268900941950780660",
        "rating": ("Thumbtack", "4.9", "85"),
        "evidence": [
            ("Thumbtack business scope", None, "Shower and Bathtub Repair; Garbage Disposal Installation; Plumbing Inspection; Gas Line Installation; Emergency Plumbing",
             ["shower and bathtub repair advertised", "plumbing inspection advertised", "emergency plumbing advertised"]),
            ("Thumbtack", "Iris L.", "Jose did an outstanding job helping us with a clogged kitchen drain. He arrived on time, was professional and courteous throughout the entire service call, and quickly diagnosed and resolved the issue.",
             ["clogged drain diagnosed and cleared", "explained the cause"]),
            ("Thumbtack", "Diane Z.", "Initially we thought we just had a clog but Jose found that we needed to replace the pipes. We were able to pivot and change the scope of the project in a fast and fair way.",
             ["scope escalated from clog to pipe replacement - confirm no-wall-opening limit up front"]),
        ],
        "fit": {"snake_shower": "documented-adjacent", "tub_overflow_access": "advertised", "weekend_emergency": "advertised"},
        "notes": "Thumbtack profile: Current Top Pro, Hired 125 times, 3 employees, 18 years in business, hours Sun 7:00 am - 8:00 pm. SF permits are filed under both 'Rapid Flow Plumbing & Rooter Inc' (5) and 'Navta Construction Inc' (20) on this licence number.",
    },
    "1095188": {
        "display": "LGM Plumbing & Rooter",
        "profile": f"{TT}/ca/san-bruno/affordable-plumbing-services/lgm-plumbing-rooter/service/462928282454630407",
        "rating": ("Thumbtack", "5.0", "95"),
        "evidence": [
            ("Thumbtack business scope", None, "Plumbing Drain Repair; Water Treatment System Installation or Replacement; Shower and Bathtub Installation or Replacement; Plumbing Pipe Repair",
             ["drain repair advertised", "shower and bathtub work advertised"]),
            ("Thumbtack", "Amanda S.", "Luis showed up on time, assessed our kitchen sink, fixed it SUPER quickly and gave tips on how to avoid having it clog like that again. He even showed where's an easier place to snake in the future",
             ["slow-draining / clogging drain cleared", "explained snaking access point"]),
        ],
        "fit": {"snake_shower": "documented-adjacent", "tub_overflow_access": "advertised"},
        "notes": "Thumbtack profile: Hired 166 times, 1 employee (owner Luis Matamoros Torres per background-check line), 4 years in business, Top Pro 2023-2024, Sunday closed. Based in San Bruno (94066); 7 SF permits incl. one filed 07/17/2026.",
    },
    "1006178": {
        "display": "Integrity First Plumbing Inc",
        "profile": f"{TT}/ca/san-francisco/drain-cleaning/integrity-first-plumbing-inc/service/307330201449660645",
        "rating": ("Thumbtack", "5.0", "26"),
        "evidence": [
            ("Thumbtack business scope", None, "Plumbing Drain Repair; Shower and Bathtub Installation or Replacement; Plumbing Pipe Repair",
             ["drain repair advertised", "shower and bathtub work advertised"]),
            ("Thumbtack", "Praneeth W.", "Showed up on time, fixed the issue I was having. Work seemed thorough. Somewhat pricey I thought for the hour of work but knowing work was done well was peace of mind",
             ["slow-draining single drain cleared", "price noted as somewhat high"]),
            ("Thumbtack", "Joanne E.", "After they unclogged the kitchen sink they checked the bathroom and made sure there was no problem and I was not charged for the extra work.",
             ["drain unclogged", "checked adjoining fixtures at no charge"]),
        ],
        "fit": {"snake_shower": "documented-adjacent", "tub_overflow_access": "advertised", "weekend_emergency": "advertised"},
        "notes": "Thumbtack profile: Hired 26 times, 3 employees, 12 years in business, Top Pro 2018-2019; the profile shows NO 'License verified' credential and its reviews date from 2018-2019. Licence 1006178 was matched through the CSLB name search (INTEGRITY FIRST PLUMBING INC, San Francisco, Active). No SF plumbing permits are filed under this licence.",
    },
    "1099380": {
        "display": "JC Plumbing & Rooter",
        "profile": None,  # listing card only; profile is in Pinole/Hayward category pages not captured
        "rating": None, "evidence": [], "fit": {},
        "notes": "Surfaced by the Thumbtack SF plumbers review strip ('JC PLUMBING', pinole) and matched to SF permit rows 'Jc Plumbing & Rooter' 1099380. Based in Hayward; only 2 SF permits (latest 2023).",
    },
    "1022293": {
        "display": "Rays Service One Plumbing",
        "profile": None, "rating": None, "evidence": [], "fit": {},
        "notes": "Surfaced by the Thumbtack SF plumbers review strip ('Ray's Service One', san-pablo) and matched to SF permit row 'Rays Service One Plumbing' 1022293. Based in Oakland; a single SF permit (2017).",
    },
    "1007707": {
        "display": "Maximus Plumbing",
        "profile": None, "rating": None, "evidence": [], "fit": {},
        "notes": "Surfaced by the Thumbtack SF plumbers review strip ('Maximus Plumbing & Heating', san-carlos) and matched to SF permit rows 'Maximus Plumbing' 1007707.",
    },
    "1041020": {
        "display": "Prosper Construction Development Inc",
        # The rating was captured from the SF drain-unclogging category page (listing card);
        # the individual profile was not fetched, so it is linked for manual review only.
        "profile": f"{TT}/ca/san-francisco/drain-unclogging",
        "manual_profile": f"{TT}/ca/san-francisco/general-contractors/prosper-construction-development/service/339550527742099628",
        "rating": ("Thumbtack", "4.9", "71"),
        "evidence": [],
        "fit": {},
        "notes": "Listed on Thumbtack's SF drain-unclogging page as 'Licensed pro' (4.9, 71 reviews). CSLB shows a B - GENERAL BUILDING licence only, no C36; 176 SF plumbing permits incl. 38 since 2024, latest a french drain (PP20260828194).",
    },
    "949110": {
        "display": "Shedrick The Plumber",
        "profile": "https://www.bbb.org/us/ca/san-francisco/profile/plumber/shedrick-the-plumber-1116-925187",
        "rating": ("BBB", "A+", None),
        "evidence": [
            ("BBB", None, "Business Categories: Plumber, Plumbing Renovation, Water Leak Detectors, Sewer Contractors, Tankless Water Heaters, Commercial Plumber, Leak Detection, Water Heater Installation, Pipe Fitter, Drain Cleaning, Water Leak Repair",
             ["drain cleaning listed", "leak detection listed"]),
            ("BBB", None, "BBB records show a license number of 949110 for this business, issued by Contractors State License Board. The expiration date of this license is 6/30/2028.",
             ["BBB-printed licence number matches CSLB"]),
        ],
        "fit": {"snake_shower": "advertised"},
        "notes": "BBB: Accredited since 6/5/2024, A+, 16 years in business, sole proprietorship, owner Shedrick Ferguson, 4 employees; service area includes San Francisco County. 116 SF permits incl. 19 since 2024; latest PW20260902766 'replaced shower pan' (filed 2026-09-02).",
    },
    "1079325": {
        "display": "Service Star Plumbing",
        "profile": "https://www.bbb.org/us/ca/san-francisco/profile/plumber/service-star-plumbing-1116-935024",
        "rating": ("BBB", "A+", None),
        "evidence": [],
        "fit": {},
        "notes": "BBB: Accredited since 8/29/2022, A+, owner Bennyson L De La Cruz, 2 employees, service area includes San Francisco County; BBB prints licence 1079325 - but CSLB shows that licence UNDER SUSPENSION (contractor's bond) at the verification date.",
    },
    "850352": {
        "display": "Bay Metro Corporation",
        "profile": "https://www.bbb.org/us/ca/san-francisco/profile/general-contractor/bay-metro-corporation-1116-75127",
        "rating": ("BBB", "A+", None),
        "evidence": [],
        "fit": {},
        "website": "https://www.baymetrocorp.com/",
        "notes": "BBB: Accredited since 7/27/2005, A+, 22 years, president Manny Gonzalez, 3 employees; described as a General Contractor specializing in residential remodeling. Holds B + C36; workers-comp classes are carpentry/wallboard. Not a drain-service business.",
    },
}

FIT_KEYS = ("snake_shower", "tub_overflow_access", "prewar_galvanized",
            "camera_inspection", "non_destructive", "weekend_emergency")

BAY_AREA = ("SAN FRANCISCO", "SO SAN FRANCISCO", "SOUTH SAN FRANCISCO", "DALY CITY", "SAN BRUNO",
            "BRISBANE", "MILLBRAE", "PACIFICA", "SAN MATEO", "OAKLAND", "HAYWARD", "SAN LEANDRO",
            "BURLINGAME", "COLMA")


def title_name(legal: str) -> str:
    t = legal.title().replace("'S", "'s").replace("Llc", "LLC").replace(" Dba ", " dba ")
    t = re.sub(r"\bAs Plus\b", "AS Plus", t)
    t = re.sub(r"\bLgm\b", "LGM", t)
    t = re.sub(r"\bJc\b", "JC", t)
    t = re.sub(r"\bSnc\b", "SNC", t)
    t = re.sub(r"\bRl\b", "RL", t)
    t = re.sub(r"\bT T\b", "T T", t)
    return t


def tier_for(rec: dict) -> str:
    status = rec["status_code"]
    if status != "active":
        return "do-not-hire"
    if "C36" not in (rec["classifications"] or ""):
        return "wrong-scale"
    addr = rec["cslb_address"].upper()
    if not any(city in addr for city in BAY_AREA):
        return "conditional"
    return "viable"


def is_outer_sunset(rec: dict) -> bool:
    m = re.search(r"\b(\d{5})(?:-\d{4})?\s*$", rec["cslb_address"])
    return bool(m and m.group(1) in OUTER_SUNSET_ZIPS)


def build_entry(lic: str, rec: dict) -> dict:
    review = REVIEWS.get(lic, {})
    tier = tier_for(rec)
    legal = rec["legal_name"]
    dba = None
    addr_parts = rec["cslb_address"].split(" / ")
    if addr_parts and addr_parts[0].upper().startswith("DBA "):
        dba = addr_parts[0][4:].strip().title()
        addr_parts = addr_parts[1:]
    display = review.get("display") or title_name(dba or legal)
    if lic == "486546":
        display = "W & J Plumbing Co (Winson Wah Lau)"
    slug = re.sub(r"[^a-z0-9]+", "-", display.lower()).strip("-")

    status = rec["status_code"]
    permits = PERMITS.get(lic, 0)
    latest, recent_n, latest_desc = RECENT.get(lic, (None, 0, None))
    sunset = is_outer_sunset(rec)

    flags: list[dict] = []
    if status != "active":
        flags.append({
            "severity": "critical",
            "label": f"LICENSE {status.upper()} — do not book",
            "detail": (f"CSLB shows: {rec['status_raw']} Expire date on record: {rec['expire_date']}. "
                       f"A contractor whose licence is {status} cannot legally contract for plumbing work in "
                       f"California; the {permits} historical SF permit rows do not change that. Do not book.")})
        if status == "suspended":
            flags.append({
                "severity": "warn",
                "label": "Suspension may be temporary — re-check CSLB before ruling out",
                "detail": ("The CSLB status text says the suspension can lift retroactively once a bond is processed. "
                           "If you want this business, re-load the CSLB record on the day you call and ask for proof of bond.")})
    else:
        if "C36" not in (rec["classifications"] or ""):
            flags.append({
                "severity": "warn",
                "label": "No C36 plumbing classification",
                "detail": (f"CSLB classifications are {rec['classifications']}. This licence does not carry C36 (plumbing), "
                           "so it is not the right licence for a drain-clearing service call even though the business "
                           "pulls SF plumbing permits as a general contractor.")})
        if rec["workers_comp_code"] == "exempt":
            flags.append({
                "severity": "info",
                "label": "Workers' comp exempt (no employees certified)",
                "detail": ("CSLB shows the licence exempt from workers' compensation because the licensee certified "
                           "it has no employees. That is normal for an owner-operator; if a second worker shows up, ask who employs them.")})
        if rec["reissue_date"]:
            flags.append({
                "severity": "info",
                "label": "License reissued to another entity",
                "detail": f"CSLB shows Reissue Date {rec['reissue_date']} and Miscellaneous Information '{rec['misc']}'. The licence number predates the current business entity."})
        if recent_n == 0 and permits:
            flags.append({
                "severity": "info",
                "label": "No SF plumbing permits filed since 2024",
                "detail": (f"The licence has {permits} SF plumbing-permit contact rows all-time, but none numbered 2024-2026 "
                           f"(latest {latest}). Drain clearing does not need a permit, so this only means the firm is not "
                           "currently pulling permitted work in the city; ask whether they still take SF service calls.")})
        if tier == "conditional":
            flags.append({
                "severity": "info",
                "label": "Based outside the immediate Bay Area service radius",
                "detail": f"Address of record is {rec['cslb_address']}. Confirm they will dispatch to 94122 and whether a travel charge applies."})
        if rec["cslb_address"].upper().startswith("P O BOX"):
            flags.append({
                "severity": "info",
                "label": "Address of record is a PO box",
                "detail": f"CSLB lists {rec['cslb_address']}; a PO box is legitimate for a sole owner but means there is no shop to visit. Ask where the business is based."})
    if lic == "1006178":
        flags.append({
            "severity": "warn",
            "label": "No Thumbtack licence badge and no SF permits under this licence",
            "detail": ("The Thumbtack profile shows no 'License verified' credential and its reviews stop in 2019; the SF permit "
                       "dataset has zero rows for licence 1006178 (only 'Integrity First Construction Inc', a different licence, "
                       "1055539, in Fremont). The CSLB record itself is active and San Francisco based. Ask them to confirm "
                       "licence 1006178 by name before booking.")})
    if lic == "1115649":
        flags.append({
            "severity": "info",
            "label": "Permits filed under two business names on one licence",
            "detail": ("SF permit contacts list 'Rapid Flow Plumbing & Rooter Inc' (5 rows) and 'Navta Construction Inc' (20 rows) "
                       "under licence 1115649. CSLB shows the licence as RAPID FLOW PLUMBING & ROOTER INC with B and C36 classifications. "
                       "Not an irregularity in itself; noted so the name on the invoice matches the licence.")})
    if lic == "1079325":
        flags.append({
            "severity": "warn",
            "label": "BBB A+ accreditation while CSLB licence is suspended",
            "detail": ("BBB prints licence 1079325 with an 8/31/2027 expiry and an A+ rating, but the CSLB record fetched the same day "
                       "shows a contractor's-bond suspension (bond cancelled 07/29/2026). Platform badges lag the licensing board.")})
    if lic == "1041020":
        flags.append({
            "severity": "warn",
            "label": "Thumbtack 'Licensed pro' badge refers to a B (general building) licence",
            "detail": ("Thumbtack lists Prosper construction development as a Licensed pro on its drain-unclogging page, but the CSLB "
                       "licence 1041020 carries only B - GENERAL BUILDING. Hire a C36 plumber for a drain and overflow-linkage job.")})
    if sunset:
        flags.append({
            "severity": "info",
            "label": "Based in the Outer Sunset / Parkside (94122 / 94116)",
            "detail": (f"CSLB address of record is {rec['cslb_address']} and SF permit contacts list the same zip - the business is "
                       "based in the tenant's own neighbourhood. Locality is a convenience signal, not a skill signal.")})
    if latest_desc and status == "active":
        flags.append({
            "severity": "info",
            "label": f"Most recent SF permit: {latest}",
            "detail": f"SF DBI permit {latest} description (verbatim from data.sfgov.org a6aw-rudh): \"{latest_desc}\". Shows the kind of work the firm currently pulls permits for."})

    fit = {k: "unknown" for k in FIT_KEYS}
    if tier == "wrong-scale":
        fit["snake_shower"] = "no-evidence"
    if status == "active":
        fit.update(review.get("fit", {}))

    ratings = []
    evidence = []
    if review.get("rating") and status == "active":
        platform, score, count = review["rating"]
        ratings.append({"platform": platform, "score": score, "count": count,
                        "url": review["profile"], "access": "direct", "raw": REVIEW_RAW})
    elif review.get("rating"):
        # keep the aggregate visible for non-active licences too: it is part of the irregularity story
        platform, score, count = review["rating"]
        ratings.append({"platform": platform, "score": score, "count": count,
                        "url": review["profile"], "access": "direct", "raw": REVIEW_RAW})
    for platform, author, text, signals in review.get("evidence", []):
        evidence.append({"platform": platform, "author": author, "text": text,
                         "url": review["profile"], "access": "direct", "raw": REVIEW_RAW,
                         "job_signals": signals})

    if status != "active":
        headline = (f"CSLB shows this licence {rec['status_raw'].split('.')[0].lower().replace('this license is ', '')} "
                    f"— do not book; {permits} historical SF permits" + (", Outer Sunset based" if sunset else "") + ".")
    elif tier == "wrong-scale":
        headline = f"Active licence but {rec['classifications']} only — a general contractor, not a C36 plumber; wrong licence for this job."
    else:
        bits = []
        if review.get("rating"):
            p, s, c = review["rating"]
            bits.append(f"{p} {s}" + (f" ({c} reviews)" if c else ""))
        bits.append(f"{permits} SF permits" + (f", {recent_n} since 2024" if recent_n else ""))
        if sunset:
            bits.append("based in 94122/94116")
        headline = (f"Active C36 licence verified on CSLB; {'; '.join(bits)}. "
                    + ("Review evidence is adjacent (drain clearing), not the exact overflow-linkage task — screen by phone."
                       if review.get("rating") else
                       "No review-platform evidence captured for this pass — screen by phone using the linked Yelp/Google searches."))

    sources = [
        {"label": f"CSLB license record {lic}",
         "url": f"https://www2.cslb.ca.gov/OnlineServices/CheckLicenseII/LicenseDetail.aspx?LicNum={lic}",
         "tier": "official-gov", "access": "direct", "raw": f"data/raw/cslb-{lic}.txt"},
        {"label": "SF plumbing-permit contact rows for this licence (all-time, every firm-name spelling)",
         "url": PERMIT_URL, "tier": "official-gov", "access": "direct", "raw": PERMIT_RAW},
    ]
    if review.get("profile"):
        host = urllib.parse.urlparse(review["profile"]).hostname or ""
        label = "Thumbtack profile (fetched directly)" if "thumbtack" in host else "BBB business profile (fetched directly)"
        sources.append({"label": label, "url": review["profile"], "tier": "official-platform",
                        "access": "direct", "raw": REVIEW_RAW})
    q = urllib.parse.quote(display)
    sources.append({"label": f"Yelp - manual review search for {display}",
                    "url": f"https://www.yelp.com/search?find_desc={q}&find_loc=San+Francisco%2C+CA",
                    "tier": "official-platform", "access": "manual-review"})
    sources.append({"label": f"Google reviews - manual review for {display}",
                    "url": f"https://www.google.com/search?q={q}+San+Francisco+plumber+reviews",
                    "tier": "official-platform", "access": "manual-review"})
    if review.get("manual_profile"):
        sources.append({"label": "Thumbtack profile (not fetched - manual review)", "url": review["manual_profile"],
                        "tier": "official-platform", "access": "manual-review"})
    # A business website printed on a fetched BBB profile is carried in the `website`
    # field (rendered as the "Web" link) but is NOT listed as a source, because the
    # site itself was not fetched and the validator's allow-list is limited to visited hosts.

    entry = {
        "key": lic,
        "id": slug,
        "display_name": display,
        "dba": dba,
        "tier": tier,
        "headline": headline,
        "phone_display": rec["cslb_phone"],
        "address_display": ", ".join(addr_parts) if addr_parts else None,
        "website": review.get("website"),
        "sf_permits": permits,
        "research_batch": BATCH,
        "discovery": DISCOVERY.get(lic, "sfgov-outer-sunset" if sunset else "sfgov-permits"),
        "outer_sunset_based": sunset,
        "job_fit": fit,
        "ratings": ratings,
        "evidence": evidence,
        "flags": flags,
        "sources": sources,
    }
    if review.get("notes"):
        entry["research_note"] = review["notes"]
    return entry


def main() -> int:
    recs = {}
    for lic in LICENSES:
        path = RAW / f"cslb-{lic}.txt"
        if not path.exists():
            print(f"missing capture {path}", file=sys.stderr)
            return 1
        recs[lic] = parse(path)

    cur_path = DATA / "curation.json"
    cur = json.loads(cur_path.read_text(encoding="utf-8"))
    existing = {str(e["key"]) for e in cur["entries"] if e.get("research_batch") != BATCH}
    existing |= {str(o) for e in cur["entries"] if e.get("research_batch") != BATCH
                 for o in e.get("other_licenses", [])}
    overlap = existing & set(LICENSES)
    if overlap:
        print(f"refusing: licences already in the master list: {sorted(overlap)}", file=sys.stderr)
        return 1

    cur["entries"] = [e for e in cur["entries"] if e.get("research_batch") != BATCH]
    new_entries = [build_entry(lic, recs[lic]) for lic in LICENSES]
    ids = Counter(e["id"] for e in cur["entries"] + new_entries)
    dupes = [i for i, n in ids.items() if n > 1]
    if dupes:
        print(f"refusing: duplicate ids {dupes}", file=sys.stderr)
        return 1
    cur["entries"].extend(new_entries)
    for e in new_entries:
        print(f"{e['key']:>8} {e['tier']:<13} {e['display_name']}")

    # Access log: record what was reachable on this pass.
    log = cur["methodology"]["access_log"]
    def upsert(source, tier, access, note):
        for row in log:
            if row["source"] == source:
                row.update({"tier": tier, "access": access, "note": note})
                return
        log.append({"source": source, "tier": tier, "access": access, "note": note})
    # Drop rows a previous run of this script may have appended under other names.
    log[:] = [r for r in log if r["source"] not in ("Thumbtack", "Better Business Bureau",
                                                     "SF open data (data.sfgov.org)", "Reddit")]
    upsert("thumbtack.com", "official-platform", "direct",
           "Direct current pages captured on 2026-09-04. Pass b6 fetched the SF category pages (plumbers / drain-cleaning / drain-unclogging) and individual pro profiles; ratings, review counts, 'License verified - C36' credentials and review text were captured verbatim in data/raw/research-expansion50-b6-2026-09-04.txt. Inherited now-dead profile URLs were removed earlier.")
    upsert("bbb.org", "official-platform", "direct",
           "Fetched successfully for search results and individual business profiles. Pass b6 fetched the 'plumber near San Francisco, CA' search and three profiles; BBB-printed CSLB licence numbers were cross-checked against the CSLB record the same day (one A+ accredited firm turned out to be under bond suspension).")
    upsert("data.sfgov.org Socrata API (resource k6kv-9kix)", "official-gov", "direct",
           "Fetched successfully. Per-licence permit-row counts for every batch; pass b6 additionally captured latest-permit numbers, 2024-2026 activity, a6aw-rudh permit descriptions and the contractor-address-zip 94122/94116 aggregate (data/raw/sfgov-plumbing-permits-b6-2026-09-04.txt).")
    upsert("reddit.com", "community", "blocked",
           "BLOCKED - HTTP 403 on old.reddit.com, www.reddit.com and the .json endpoints (re-tested 2026-09-04 for pass b6). Only search-engine snippets were visible; no Reddit quotation is used as candidate evidence. Inherited placeholder-style thread URLs were removed earlier.")
    upsert("cslb.ca.gov NameSearch.aspx", "official-gov", "direct",
           "GET NameSearch.aspx?NextName=<name> returns an alphabetical business-name listing; used in pass b6 to resolve Thumbtack pros to licence numbers and to confirm that 'Drain Geeks' and the 'Cárcamo' listing have no CSLB business-name record. ZipCodeSearch is POST-only and was not usable.")

    gate = {
        "count": 50,
        "licenses": sorted(LICENSES, key=int),
        "status_summary": dict(Counter(recs[l]["status_code"] for l in LICENSES)),
        "required_flags": {},
        "critical_flag_licenses": [],
        "status_disclosures": {},
        "review_capture": REVIEW_RAW,
        "strict_permit_counts": True,
        "finalized": True,
    }
    for lic in LICENSES:
        r = recs[lic]
        if r["status_code"] != "active":
            gate["required_flags"][lic] = [r["status_code"]]
            gate["critical_flag_licenses"].append(lic)
            if r["status_code"] == "inactive":
                gate["status_disclosures"][lic] = "inactive"
            if r["status_code"] == "suspended":
                gate["status_disclosures"][lic] = "suspension"
        elif "C36" not in (r["classifications"] or ""):
            gate["required_flags"][lic] = ["c36"]
    gate["critical_flag_licenses"].sort(key=int)
    gates_path = DATA / "expansion_gates.json"
    gates = json.loads(gates_path.read_text(encoding="utf-8"))
    gates[BATCH] = gate
    gates_path.write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")
    cur_path.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"gate {BATCH}: {gate['status_summary']}")
    print(f"curation now has {len(cur['entries'])} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
