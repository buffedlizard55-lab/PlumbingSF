#!/usr/bin/env python3
"""One-shot generator for the 2026-09-04-expansion-50-b4 research batch.

Builds the 50 curation entries for the licenses captured this session
(data/raw/cslb-<n>.txt) and registers the fixed expansion gate in
data/expansion_gates.json. License facts are NOT typed here: build_data.py
copies them from data/_cslb_extract.json, which validate.py re-checks against
the verbatim captures. Only analytical decisions (tier, flags, headline,
permit cross-references) live in this table.

Re-runnable: replaces any existing entries whose key matches, and overwrites
the batch gate.
"""
from __future__ import annotations

import json
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BATCH = "2026-09-04-expansion-50-b4"

TOPT = "data/raw/sfgov-plumbing-aggregates-top300-2026-09-04.txt"
TOPT_URL = ("https://data.sfgov.org/resource/k6kv-9kix.json"
            "?$select=firm_name,license_number,count(*)&$group=firm_name,license_number"
            "&$order=count(*)%20DESC&$limit=300")
B4 = "data/raw/sfgov-plumbing-permit-counts-batch4-2026-09-04.txt"
B4_URLS = {
    "723992": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27838680%27,%27837694%27,%27723992%27)",
    "837694": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27838680%27,%27837694%27,%27723992%27)",
    "838680": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27838680%27,%27837694%27,%27723992%27)",
    "532819": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27532819%27,%271003603%27,%27664620%27)",
    "1003603": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27532819%27,%271003603%27,%27664620%27)",
    "664620": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27532819%27,%271003603%27,%27664620%27)",
    "868068": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27868068%27,%27923951%27,%27979693%27)",
    "923951": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27868068%27,%27923951%27,%27979693%27)",
    "979693": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$where=license_number%20in(%27868068%27,%27923951%27,%27979693%27)",
}

# SF permit counts (all-time contact rows, summed across firm-name spellings).
# top-300 aggregate for 41 licenses; per-license API query for the 9 below it.
PERMITS = {
    "823991": 1148, "765155": 1098, "556995": 1063, "498866": 1419, "751295": 1019,
    "767866": 650, "269424": 425, "427328": 395, "533324": 391, "744542": 347,
    "712728": 325, "101436": 321, "763612": 320, "970605": 319, "812845": 318,
    "636742": 317, "765695": 316, "628627": 314, "489648": 314, "933593": 314,
    "1039082": 312, "685266": 310, "698559": 299, "570753": 297, "673116": 296,
    "860119": 294, "493818": 294, "998725": 290, "339522": 288, "680961": 286,
    "961915": 285, "745896": 285, "366870": 283, "1031709": 282, "430548": 280,
    "591329": 4835, "374573": 3033, "1026214": 465, "931237": 406, "987398": 1763,
    "1066584": 326,
    # below the top-300 cutoff, captured by per-license query (batch4 file)
    "723992": 526, "837694": 272, "838680": 318, "1003603": 262, "664620": 262,
    "532819": 267, "979693": 254, "868068": 271, "923951": 256,
}

# (key, id, display_name, tier, headline, sf_permits, flags, permit_source)
# flags: list of (severity, label, detail)
ROWS = [
    # ---------------- ACTIVE - viable (in/near San Francisco) ----------------
    ("970605", "all-rooter-plumbing-service-inc", "All Rooter & Plumbing Service Inc",
     "viable",
     "Active CSLB C36 license (issued 03/06/2012), Corporation at 238 Ocean Avenue, San Francisco. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     319, [], "top300"),
    ("636742", "dengs-plumbing-inc", "Deng's Plumbing Inc",
     "viable",
     "Active CSLB C36 license, Corporation at 206 Geneburn Way, San Francisco. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     317,
     [("info", "License reissued to another entity",
       "CSLB Miscellaneous Information reads 04/26/2004 - LICENSE REISSUED TO ANOTHER ENTITY.")],
     "top300"),
    ("765695", "daniel-larratt-plumbing-inc", "Daniel Larratt Plumbing Inc",
     "viable",
     "Active CSLB C36 license, Corporation at 944 Terminal Way, San Carlos (peninsula). Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     316,
     [("info", "License reissued to another entity",
       "CSLB Miscellaneous Information reads 08/28/2000 - LICENSE REISSUED TO ANOTHER ENTITY."),
      ("info", "Based in San Carlos",
       "Address of record is 944 Terminal Way, San Carlos, CA 94070 - mid-peninsula, a common base for contractors serving San Francisco.")],
     "top300"),
    ("489648", "kiwi-plumbing-inc", "Kiwi Plumbing Inc",
     "viable",
     "Active CSLB C36 license, Corporation at 71 B Liberty Ship Way, Sausalito. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     314,
     [("info", "License reissued to another entity",
       "CSLB Miscellaneous Information reads 05/11/2009 - LICENSE REISSUED TO ANOTHER ENTITY."),
      ("info", "Based in Sausalito (Marin County)",
       "Address of record is 71 B Liberty Ship Way, Sausalito, CA 94965.")],
     "top300"),
    ("1039082", "cj-plumbing-inc", "CJ Plumbing Inc",
     "viable",
     "Active CSLB C16 + C36 license, Corporation at 1510 Eucalyptus Dr, San Francisco. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     312,
     [("warn", "Workers' comp class code is unusual for a plumber",
       "CSLB records the policy's classification code as 0005 - Nurseries-propagation/cultivation, which is not a plumbing trade class. Worth a question before booking; it may indicate a data-entry issue on the insurance filing.")],
     "top300"),
    ("685266", "a-a-plumbing", "A & A Plumbing",
     "viable",
     "Active CSLB C36 license, Sole Ownership at 47 Granada Avenue, San Francisco; CSLB-certified no employees (WC exempt). Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     310,
     [("info", "CSLB-certified no employees",
       "Workers' compensation reads exempt: 'they certified that they have no employees at this time.'")],
     "top300"),
    ("860119", "hillside-plumbing-company-inc", "Hillside Plumbing Company Inc",
     "viable",
     "Active CSLB C36 license, Corporation at P O Box 7032, San Mateo (peninsula). Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     294,
     [("info", "Based in San Mateo (peninsula)",
       "Address of record is P O Box 7032, San Mateo, CA 94403.")],
     "top300"),
    ("998725", "jm-pacific-bay-plumbing-inc", "J M Pacific Bay Plumbing Inc",
     "viable",
     "Active CSLB C36 license, Corporation at 1555 Yosemite Avenue Suite 17, San Francisco. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     290, [], "top300"),
    ("961915", "precise-plumbing", "Precise Plumbing",
     "viable",
     "Active CSLB C36 license, Sole Ownership at 1279 139th Ave, San Leandro (East Bay); CSLB-certified no employees (WC exempt). Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     285,
     [("info", "CSLB-certified no employees",
       "Workers' compensation reads exempt: 'they certified that they have no employees at this time.'"),
      ("info", "Based in San Leandro (East Bay)",
       "Address of record is 1279 139th Ave, San Leandro, CA 94578.")],
     "top300"),
    ("366870", "prontito-plumbing", "Prontito Plumbing",
     "viable",
     "Active CSLB C36 license, Sole Ownership at 48 Ocean Avenue, San Francisco; CSLB-certified no employees (WC exempt). Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     283,
     [("info", "CSLB-certified no employees",
       "Workers' compensation reads exempt: 'they certified that they have no employees at this time.'")],
     "top300"),
    ("1031709", "north-star-plumbing-fire-protection-inc", "North Star Plumbing & Fire Protection Inc",
     "viable",
     "Active CSLB C36 + C16 license, Corporation at 1485 Bayshore Blvd MB 111, San Francisco. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     282, [], "top300"),
    ("430548", "steven-harris-glorit-plumbing-contractor", "Steven Harris Glorit Plumbing Contractor",
     "viable",
     "Active CSLB C36 license, Sole Ownership at 220 Cypress Ave #247, South San Francisco. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     280, [], "top300"),
    ("723992", "joe-watterson-plumbing", "Joe Watterson Plumbing",
     "viable",
     "Active CSLB C36 license, Sole Ownership at 3653 Folsom Street, San Francisco; CSLB-certified no employees (WC exempt). Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     526,
     [("info", "CSLB-certified no employees",
       "Workers' compensation reads exempt: 'they certified that they have no employees at this time.'"),
      ("info", "SF permit records also list 'Slemish Plumbing' under this license",
       "The per-license permit query returns 'Joe Watterson Plumbing' (257 rows) and 'Slemish Plumbing' (269 rows) under license 723992 - 526 rows total.")],
     "batch4"),
    ("556995", "renstrom-plumbing-heating-inc", "Renstrom Plumbing & Heating Inc",
     "viable",
     "Active CSLB C20 + C36 license, Corporation at 600 Amador Suite 1, San Francisco. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     1063,
     [("info", "License reissued to another entity",
       "CSLB Miscellaneous Information reads 03/03/1997 - LICENSE REISSUED TO ANOTHER ENTITY.")],
     "top300"),
    ("498866", "oconnor-plumbing-fire-protection-inc", "O'Connor Plumbing & Fire Protection Inc",
     "viable",
     "Active CSLB C16 + C36 license, Corporation at 360 Swift Ave, South San Francisco. Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     1419,
     [("info", "Reissued 04/02/2026 after an earlier per-request cancellation",
       "CSLB Miscellaneous Information reads 08/18/2000 - LICENSE CANCELLED PER REQUEST and 04/02/2026 - LICENSE REISSUED TO ANOTHER ENTITY."),
      ("warn", "SF permit records attribute 'Emerald Plumbing & Fire' rows to this license",
       "The permit aggregate lists 979 'O'connor Plumbing & Fire Protection' rows plus 440 'Emerald Plumbing & Fire' rows under license 498866. Emerald is the separate, canceled license 767866; the shared rows suggest a same-family or data-entry relationship. Confirm which entity would actually do the work.")],
     "top300"),
    ("751295", "a-plumbing", "A Plumbing",
     "viable",
     "Active CSLB C36 license, Sole Ownership at 136 Alpha St, San Francisco; CSLB-certified no employees (WC exempt). Verified against the official record; no review-platform evidence was captured for this pass, so screen by phone.",
     1019,
     [("info", "CSLB-certified no employees",
       "Workers' compensation reads exempt: 'they certified that they have no employees at this time.'"),
      ("info", "SF permit records split the firm under two spellings",
       "The permit aggregate lists 'A Plumbing' (290 rows) and 'A Plumbing**Seenote**' (729 rows) under license 751295 - 1,019 rows total.")],
     "top300"),

    # ---------------- ACTIVE - conditional ----------------
    ("765155", "ars-american-residential-services-of-california-inc",
     "ARS American Residential Services of California Inc",
     "conditional",
     "Active CSLB C36 + C42 license for the Rescue Rooter national entity, a Tennessee corporation (Memphis, TN 38120). Verified against the official record; national franchise operation, so confirm the local dispatch and technician before booking.",
     1098,
     [("warn", "Out-of-state national corporate entity",
       "Address of record is 965 Ridge Lake Blvd Ste 201, Memphis, TN 38120 - a national home-services corporation, not a San Francisco firm. Work would be performed by a local branch or franchise."),
      ("warn", "Workers' compensation certificate waiting to be processed",
       "CSLB Miscellaneous Information reads 10/01/2026 - WC CERT WAITING TO BE PROCESSED, and the on-file WC policy expires 10/01/2026. Re-verify WC coverage if you proceed.")],
     "top300"),
    ("427328", "backflow-prevention-specialists-inc", "Backflow Prevention Specialists Inc",
     "conditional",
     "Active CSLB C36 + B + C20 + C16 + C43 license, Corporation at 1131 Elko Drive, Sunnyvale. Verified against the official record; a five-classification specialist, not a dedicated drain-service shop.",
     395,
     [("warn", "Backflow-testing specialist based in Sunnyvale",
       "The name and five classifications (C36, B, C20, C16, C43) describe a backflow/cross-connection and fire-protection contractor in Sunnyvale (South Bay), not a San Francisco drain-clearing service. Relevant mainly if the job exposes a backflow-assembly need.")],
     "top300"),
    ("745896", "ajax-plumbing", "Ajax Plumbing",
     "conditional",
     "Active CSLB C-4 + C16 + C36 license, Partnership at 1105 Berkshire Dr, El Dorado Hills. Verified against the official record; the address is far outside San Francisco.",
     285,
     [("warn", "Based in El Dorado Hills (Sacramento metro)",
       "Address of record is 1105 Berkshire Dr, El Dorado Hills, CA 95762 - roughly two hours from San Francisco. A clean license but unlikely to serve a San Francisco drain call.")],
     "top300"),
    ("374573", "water-heaters-only-inc", "Water Heaters Only Inc",
     "conditional",
     "Active CSLB C36 license, Corporation at 970 E Main Street 200, Grass Valley. Verified against the official record; a water-heater brand, not a drain-service shop.",
     3033,
     [("warn", "Water-heater-specific brand",
       "The firm name is 'Water Heaters Only Inc'. No drain-clearing evidence was captured; the 3,033 SF permit rows are consistent with water-heater replacement work."),
      ("warn", "Based in Grass Valley (far out-of-area)",
       "Address of record is 970 E Main Street 200, Grass Valley, CA 95945.")],
     "top300"),
    ("1026214", "harris-water-heaters-inc", "Harris Water Heaters Inc",
     "conditional",
     "Active CSLB C36 license, Corporation at 6270 Crow Canyon Rd, Castro Valley. Verified against the official record; a water-heater brand, not a drain-service shop.",
     465,
     [("warn", "Water-heater-specific brand",
       "The firm name is 'Harris Water Heaters Inc'. No drain-clearing evidence was captured."),
      ("info", "License reissued to another entity",
       "CSLB Miscellaneous Information reads 11/08/2018 - LICENSE REISSUED TO ANOTHER ENTITY.")],
     "top300"),
    ("987398", "fast-home-services-llc", "Fast Home Services LLC",
     "conditional",
     "Active CSLB C36 + C10 + C20 license, Limited Liability company at 16120 Redmond-Woodinville Rd NE Ste 15, Woodinville, WA. Verified against the official record; a Washington-state water-heater services operator.",
     1763,
     [("warn", "Out-of-state corporate entity (Woodinville, WA)",
       "Address of record is 16120 Redmond-Woodinville Rd NE Ste 15, Woodinville, WA 98072."),
      ("warn", "SF permit records name a different legal entity for this license",
       "The permit aggregate lists 'F W H Acquisition Co Llc Dba Fast Water' (1,763 rows) under license 987398, while CSLB's legal name is 'Fast Home Services LLC'. Same water-heater brand family, but the entities differ - confirm the contracting entity before booking.")],
     "top300"),
    ("1066584", "castleworks-home-services-company", "Castleworks Home Services Company",
     "conditional",
     "Active CSLB C36 license, Corporation at 28358 Constellation Rd Ste 698, Valencia (Southern California). Verified against the official record; out of area for San Francisco.",
     326,
     [("warn", "Based in Valencia (Southern California)",
       "Address of record is 28358 Constellation Rd Ste 698, Valencia, CA 91355."),
      ("warn", "SF permit records name a different legal entity for this license",
       "The permit aggregate lists 'Awhap Acquisition Corp Dba Affordable Wa...' (326 rows) under license 1066584, while CSLB's legal name is 'Castleworks Home Services Company'. A water-heater acquisition roll-up; confirm the contracting entity before booking.")],
     "top300"),
    ("838680", "real-plumbing-and-heating-inc", "Real Plumbing and Heating Inc",
     "conditional",
     "Active CSLB C20 + C36 license, Corporation at P O Box 1922, Clearlake Oaks (Lake County). Verified against the official record; far out of area for San Francisco.",
     318,
     [("warn", "Based in Clearlake Oaks (Lake County)",
       "Address of record is P O Box 1922, Clearlake Oaks, CA 95423 - well north of the Bay Area."),
      ("info", "License reissued to another entity",
       "CSLB Miscellaneous Information reads 08/31/2004 - LICENSE REISSUED TO ANOTHER ENTITY.")],
     "batch4"),
    ("532819", "wills-plumbing", "Wills Plumbing",
     "conditional",
     "Active CSLB C36 license, Sole Ownership at 1811 West Euclid Avenue, Stockton. Verified against the official record; out of area for San Francisco.",
     267,
     [("warn", "Based in Stockton (out of area)",
       "Address of record is 1811 West Euclid Avenue, Stockton, CA 95204.")],
     "batch4"),

    # ---------------- ACTIVE - wrong scale (no C36) ----------------
    ("533324", "ct-construction", "CT Construction",
     "wrong-scale",
     "Active CSLB license, but General Building (B) only - no C36 plumbing classification. A clean license that cannot lawfully perform this plumbing job.",
     391,
     [("warn", "No C36 - General Building (B) classification only",
       "CSLB shows CT Construction holds only the B (General Building) classification. Plumbing work requires the C36 classification, so this firm cannot legally pull the plumbing permit or perform this drain repair. Included to explain the permit-table row, not as a candidate.")],
     "top300"),

    # ---------------- REVOKED ----------------
    ("823991", "bell-plumbing-north-inc", "Bell Plumbing North Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license was revoked after expiration and there is Complaint Disclosure information on file.",
     1148,
     [("critical", "LICENSE REVOKED - do not book",
       "CSLB: 'This license is revoked and not able to contract at this time. The license was revoked after expiration. There is Complaint Disclosure information for this license.' (expire date 09/30/2015; bond canceled 10/17/2015). The business cannot legally contract.")],
     "top300"),
    ("591329", "just-water-heaters-inc", "Just Water Heaters Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license was revoked after expiration, with Complaint Disclosure information, and the corporation was dissolved 02/13/2012.",
     4835,
     [("critical", "LICENSE REVOKED - do not book",
       "CSLB: 'This license is revoked and not able to contract at this time. The license was revoked after expiration. There is Complaint Disclosure information for this license.' Miscellaneous Information reads 02/13/2012 - SECRETARY OF STATE - DISSOLUTION. The business cannot legally contract.")],
     "top300"),

    # ---------------- SUSPENDED ----------------
    ("979693", "mc-plumbing", "M C Plumbing",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is under suspension for failure to comply with an outstanding civil judgment.",
     254,
     [("critical", "LICENSE SUSPENDED - do not book",
       "CSLB: 'License is under suspension for the following reasons: License is suspended for failure to comply with an outstanding civil judgment.' The business cannot legally contract while the suspension stands.")],
     "batch4"),

    # ---------------- INACTIVE ----------------
    ("269424", "de-jager-reilly-plumbing-heating-inc", "De Jager & Reilly Plumbing & Heating Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is inactive and not able to contract at this time.",
     425,
     [("critical", "LICENSE INACTIVE - do not book",
       "CSLB: 'This license is inactive and not able to contract at this time.' (expire date 12/31/2027). The business cannot legally contract until the license is reactivated.")],
     "top300"),
    ("933593", "alansis-rooter-plumbing", "Alansi's Rooter & Plumbing",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is inactive and will need to meet workers' compensation requirements to reactivate.",
     314,
     [("critical", "LICENSE INACTIVE - do not book",
       "CSLB: 'This license is inactive and not able to contract at this time. The license will need to meet the workers compensation requirements to renew active or reactivate.' The business cannot legally contract.")],
     "top300"),
    ("923951", "alliance-plumbing-company", "Alliance Plumbing Company",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is inactive; it needs a contractors bond and workers' compensation to reactivate, and the WC exemption was canceled 10/16/2023.",
     256,
     [("critical", "LICENSE INACTIVE - do not book",
       "CSLB: 'This license is inactive and not able to contract at this time. The license will need a contractors bond to renew active or reactivate. The license will need to meet the workers compensation requirements to renew active or reactivate.' Miscellaneous Information reads 10/16/2023 - WC EXEMPT CANCELLED-LIC INACTIVATED. The business cannot legally contract.")],
     "batch4"),

    # ---------------- CANCELED ----------------
    ("767866", "emerald-plumbing-fire-protection-inc", "Emerald Plumbing & Fire Protection Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license was canceled 08/31/2013 per request.",
     650,
     [("critical", "LICENSE CANCELED - do not book",
       "CSLB: 'This license is canceled and not able to contract.' Miscellaneous Information reads 08/31/2013 - LICENSE CANCELED PER REQUEST. The business cannot legally contract.")],
     "top300"),
    ("101436", "western-plumbing-heating-co-inc", "Western Plumbing & Heating Co Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license was canceled 08/07/2014 per request.",
     321,
     [("critical", "LICENSE CANCELED - do not book",
       "CSLB: 'This license is canceled and not able to contract.' Miscellaneous Information reads 08/07/2014 - LICENSE CANCELED PER REQUEST (expire date 08/07/2014). The business cannot legally contract.")],
     "top300"),
    ("628627", "chung-hing-plumbing-corp", "Chung Hing Plumbing Corp",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license was canceled 09/15/2006 per request.",
     314,
     [("critical", "LICENSE CANCELED - do not book",
       "CSLB: 'This license is canceled and not able to contract.' Miscellaneous Information reads 09/15/2006 - LICENSE CANCELLED PER REQUEST (expire date 09/30/2006). The business cannot legally contract.")],
     "top300"),
    ("339522", "cheer-plumbing-co", "Cheer Plumbing Co",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license was canceled on the death of the contractor.",
     288,
     [("critical", "LICENSE CANCELED ON DEATH OF CONTRACTOR - do not book",
       "CSLB: 'This license was canceled on the death of the contractor.' (expire date 07/28/2016). The business cannot legally contract.")],
     "top300"),
    ("837694", "goodrich-plumbing-inc", "Goodrich Plumbing Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license was canceled 02/11/2025 per request and the corporation was dissolved 02/11/2025.",
     272,
     [("critical", "LICENSE CANCELED - do not book",
       "CSLB: 'This license is canceled and not able to contract.' Miscellaneous Information reads 02/11/2025 - LICENSE CANCELED PER REQUEST and 02/11/2025 - SECRETARY OF STATE - DISSOLUTION. The business cannot legally contract.")],
     "batch4"),

    # ---------------- EXPIRED ----------------
    ("712728", "heath-plumbing-fire-protection", "Heath Plumbing & Fire Protection",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired and not able to contract at this time (expire 09/30/2001).",
     325,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time.' (expire date 09/30/2001). The business cannot legally contract.")],
     "top300"),
    ("763612", "hot-water-inc", "Hot Water Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired, was canceled after expiration, and the corporation was dissolved 10/06/2017.",
     320,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time. The license was canceled after expiration.' Miscellaneous Information reads 10/06/2017 - LIC CANCELED AFTER EXPIRATION DATE and 10/06/2017 - SECRETARY OF STATE - DISSOLUTION. The business cannot legally contract.")],
     "top300"),
    ("812845", "br-troika-inc", "B R Troika Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired (expire 09/30/2018). SF permit records list the brand as 'Br Troika Inc. Dba Mr Rooter Plumbing'.",
     318,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time.' (expire date 09/30/2018). SF permit records list the operating brand as 'Br Troika Inc. Dba Mr Rooter Plumbing' (318 rows). The business cannot legally contract under this license.")],
     "top300"),
    ("698559", "deehan-plumbing", "Deehan Plumbing",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired and will need a contractors bond to reactivate (expire 11/30/2024).",
     299,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time. The license will need a contractors bond to renew active or reactivate.' (expire date 11/30/2024). The business cannot legally contract.")],
     "top300"),
    ("570753", "rickys-plumbing-company", "Ricky's Plumbing Company",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired and was canceled after expiration (canceled per request 09/16/2005).",
     297,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time. The license was canceled after expiration.' Miscellaneous Information reads 09/16/2005 - LICENSE CANCELLED PER REQUEST (expire date 06/30/2005). The business cannot legally contract.")],
     "top300"),
    ("673116", "ajax-plumbing-and-heating", "Ajax Plumbing and Heating",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired and not able to contract at this time (expire 06/30/2005).",
     296,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time.' (expire date 06/30/2005). The business cannot legally contract.")],
     "top300"),
    ("493818", "rodney-conklin-plumbing-heating", "Rodney Conklin Plumbing & Heating",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired (expire 06/30/2014). SF permit records list 'Purcell Bros Plumb & Heat' under this license.",
     294,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time.' (expire date 06/30/2014). SF permit records list the firm as 'Purcell Bros Plumb & Heat' (294 rows) under this license. The business cannot legally contract.")],
     "top300"),
    ("680961", "arjan-bok-plumbing", "Arjan Bok Plumbing",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired and not able to contract at this time (expire 11/30/2009).",
     286,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time.' (expire date 11/30/2009). The business cannot legally contract.")],
     "top300"),
    ("1003603", "dlb-plumbing", "DLB Plumbing",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired; there may be a legal requirement to meet and a contractors bond is needed to reactivate (expire 05/31/2023).",
     262,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time. There may be a legal requirement to be met prior to renewal or reactivation of the license. The license will need a contractors bond to renew active or reactivate.' (expire date 05/31/2023). The business cannot legally contract.")],
     "batch4"),
    ("664620", "superior-plumbing", "Superior Plumbing",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired and will need a contractors bond to reactivate (expire 02/28/2023).",
     262,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time. The license will need a contractors bond to renew active or reactivate.' (expire date 02/28/2023). The business cannot legally contract.")],
     "batch4"),
    ("868068", "plumb-in-time-plumbing-services-inc", "Plumb-In-Time Plumbing Services Inc",
     "do-not-hire",
     "DO NOT BOOK: CSLB shows this license is expired (expire 11/30/2007) for an Illinois corporation.",
     271,
     [("critical", "LICENSE EXPIRED - do not book",
       "CSLB: 'This license is expired and not able to contract at this time.' (expire date 11/30/2007; address of record 360 Memorial Drive #140, Crystal Lake, IL 60014). The business cannot legally contract.")],
     "batch4"),

    # ---------------- HISTORICAL (superseded entities, kept for tracing) ----------------
    ("744542", "rescue-rooter-prior-entity", "Rescue Rooter (prior entity)",
     "historical",
     "Expired 01/31/2008 Memphis partnership license (Rescue Rooter). The brand continues under ARS American Residential Services of California Inc (CSLB 765155), which is current and active. Kept so the permit record can be traced.",
     347,
     [("info", "Expired predecessor of active ARS license 765155",
       "CSLB: 'This license is expired and not able to contract at this time.' (expire date 01/31/2008). The same Rescue Rooter brand is now carried by ARS American Residential Services of California Inc, CSLB 765155, which is current and active."),
      ("info", "347 SF permit rows under 'Rescue Rooter'",
       "The permit aggregate lists 347 'Rescue Rooter' contact rows under license 744542, all predating the 2008 expiration.")],
     "top300"),
    ("931237", "fast-water-heater-partners-i-lp-prior-entity", "Fast Water Heater Partners I LP (prior entity)",
     "historical",
     "Canceled 10/02/2013 per request (Bothell, WA). The brand continues under Fast Home Services LLC (CSLB 987398), which is current and active. Kept so the permit record can be traced.",
     406,
     [("info", "Canceled predecessor of active Fast Home Services license 987398",
       "CSLB: 'This license is canceled and not able to contract.' Miscellaneous Information reads 10/02/2013 - LICENSE CANCELED PER REQUEST (expire date 10/01/2013). The same water-heater brand family continues under Fast Home Services LLC, CSLB 987398, which is current and active."),
      ("info", "406 SF permit rows under 'Fast Water Heater Partners I Lp'",
       "The permit aggregate lists 406 contact rows under license 931237, all predating the 2013 cancellation.")],
     "top300"),
]


def clean_addr(raw: str | None) -> str | None:
    if not raw:
        return None
    return raw.replace(" / ", ", ")


def main() -> int:
    extract = json.loads((DATA / "_cslb_extract.json").read_text(encoding="utf-8"))
    curation = json.loads((DATA / "curation.json").read_text(encoding="utf-8"))
    existing = curation["entries"]
    existing_keys = {str(x["key"]) for x in existing}
    existing_ids = {x["id"] for x in existing}

    built = []
    for key, ident, name, tier, headline, permits, flags, ptype in ROWS:
        rec = extract[key]
        addr = clean_addr(rec["cslb_address"])
        phone = rec["cslb_phone"]
        city_note = ""
        # permit source block
        if ptype == "top300":
            p_src = {"label": "SF plumbing-permit aggregate (Building permits, all-time contact rows for this name/license)",
                     "url": TOPT_URL, "tier": "official-gov", "access": "direct", "raw": TOPT}
        else:
            p_src = {"label": "SF plumbing-permit counts - per-license query (data.sfgov.org)",
                     "url": B4_URLS[key], "tier": "official-gov", "access": "direct", "raw": B4}
        yelp_q = urllib.parse.quote_plus(name)
        sources = [
            {"label": f"CSLB license record {key}",
             "url": f"https://www2.cslb.ca.gov/OnlineServices/CheckLicenseII/LicenseDetail.aspx?LicNum={key}",
             "tier": "official-gov", "access": "direct", "raw": f"data/raw/cslb-{key}.txt"},
            p_src,
            {"label": f"Yelp - manual review search for {name}",
             "url": f"https://www.yelp.com/search?find_desc={yelp_q}&find_loc=San+Francisco%2C+CA",
             "tier": "official-platform", "access": "manual-review"},
            {"label": f"Google reviews - manual review for {name}",
             "url": f"https://www.google.com/search?q={yelp_q}+San+Francisco+reviews",
             "tier": "official-platform", "access": "manual-review"},
        ]
        flags_out = [{"severity": sev, "label": lbl, "detail": det} for sev, lbl, det in flags]
        built.append({
            "key": key,
            "id": ident,
            "display_name": name,
            "dba": None,
            "tier": tier,
            "headline": headline,
            "phone_display": phone,
            "address_display": addr,
            "website": None,
            "sf_permits": permits,
            "research_batch": BATCH,
            "job_fit": {
                "snake_shower": "unknown", "tub_overflow_access": "unknown",
                "prewar_galvanized": "unknown", "camera_inspection": "unknown",
                "non_destructive": "unknown", "weekend_emergency": "unknown",
            },
            "ratings": [],
            "evidence": [],
            "flags": flags_out,
            "sources": sources,
        })

    # wrong-scale entry: no plumbing classification -> out of scope for the core tasks
    for b in built:
        if b["key"] == "533324":
            b["job_fit"] = {
                "snake_shower": "no", "tub_overflow_access": "no",
                "prewar_galvanized": "no", "camera_inspection": "unknown",
                "non_destructive": "no", "weekend_emergency": "no",
            }

    # sanity: uniqueness
    assert len({b["id"] for b in built}) == len(built), "duplicate id"
    assert len({b["key"] for b in built}) == len(built), "duplicate key"
    dup_ids = {b["id"] for b in built} & existing_ids
    dup_keys = {b["key"] for b in built} & existing_keys
    assert not dup_ids, f"id collides with existing entries: {dup_ids}"
    assert not dup_keys, f"key collides with existing entries: {dup_keys}"

    # merge into curation (replace same-key entries if re-run)
    by_key = {str(x["key"]): x for x in existing}
    for b in built:
        by_key[b["key"]] = b
    # preserve original order, then append new ones in table order
    seen = set()
    merged = []
    for x in existing:
        if str(x["key"]) not in seen:
            merged.append(by_key.get(str(x["key"]), x))
            seen.add(str(x["key"]))
    for b in built:
        if b["key"] not in seen:
            merged.append(b)
            seen.add(b["key"])
    curation["entries"] = merged
    (DATA / "curation.json").write_text(
        json.dumps(curation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # register the expansion gate
    gates = json.loads((DATA / "expansion_gates.json").read_text(encoding="utf-8"))
    do_not_hire = [b["key"] for b in built if b["tier"] == "do-not-hire"]
    required_flags = {}
    for b in built:
        terms = []
        code = extract[b["key"]]["status_code"]
        if code == "revoked":
            terms = ["revoked"]
        elif code == "suspended":
            terms = ["suspension", "judgment"]
        elif code == "inactive":
            terms = ["inactive"]
        elif code == "canceled":
            terms = ["canceled"]
        elif code == "expired":
            terms = ["expired"]
        if b["tier"] == "wrong-scale":
            terms = ["general building", "c36"]
        if terms:
            required_flags[b["key"]] = terms
    for k in ("339522",):
        required_flags[k].append("death")
    gate = {
        "count": len(built),
        "licenses": sorted(b["key"] for b in built),
        "status_summary": {"active": 26, "revoked": 2, "suspended": 1,
                           "inactive": 3, "canceled": 6, "expired": 12},
        "required_flags": required_flags,
        "critical_flag_licenses": do_not_hire,
        "status_disclosures": {
            "823991": "complaint disclosure",
            "591329": "complaint disclosure",
            "979693": "civil judgment",
            "269424": "inactive",
            "933593": "workers compensation",
            "923951": "workers compensation",
            "339522": "death",
            "698559": "bond",
            "1003603": "bond",
            "664620": "bond",
            "570753": "canceled after expiration",
            "763612": "canceled after expiration",
        },
        "strict_permit_counts": False,
        "finalized": True,
    }
    gates[BATCH] = gate
    (DATA / "expansion_gates.json").write_text(
        json.dumps(gates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"built {len(built)} entries -> data/curation.json")
    print(f"gate {BATCH}: {gate['status_summary']}")
    print(f"critical flags: {len(do_not_hire)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
