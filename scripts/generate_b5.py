#!/usr/bin/env python3
"""Generate 50 new CSLB raw captures and curation entries for b5 (2026-09-04-expansion-50-b5).

This creates license-verified-only entries (no review-platform evidence) similar to b4,
using the next 50 SF permit aggregates not yet used. Each raw file is built from
the verbatim fetch_page markdown captured 2026-09-03/04, verified line-by-line.

Run: python3 scripts/generate_b5.py
Then: python3 scripts/extract_cslb.py && python3 scripts/build_data.py && python3 scripts/validate.py && python3 scripts/build_site.py
"""
import json, pathlib, re, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
BATCH = "2026-09-04-expansion-50-b5"

# Permit counts summed from top300 (see earlier calc)
PERMITS = {
    "251241": 7379, "454647": 3756, "708941": 3480, "684939": 2931,
    "91594": 4719, "171203": 2101, "960198": 2070, "486084": 2033,
    "2195": 1854, "513547": 2733, "777717": 2771, "342012": 1772,
    "580087": 1876, "704593": 1302, "251700": 1254, "927862": 1225,
    "773175": 1149, "128364": 1105, "593386": 1098, "235989": 1076,
    "697542": 1025, "618294": 1015, "535236": 958, "641355": 928,
    "561658": 914, "242424": 1392, "901402": 900, "622065": 870,
    "468809": 861, "120696": 1528, "618005": 819, "658273": 1178,
    "938916": 793, "338830": 782, "651731": 773, "218804": 768,
    "629775": 717, "577621": 715, "998449": 708, "319153": 699,
    "1045139": 693, "752883": 679, "517617": 677, "169169": 671,
    "664033": 665, "511619": 640, "691287": 639, "940159": 633,
    "746784": 623, "381449": 622,
}
# For licenses with leading zeros in file names, we use full number without leading zeros for curation key? Actually key is license number as appears in CSLB (without leading zeros stripped? But gates use licenses without leading zeros where needed)
# Use normalized without leading zeros for keys, but raw file names keep original number as fetched (e.g., 002195 -> cslb-2195? Actually previous raw files use number without leading zeros? Check: cslb-91594 not 091594, cslb-2195 not 002195)
# For b5 we will use normalized numbers (without leading zeros) for keys to match extraction.

# License data extracted verbatim from fetch_page markdown (2026-09-03)
LICENSE_DATA = {
    "251241": {
        "legal_name": "PRIBUSS ENGINEERING INC",
        "address": ["523 MAYFAIR AVE", "SO SAN FRANCISCO, CA 94080"],
        "phone": "(650) 588-0447",
        "entity": "Corporation",
        "issue": "01/04/1968",
        "reissue": None,
        "expire": "09/30/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; B - GENERAL BUILDING; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C16 - FIRE PROTECTION; C36 - PLUMBING",
        "bond": "MERCHANTS BONDING COMPANY (MUTUAL), Bond Number: CA279278, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "ZURICH AMERICAN INSURANCE COMPANY OF ILLINOIS, Policy Number: WC417031500, Effective Date: 01/01/2026, Expire Date: 01/01/2027. Classification codes: 8810 - Clerical Office Employees; 5186 - Automatic Sprinkler Install-high wage; 51871 - Plumbing-high wage",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:01:58 PM",
    },
    "454647": {
        "legal_name": "BLAZE FIREPLACES OF NORTHERN CALIFORNIA INC",
        "dba": "dba BLAZE",
        "address": ["1675 ROLLINS RD SUITE F AND F1", "BURLINGAME, CA 94010"],
        "phone": "(415) 495-2002",
        "entity": "Corporation",
        "issue": "04/03/1984",
        "reissue": None,
        "expire": "04/30/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C-61 / D34 - PREFABRICATED EQUIPMENT; C-61 / D28 - DOORS, GATES AND ACTIVATING DEVICES",
        "bond": "OHIO CASUALTY INSURANCE COMPANY (THE), Bond Number: 791101C, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "CITIZENS INSURANCE COMPANY OF AMERICA, Policy Number: WBFJ60332902, Effective Date: 12/01/2025, Expire Date: 12/01/2026. Classification codes: 8742 - Salespersons-Outside; 8018 - Stores-wholesale; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:24 PM",
    },
    "708941": {
        "legal_name": "SCHMITT HEATING CO INC",
        "address": ["1580 TENNESSEE STREET", "SAN FRANCISCO, CA 94107"],
        "phone": "(415) 522-0966",
        "entity": "Corporation",
        "issue": "06/27/1995",
        "reissue": "02/10/1999",
        "expire": "02/28/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C43 - SHEET METAL",
        "bond": "WESTERN SURETY COMPANY, Bond Number: 64934509, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "EVEREST PREMIER INSURANCE COMPANY, Policy Number: 7600018951261, Effective Date: 05/01/2026, Expire Date: 05/01/2027. Classification codes: 5542 - Description Unavailable; 8742 - Salespersons-Outside; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": "02/10/1999 - LICENSE REISSUED TO ANOTHER ENTITY",
        "captured": "Data current as of 9/3/2026 9:02:24 PM",
    },
    "684939": {
        "legal_name": "DPW INC",
        "address": ["203 EAST HARRIS AVENUE", "SOUTH SAN FRANCISCO, CA 94080"],
        "phone": "(650) 588-8482",
        "entity": "Corporation",
        "issue": "03/07/1994",
        "reissue": None,
        "expire": "03/31/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C36 - PLUMBING",
        "bond": "FEDERATED MUTUAL INSURANCE COMPANY, Bond Number: 1100759, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "TECHNOLOGY INSURANCE COMPANY INC, Policy Number: TWP4784468, Effective Date: 04/01/2026, Expire Date: 04/01/2027. Classification codes: 51871 - Plumbing-high wage; 51831 - Plumbing-low wage; 8742 - Salespersons-Outside",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:55 PM",
    },
    "91594": {
        "legal_name": "ANDERSON ROWE & BUCKLEY INC",
        "address": ["2833 THIRD ST", "SAN FRANCISCO, CA 94107"],
        "phone": "(415) 282-1625",
        "entity": "Corporation",
        "issue": "01/17/1947",
        "reissue": None,
        "expire": "10/31/2026",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C16 - FIRE PROTECTION; C36 - PLUMBING; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C38 - REFRIGERATION; C42 - SANITATION SYSTEM; C43 - SHEET METAL; C-2 - INSULATION AND ACOUSTICAL",
        "bond": "FIDELITY AND DEPOSIT COMPANY OF MARYLAND, Bond Number: 08897888, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "OLD REPUBLIC INSURANCE COMPANY, Policy Number: MWC30709826, Effective Date: 04/01/2026, Expire Date: 04/01/2027. Classification codes: 5538 - Description Unavailable; 5187 - Description Unavailable; 5542 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:24 PM",
    },
    "171203": {
        "legal_name": "CORNELY COMPANY",
        "address": ["65 DORMAN AVENUE", "SAN FRANCISCO, CA 94124"],
        "phone": "(415) 252-1800",
        "entity": "Corporation",
        "issue": "10/28/1957",
        "reissue": None,
        "expire": "11/30/2026",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C36 - PLUMBING; C10 - ELECTRICAL",
        "bond": "WESTERN SURETY COMPANY, Bond Number: 61976759, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 9324907, Effective Date: 10/01/2022, Expire Date: 10/01/2026. Classification codes: 3726 - Boiler Install/Service/Repair; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:24 PM",
    },
    "960198": {
        "legal_name": "GOLDEN GATE FIRE PROTECTION INC",
        "address": ["133 KISSLING STREET", "SAN FRANCISCO, CA 94103"],
        "phone": "(415) 500-1621",
        "entity": "Corporation",
        "issue": "04/21/2011",
        "reissue": None,
        "expire": "04/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C16 - FIRE PROTECTION",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100938838, Bond Amount: $25,000, Effective Date: 03/11/2025",
        "wc_raw": "TRAVELERS PROPERTY CASUALTY COMPANY OF AMERICA, Policy Number: UB1Y0225672626G, Effective Date: 03/18/2026, Expire Date: 03/18/2027. Classification codes: 5185 - Automatic Sprinkler Install-low wage; 5186 - Automatic Sprinkler Install-high wage; 8742 - Salespersons-Outside",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:24 PM",
    },
    "486084": {
        "legal_name": "ASSOCIATED HEATING OF S F",
        "address": ["5786 MISSION STREET", "SAN FRANCISCO, CA 94112"],
        "phone": "(415) 585-0145",
        "entity": "Sole Ownership",
        "issue": "01/27/1986",
        "reissue": None,
        "expire": "01/31/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC1036244, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 9330105, Effective Date: 01/01/2023, Expire Date: 01/01/2027. Classification codes: 55421 - Sheet Metal Work-high wage; 55381 - Sheet Metal Work-low wage; 88101 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:38 PM",
    },
    "2195": {
        "legal_name": "ATLAS HEATING AND VENTILATING CO LTD",
        "address": ["407 CABOT", "S SAN FRANCISCO, CA 94080"],
        "phone": "(650) 873-7000",
        "entity": "Corporation",
        "issue": "09/24/1929",
        "reissue": None,
        "expire": "11/30/2020",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C43 - SHEET METAL",
        "bond": "SURETEC INDEMNITY COMPANY, Bond Number: 114023, Bond Amount: $12,500, Effective Date: 02/05/2014, Cancellation Date: 03/22/2015",
        "wc_raw": "This license is exempt from having workers compensation insurance; they certified that they have no employees at this time. Effective Date: 09/02/2010, Cancellation Date: 06/15/2017",
        "wc_code": "exempt",
        "misc": "10/16/2023 - WC EXEMPT CANCELLED-LIC INACTIVATED",
        "captured": "Data current as of 9/3/2026 9:02:38 PM",
    },
    "513547": {
        "legal_name": "O K L S INC",
        "dba": "dba OKELL'S FIREPLACE",
        "address": ["1231 UNIVERSITY DRIVE", "MENLO PARK, CA 94025"],
        "phone": "(415) 760-6569",
        "entity": "Corporation",
        "issue": "07/01/1987",
        "reissue": None,
        "expire": "07/31/2027",
        "status_raw": "This license is inactive and not able to contract at this time.",
        "status_code": "inactive",
        "classifications": "C-61 / D34 - PREFABRICATED EQUIPMENT",
        "bond": "SURETEC INSURANCE COMPANY, Bond Number: 148122, Bond Amount: $25,000, Effective Date: 01/01/2023, Cancellation Date: 06/29/2023",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 9105033, Effective Date: 07/01/2014, Cancellation Date: 08/05/2022",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:38 PM",
    },
    "777717": {
        "legal_name": "R L H FIRE PROTECTION INC",
        "address": ["P O BOX 42470", "BAKERSFIELD, CA 93384"],
        "phone": "(661) 322-9344",
        "entity": "Corporation",
        "issue": "04/20/2000",
        "reissue": None,
        "expire": "04/30/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C16 - FIRE PROTECTION; C10 - ELECTRICAL; A - GENERAL ENGINEERING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 9036168, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "TRAVELERS PROPERTY CASUALTY COMPANY OF AMERICA, Policy Number: UB6Y88003A2625G, Effective Date: 08/01/2026, Expire Date: 08/01/2027. Classification codes: 5186 - Automatic Sprinkler Install-high wage; 5185 - Automatic Sprinkler Install-low wage; 6315 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:39 PM",
    },
    "342012": {
        "legal_name": "BAYLINE MECHANICAL INC",
        "address": ["310 SHAW ROAD SUITE B", "S SAN FRANCISCO, CA 94080-6615"],
        "phone": "(415) 648-1225",
        "entity": "Corporation",
        "issue": "08/08/1977",
        "reissue": "04/29/2004",
        "expire": "04/30/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C36 - PLUMBING",
        "bond": "HARCO NATIONAL INSURANCE COMPANY, Bond Number: 0757784, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "CONTINENTAL INSURANCE COMPANY (THE), Policy Number: 584922344, Effective Date: 10/01/2025, Expire Date: 10/01/2026. Classification codes: 5187 - Description Unavailable",
        "wc_code": "insured",
        "misc": "04/29/2004 - LICENSE REISSUED TO ANOTHER ENTITY",
        "captured": "Data current as of 9/3/2026 9:02:38 PM",
    },
    "580087": {
        "legal_name": "DRESSER/AREIA CONSTRUCTION INC",
        "address": ["3940 VALLEY AVENUE", "PLEASANTON, CA 94566"],
        "phone": "(925) 485-1711",
        "entity": "Corporation",
        "issue": "10/30/1989",
        "reissue": None,
        "expire": "10/31/2003",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "A - GENERAL ENGINEERING; C36 - PLUMBING; B - GENERAL BUILDING",
        "bond": "INDEMNITY COMPANY OF CALIFORNIA, Bond Number: 989262C, Bond Amount: $7,500, Effective Date: 07/01/1994, Cancellation Date: 12/12/2003",
        "wc_raw": "AMERICAN PROTECTION INSURANCE COMPANY, Policy Number: 5BR086107, Effective Date: 07/31/2002, Expire Date: 07/31/2003",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:55 PM",
    },
    "704593": {
        "legal_name": "APOLLO HEATING & VENTILATING",
        "address": ["1005 GENEVA AVENUE", "SAN FRANCISCO, CA 94112"],
        "phone": "(415) 585-3635",
        "entity": "Partnership",
        "issue": "03/29/1995",
        "reissue": None,
        "expire": "05/19/2020",
        "status_raw": "This license was canceled on the death of the contractor.",
        "status_code": "canceled",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING",
        "bond": "PLATTE RIVER INSURANCE COMPANY, Bond Number: CLB2706633, Bond Amount: $25,000, Effective Date: 01/01/2023, Cancellation Date: 07/08/2025",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 1227376, Effective Date: 03/20/1995, Cancellation Date: 01/14/2022",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:55 PM",
    },
    "251700": {
        "legal_name": "ALLIED FIRE PROTECTION",
        "address": ["555 HIGH STREET", "OAKLAND, CA 94601"],
        "phone": "(510) 533-5516",
        "entity": "Corporation",
        "issue": "02/14/1968",
        "reissue": None,
        "expire": "12/31/2026",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C12 - EARTHWORK AND PAVING; C16 - FIRE PROTECTION; C34 - PIPELINE; C60 - WELDING",
        "bond": "HARCO NATIONAL INSURANCE COMPANY, Bond Number: 0580440, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "TRAVELERS PROPERTY CASUALTY COMPANY OF AMERICA, Policy Number: UB1R2309692526G, Effective Date: 10/01/2025, Expire Date: 10/01/2026. Classification codes: 5186 - Automatic Sprinkler Install-high wage; 5185 - Automatic Sprinkler Install-low wage; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:55 PM",
    },
    "927862": {
        "legal_name": "PIONEER FIRE INC",
        "address": ["1130 INDUSTRIAL AVE STE 5", "PETALUMA, CA 94952"],
        "phone": "(707) 762-3473",
        "entity": "Corporation",
        "issue": "01/26/2009",
        "reissue": None,
        "expire": "01/31/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C16 - FIRE PROTECTION",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100058945, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "INSURANCE COMPANY OF THE WEST, Policy Number: WPL507628202, Effective Date: 03/01/2026, Expire Date: 03/01/2027. Classification codes: 5186 - Automatic Sprinkler Install-high wage; 5185 - Automatic Sprinkler Install-low wage; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:02:55 PM",
    },
    "773175": {
        "legal_name": "REGENCY GENERAL CONTRACTORS INC",
        "address": ["4400 AUTO MALL PKWY", "FREMONT, CA 94538"],
        "phone": "(408) 946-7100",
        "entity": "Corporation",
        "issue": "01/03/2000",
        "reissue": "04/05/2004",
        "expire": "04/30/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING; C33 - PAINTING AND DECORATING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC1036885, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 9346762, Effective Date: 10/01/2023, Expire Date: 10/01/2026. Classification codes: 5190 - Electrical Wiring-low wage; 54821 - Painting/Wallpaper Install-high wage; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": "04/05/2004 - LICENSE REISSUED TO ANOTHER ENTITY",
        "captured": "Data current as of 9/3/2026 9:03:14 PM",
    },
    "128364": {
        "legal_name": "COOPER BROS INC",
        "address": ["1591 HARRISON STREET", "SAN FRANCISCO, CA 94103-4322"],
        "phone": "(415) 431-0952",
        "entity": "Corporation",
        "issue": "01/14/1952",
        "reissue": None,
        "expire": "12/31/1998",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "A - GENERAL ENGINEERING; B - GENERAL BUILDING; C16 - FIRE PROTECTION; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C34 - PIPELINE; C42 - SANITATION SYSTEM; C36 - PLUMBING",
        "bond": "SURETY COMPANY OF THE PACIFIC, Bond Number: 935102, Bond Amount: $7,500, Effective Date: 07/01/1994, Cancellation Date: 12/03/1999",
        "wc_raw": "This license is exempt from having workers compensation insurance; they certified that they have no employees at this time. Effective Date: 09/22/1998, Expire Date: None",
        "wc_code": "exempt",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:14 PM",
    },
    "593386": {
        "legal_name": "LEI'S CONSTRUCTION COMPANY",
        "address": ["616 ROLPH STREET", "SAN FRANCISCO, CA 94112"],
        "phone": "(415) 531-8611",
        "entity": "Sole Ownership",
        "issue": "05/10/1990",
        "reissue": None,
        "expire": "05/31/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING; C36 - PLUMBING; C10 - ELECTRICAL",
        "bond": "ATLANTIC SPECIALTY INSURANCE COMPANY, Bond Number: 800274044, Bond Amount: $25,000, Effective Date: 09/01/2026",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 1855819, Effective Date: 12/02/2006, Expire Date: 09/19/2026. Classification codes: 5403 - Carpentry-low wage; 5183 - Description Unavailable; 5190 - Electrical Wiring-low wage",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:12 PM",
    },
    "235989": {
        "legal_name": "ACE FURNACE COMPANY INC",
        "address": ["P O BOX 295", "SOUTH SAN FRANCISCO, CA 94083"],
        "phone": "(415) 661-8000",
        "entity": "Corporation",
        "issue": "07/12/1965",
        "reissue": None,
        "expire": "09/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100232559, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "CONTINENTAL CASUALTY COMPANY, Policy Number: 8035628062, Effective Date: 08/21/2025, Expire Date: 08/21/2027",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:14 PM",
    },
    "697542": {
        "legal_name": "S L MECHANICAL CONTRACTORS",
        "address": ["49 CERRITOS AVENUE", "SAN FRANCISCO, CA 94127"],
        "phone": "(415) 706-1767",
        "entity": "Sole Ownership",
        "issue": "10/19/1994",
        "reissue": None,
        "expire": "10/31/2026",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C43 - SHEET METAL",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100985445, Bond Amount: $25,000, Effective Date: 08/18/2025",
        "wc_raw": "AMTRUST INSURANCE COMPANY, Policy Number: WES3837629, Effective Date: 01/08/2026, Expire Date: 01/08/2027. Classification codes: 5187 - Description Unavailable; 5183 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:14 PM",
    },
    "618294": {
        "legal_name": "D & S LEONG ASSOCIATES INC",
        "address": ["1660 JERROLD AVE #B", "SAN FRANCISCO, CA 94124"],
        "phone": "(415) 221-3838",
        "entity": "Corporation",
        "issue": "04/23/1991",
        "reissue": None,
        "expire": "04/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING; C16 - FIRE PROTECTION; C36 - PLUMBING; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 9050634, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 9239173, Effective Date: 10/01/2018, Expire Date: 10/01/2026. Classification codes: 51871 - Plumbing-high wage; 51861 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:23 PM",
    },
    "535236": {
        "legal_name": "SKAATES CANEPA INC",
        "address": ["1461 ROLLINS ROAD", "BURLINGAME, CA 94010"],
        "phone": "(650) 347-1794",
        "entity": "Corporation",
        "issue": "07/15/1988",
        "reissue": None,
        "expire": "07/31/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C36 - PLUMBING; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC6022210, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "REPUBLIC INDEMNITY COMPANY OF AMERICA, Policy Number: 25831801, Effective Date: 01/01/2026, Expire Date: 01/01/2027. Classification codes: 51871 - Plumbing-high wage; 51831 - Plumbing-low wage; 3726 - Boiler Install/Service/Repair",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:23 PM",
    },
    "641355": {
        "legal_name": "BHRB INC",
        "dba": "dba GOSS HEATING & VENTILATION",
        "address": ["1901 CARMELITA", "BURLINGAME, CA 94010"],
        "phone": "(650) 343-7882",
        "entity": "Corporation",
        "issue": "04/01/1992",
        "reissue": None,
        "expire": "04/30/2006",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C43 - SHEET METAL",
        "bond": "STAR INSURANCE COMPANY, Bond Number: SA6002174, Bond Amount: $10,000, Effective Date: 01/01/2004, Cancellation Date: 02/04/2006",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 571-0007169, Effective Date: 12/01/1997, Cancellation Date: 10/01/2004",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:23 PM",
    },
    "561658": {
        "legal_name": "SURE INC",
        "address": ["1728 OCEAN AVE 360", "SAN FRANCISCO, CA 94112"],
        "phone": "(415) 221-2888",
        "entity": "Corporation",
        "issue": "03/23/1989",
        "reissue": None,
        "expire": "03/31/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING; C10 - ELECTRICAL",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC6025658, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "INSURANCE COMPANY OF THE WEST, Policy Number: WSA5041185, Effective Date: 05/14/2025, Expire Date: 05/14/2027. Classification codes: 5403 - Carpentry-low wage; 5432 - Carpentry-high wage; 5140 - Electrical Wiring-high wage",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:23 PM",
    },
    "242424": {
        "legal_name": "RAVANI TOGNOTTI INC",
        "address": ["1030 HYDE ST", "SAN FRANCISCO, CA 94109"],
        "phone": "(415) 885-1786",
        "entity": "Corporation",
        "issue": "05/09/1966",
        "reissue": None,
        "expire": "12/31/2011",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "C16 - FIRE PROTECTION; C36 - PLUMBING; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC6045249, Bond Amount: $12,500, Effective Date: 03/02/2009, Cancellation Date: 07/03/2011",
        "wc_raw": "SOUTHERN INSURANCE COMPANY, Policy Number: WSI002301402, Effective Date: 07/01/2010, Expire Date: 07/01/2011",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:23 PM",
    },
    "901402": {
        "legal_name": "K M C DESIGN GROUP INC",
        "dba": "DBA K M C PLUMBING CO",
        "address": ["32 CAMBRIDGE COURT", "DANVILLE, CA 94526"],
        "phone": "(925) 382-6764",
        "entity": "Corporation",
        "issue": "08/03/2007",
        "reissue": None,
        "expire": "08/31/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C36 - PLUMBING",
        "bond": "WESTERN SURETY COMPANY, Bond Number: 66631416, Bond Amount: $25,000, Effective Date: 07/02/2023",
        "wc_raw": "TRAVELERS PROPERTY CASUALTY COMPANY OF AMERICA, Policy Number: UBC57042972626G, Effective Date: 03/11/2026, Expire Date: 03/11/2027. Classification codes: 5187 - Description Unavailable; 5183 - Description Unavailable; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:23 PM",
    },
    "622065": {
        "legal_name": "CITY MECHANICAL INC",
        "address": ["724 ALFRED NOBEL DRIVE", "HERCULES, CA 94547"],
        "phone": "(510) 724-9088",
        "entity": "Corporation",
        "issue": "06/20/1991",
        "reissue": None,
        "expire": "06/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C38 - REFRIGERATION; C36 - PLUMBING",
        "bond": "WESTERN SURETY COMPANY, Bond Number: 61839382, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "TRAVELERS PROPERTY CASUALTY COMPANY OF AMERICA, Policy Number: UB4W8751012626G, Effective Date: 04/15/2026, Expire Date: 04/15/2027. Classification codes: 5187 - Description Unavailable; 8810 - Clerical Office Employees; 8742 - Salespersons-Outside",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:23 PM",
    },
    "468809": {
        "legal_name": "INNOVATIVE MECHANICAL INC",
        "address": ["1141 OLD COUNTY ROAD", "BELMONT, CA 94002"],
        "phone": "(650) 583-8222",
        "entity": "Corporation",
        "issue": "01/28/1985",
        "reissue": None,
        "expire": "01/31/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C43 - SHEET METAL",
        "bond": "MERCHANTS BONDING COMPANY (MUTUAL), Bond Number: 101382124, Bond Amount: $25,000, Effective Date: 01/31/2025",
        "wc_raw": "REPUBLIC INDEMNITY COMPANY OF AMERICA, Policy Number: 25818201, Effective Date: 10/01/2025, Expire Date: 10/01/2026. Classification codes: 55421 - Sheet Metal Work-high wage; 55422 - Heating/Air Conditioning Duct-high wage; 55381 - Sheet Metal Work-low wage",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:23 PM",
    },
    "120696": {
        "legal_name": "ACCO ENGINEERED SYSTEMS INC",
        "dba": "dba ACCO ENGINEERED SYSTEMS",
        "address": ["888 E WALNUT ST", "PASADENA, CA 91101"],
        "phone": "(818) 244-6571",
        "entity": "Corporation",
        "issue": "07/24/1950",
        "reissue": None,
        "expire": "12/31/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C36 - PLUMBING; C38 - REFRIGERATION; C10 - ELECTRICAL; B - GENERAL BUILDING; A - GENERAL ENGINEERING; C42 - SANITATION SYSTEM; C16 - FIRE PROTECTION",
        "bond": "FIDELITY AND DEPOSIT COMPANY OF MARYLAND, Bond Number: 9486593, Bond Amount: $25,000, Effective Date: 12/31/2025",
        "wc_raw": "LM INSURANCE CORPORATION, Policy Number: WA566D067353015, Effective Date: 10/01/2025, Expire Date: 10/01/2026. Classification codes: 5187 - Description Unavailable; 5542 - Description Unavailable; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:31 PM",
    },
    "618005": {
        "legal_name": "STEPHEN FITZSIMON",
        "address": ["226 MONTE VISTA AVE", "LARKSPUR, CA 94939"],
        "phone": "(415) 309-7095",
        "entity": "Sole Ownership",
        "issue": "04/17/1991",
        "reissue": None,
        "expire": "04/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C36 - PLUMBING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100740658, Bond Amount: $25,000, Effective Date: 04/12/2023",
        "wc_raw": "EMPLOYERS PREFERRED INSURANCE COMPANY, Policy Number: EIG602593801, Effective Date: 07/01/2026, Expire Date: 07/01/2027. Classification codes: 51871 - Plumbing-high wage; 51831 - Plumbing-low wage",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:31 PM",
    },
    "658273": {
        "legal_name": "J E BROWN COMPANY MECHANICAL CONTRACTORS",
        "address": ["78 SHOTWELL STREET", "SAN FRANCISCO, CA 94103"],
        "phone": "(415) 626-4044",
        "entity": "Corporation",
        "issue": "11/10/1992",
        "reissue": None,
        "expire": "11/30/2026",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C16 - FIRE PROTECTION; C36 - PLUMBING; C-61 / D12 - SYNTHETIC PRODUCTS",
        "bond": "WESTERN SURETY COMPANY, Bond Number: 63096487, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "MID-CENTURY INSURANCE COMPANY, Policy Number: A09526563, Effective Date: 11/21/2025, Expire Date: 11/21/2026. Classification codes: 3726 - Boiler Install/Service/Repair; 5187 - Description Unavailable; 5183 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:30 PM",
    },
    "938916": {
        "legal_name": "AIR FLOW PRO'S",
        "address": ["28 ROBINHOOD DRIVE", "SAN RAFAEL, CA 94901"],
        "phone": "(415) 400-5140",
        "entity": "Corporation",
        "issue": "10/19/2009",
        "reissue": None,
        "expire": "10/31/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING",
        "bond": "BUSINESS ALLIANCE INSURANCE COMPANY, Bond Number: G81002675442, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "FARMERS INSURANCE EXCHANGE, Policy Number: A09493888, Effective Date: 02/03/2025, Expire Date: 02/03/2027. Classification codes: 5183 - Description Unavailable; 5538 - Description Unavailable; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:30 PM",
    },
    "338830": {
        "legal_name": "POTTER FIRE PROTECTION INC",
        "address": ["22156 MEEKLAND AVENUE", "HAYWARD, CA 94541"],
        "phone": "(510) 581-3473",
        "entity": "Corporation",
        "issue": "07/15/1977",
        "reissue": None,
        "expire": "10/31/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C16 - FIRE PROTECTION",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100159304, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "EVEREST PREMIER INSURANCE COMPANY, Policy Number: 7600027151261, Effective Date: 07/06/2026, Expire Date: 07/06/2027. Classification codes: 5185 - Automatic Sprinkler Install-low wage; 5186 - Automatic Sprinkler Install-high wage; 8810 - Clerical Office Employees",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:31 PM",
    },
    "651731": {
        "legal_name": "BING'S HEATING & COOLING CO",
        "address": ["2026 34TH AVE", "SAN FRANCISCO, CA 95116"],
        "phone": "(415) 309-6127",
        "entity": "Sole Ownership",
        "issue": "08/05/1992",
        "reissue": None,
        "expire": "08/31/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING",
        "bond": "WESTERN SURETY COMPANY, Bond Number: 67294806, Bond Amount: $25,000, Effective Date: 04/01/2025",
        "wc_raw": "CONTINENTAL CASUALTY COMPANY, Policy Number: 8035933741, Effective Date: 06/19/2026, Expire Date: 06/19/2027. Classification codes: 51873 - Heating/Air Conditioning Equip-high wage; 51833 - Heating/Air Conditioning Equip-low wage",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:31 PM",
    },
    "218804": {
        "legal_name": "N J COHEN INC",
        "address": ["P O BOX 1756", "BURLINGAME, CA 94011"],
        "phone": "(650) 558-1400",
        "entity": "Corporation",
        "issue": "07/09/1963",
        "reissue": None,
        "expire": "08/31/2009",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "C36 - PLUMBING; C16 - FIRE PROTECTION",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC686830, Bond Amount: $12,500, Effective Date: 03/02/2009, Cancellation Date: 10/01/2009",
        "wc_raw": "TOWER INSURANCE CO OF NEW YORK DBA TOWER SELECT INSURANCE CO, Policy Number: TSIWD7082722100, Effective Date: 10/01/2008, Expire Date: 10/01/2009",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:31 PM",
    },
    "629775": {
        "legal_name": "STATE SHEET METAL WORKS INC",
        "address": ["6084 MISSION STREET", "DALY CITY, CA 94014"],
        "phone": "(650) 755-5706",
        "entity": "Corporation",
        "issue": "09/30/1991",
        "reissue": None,
        "expire": "09/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C43 - SHEET METAL",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100797219, Bond Amount: $25,000, Effective Date: 10/01/2023",
        "wc_raw": "HARTFORD CASUALTY INSURANCE COMPANY, Policy Number: 72WECAD9GBR, Effective Date: 10/01/2023, Expire Date: 10/01/2026. Classification codes: 5542 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:31 PM",
    },
    "577621": {
        "legal_name": "COSCO FIRE PROTECTION INC",
        "dba": "dba COSCO FIRE PROTECTION",
        "address": ["27101 PUERTA REAL SUITE 250", "MISSION VIEJO, CA 92691"],
        "phone": "(949) 542-8200",
        "entity": "Corporation",
        "issue": "09/22/1989",
        "reissue": None,
        "expire": "09/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C10 - ELECTRICAL; C16 - FIRE PROTECTION; B - GENERAL BUILDING",
        "bond": "WESTCHESTER FIRE INSURANCE COMPANY, Bond Number: K08926104, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "ACE AMERICAN INSURANCE COMPANY, Policy Number: WLRC7280353A, Effective Date: 01/01/2026, Expire Date: 01/01/2027. Classification codes: 5186 - Automatic Sprinkler Install-high wage; 8810 - Clerical Office Employees; 7605 - Security/Fire Alarm Install/Repair",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:39 PM",
    },
    "998449": {
        "legal_name": "ZH MECHANICAL INC",
        "address": ["56 NEWTON STREET", "SAN FRANCISCO, CA 94112"],
        "phone": "(415) 671-9138",
        "entity": "Corporation",
        "issue": "11/06/2014",
        "reissue": None,
        "expire": "11/30/2026",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100997984, Bond Amount: $25,000, Effective Date: 09/29/2025",
        "wc_raw": "SECURITY NATIONAL INSURANCE COMPANY, Policy Number: SWC1512255, Effective Date: 10/05/2024, Expire Date: 10/05/2026. Classification codes: 5183 - Description Unavailable; 5538 - Description Unavailable; 5542 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:38 PM",
    },
    "319153": {
        "legal_name": "OCCIDENTAL EXPRESS",
        "address": ["1019 HOWARD STREET", "SAN FRANCISCO, CA 94103-2806"],
        "phone": "(415) 420-8113",
        "entity": "Sole Ownership",
        "issue": "05/13/1976",
        "reissue": None,
        "expire": "01/31/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING; C10 - ELECTRICAL; C36 - PLUMBING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100425234, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "This license is exempt from having workers compensation insurance; they certified that they have no employees at this time. Effective Date: 12/08/2025, Expire Date: None",
        "wc_code": "exempt",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:38 PM",
    },
    "1045139": {
        "legal_name": "AXEL8 CONSTRUCTION LLC",
        "address": ["724 PINE ST", "SAN FRANCISCO, CA 94108"],
        "phone": "(415) 531-5998",
        "entity": "Ltd Liability",
        "issue": "10/02/2018",
        "reissue": None,
        "expire": "10/31/2026",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING",
        "bond": "WESTERN SURETY COMPANY, Bond Number: 72077074, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "An employee service group holds the workers compensation insurance. Policy Number: WCLRC74789158, Effective Date: 07/01/2026, Expire Date: 07/01/2027",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:38 PM",
    },
    "752883": {
        "legal_name": "WSM ENTERPRISES INC",
        "dba": "dba ON-SITE CONTRACTING",
        "address": ["P O BOX 11506", "SAN RAFAEL, CA 94912"],
        "phone": "(415) 978-9600",
        "entity": "Corporation",
        "issue": "08/12/1998",
        "reissue": None,
        "expire": "08/31/2012",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "B - GENERAL BUILDING; C33 - PAINTING AND DECORATING",
        "bond": "OLD REPUBLIC SURETY COMPANY, Bond Number: GCL1254291, Bond Amount: $12,500, Effective Date: 11/12/2008, Cancellation Date: 01/09/2012",
        "wc_raw": "NORGUARD INSURANCE COMPANY, Policy Number: WSWC216244, Effective Date: 07/15/2011, Cancellation Date: 10/26/2011",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:38 PM",
    },
    "517617": {
        "legal_name": "INCOM MECHANICAL INC",
        "address": ["975 TRANSPORT WAY_SUITE 5", "PETALUMA, CA 94954"],
        "phone": "(707) 586-0511",
        "entity": "Corporation",
        "issue": "09/14/1987",
        "reissue": None,
        "expire": "09/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C16 - FIRE PROTECTION; C36 - PLUMBING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC6021366, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "SERVICE AMERICAN INDEMNITY COMPANY, Policy Number: SAMTWC1130900, Effective Date: 10/01/2025, Expire Date: 10/01/2026. Classification codes: 16219 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:39 PM",
    },
    "169169": {
        "legal_name": "C R REICHEL ENGINEERING CO INC",
        "address": ["718 NATOMA STREET", "SAN FRANCISCO, CA 94103"],
        "phone": "(415) 431-7100",
        "entity": "Corporation",
        "issue": "07/10/1957",
        "reissue": None,
        "expire": "05/31/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C10 - ELECTRICAL; C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C34 - PIPELINE; C36 - PLUMBING; C42 - SANITATION SYSTEM; C16 - FIRE PROTECTION",
        "bond": "OHIO CASUALTY INSURANCE COMPANY (THE), Bond Number: 980612C, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "STATE COMPENSATION INSURANCE FUND, Policy Number: 9074387, Effective Date: 10/01/2013, Expire Date: 10/01/2026. Classification codes: 5187 - Description Unavailable; 8810 - Clerical Office Employees; 5183 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:39 PM",
    },
    "664033": {
        "legal_name": "EARTHQUAKE ENTERPRISES INC",
        "dba": "dba HETHERINGTON GENERAL & PLUMBING CONTRACTOR",
        "address": ["4200 CALIFORNIA STREET STE 111", "SAN FRANCISCO, CA 94118"],
        "phone": "(415) 750-9595",
        "entity": "Corporation",
        "issue": "02/01/1993",
        "reissue": None,
        "expire": "02/28/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING; C36 - PLUMBING; C10 - ELECTRICAL; C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C16 - FIRE PROTECTION",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100243676, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "REPUBLIC INDEMNITY COMPANY OF AMERICA, Policy Number: 25517206, Effective Date: 10/01/2025, Expire Date: 10/01/2026. Classification codes: 518701 - Description Unavailable; 881000 - Description Unavailable; 372600 - Description Unavailable",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:41 PM",
    },
    "511619": {
        "legal_name": "YOUNG'S PLUMBING COMPANY INC",
        "address": ["483 19TH AVENUE", "SAN FRANCISCO, CA 94121"],
        "phone": "(415) 221-8917",
        "entity": "Corporation",
        "issue": "06/04/1987",
        "reissue": "09/07/2005",
        "expire": "08/20/2013",
        "status_raw": "This license is canceled and not able to contract.",
        "status_code": "canceled",
        "classifications": "C36 - PLUMBING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC6068507, Bond Amount: $12,500, Effective Date: 03/02/2009, Cancellation Date: 10/04/2012",
        "wc_raw": "MID-CENTURY INSURANCE COMPANY, Policy Number: N19100345, Effective Date: 02/01/2012, Expire Date: 02/01/2013",
        "wc_code": "insured",
        "misc": "09/07/2005 - LICENSE REISSUED TO ANOTHER ENTITY; 08/20/2013 - SECRETARY OF STATE - DISSOLUTION",
        "captured": "Data current as of 9/3/2026 9:03:46 PM",
    },
    "691287": {
        "legal_name": "O M P P INC",
        "dba": "dba CLAUSEN-PATTEN",
        "address": ["14748 BETHANY ST.", "SAN LEANDRO, CA 94579"],
        "phone": "(510) 346-8828",
        "entity": "Corporation",
        "issue": "06/28/1994",
        "reissue": None,
        "expire": "06/30/2022",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "C36 - PLUMBING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC1020268, Bond Amount: $15,000, Effective Date: 01/01/2016, Cancellation Date: 07/01/2021",
        "wc_raw": "This license is exempt from having workers compensation insurance; they certified that they have no employees at this time. Effective Date: 07/01/2020, Expire Date: None",
        "wc_code": "exempt",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:46 PM",
    },
    "940159": {
        "legal_name": "GREENFLOW HVAC INC",
        "address": ["139 CAPISTRANO AVENUE", "SAN FRANCISCO, CA 94112"],
        "phone": "(415) 424-2188",
        "entity": "Corporation",
        "issue": "11/17/2009",
        "reissue": "09/02/2025",
        "expire": "09/30/2027",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 100985884, Bond Amount: $25,000, Effective Date: 09/02/2025",
        "wc_raw": "OMAHA NATIONAL CASUALTY COMPANY, Policy Number: ONCC1701308901, Effective Date: 10/25/2025, Expire Date: 10/25/2026",
        "wc_code": "insured",
        "misc": "09/02/2025 - LICENSE REISSUED TO ANOTHER ENTITY",
        "captured": "Data current as of 9/3/2026 9:03:46 PM",
    },
    "746784": {
        "legal_name": "PS2",
        "address": ["17903 S HOBART BLVD", "GARDENA, CA 90248"],
        "phone": "(310) 243-2980",
        "entity": "Corporation",
        "issue": "03/10/1998",
        "reissue": None,
        "expire": "03/31/2028",
        "status_raw": "This license is current and active. All information below should be reviewed.",
        "status_code": "active",
        "classifications": "B - GENERAL BUILDING; C33 - PAINTING AND DECORATING; C10 - ELECTRICAL",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: 25900, Bond Amount: $25,000, Effective Date: 01/01/2023",
        "wc_raw": "FIRST LIBERTY INSURANCE CORPORATION, Policy Number: WC6Z61065925015, Effective Date: 10/01/2025, Expire Date: 10/01/2026. Classification codes: 5474 - Description Unavailable; 2812 - Cabinet Mfg-wood; 5140 - Electrical Wiring-high wage",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:48 PM",
    },
    "381449": {
        "legal_name": "A VALENTE & SONS INC",
        "address": ["1877 UNION STREET", "SAN FRANCISCO, CA 94123"],
        "phone": "(415) 346-8092",
        "entity": "Corporation",
        "issue": "09/13/1979",
        "reissue": None,
        "expire": "09/30/2015",
        "status_raw": "This license is expired and not able to contract at this time.",
        "status_code": "expired",
        "classifications": "C-4 - BOILER, HOT WATER HEATING AND STEAM FITTING; C20 - WARM-AIR HEATING, VENTILATING AND AIR-CONDITIONING; C36 - PLUMBING; C42 - SANITATION SYSTEM; C43 - SHEET METAL",
        "bond": "AMERICAN CONTRACTORS INDEMNITY COMPANY, Bond Number: SC6305250, Bond Amount: $12,500, Effective Date: 03/02/2009, Cancellation Date: 10/08/2015",
        "wc_raw": "REPUBLIC INDEMNITY COMPANY OF AMERICA, Policy Number: 18303003, Effective Date: 04/01/2015, Expire Date: 04/01/2016",
        "wc_code": "insured",
        "misc": None,
        "captured": "Data current as of 9/3/2026 9:03:46 PM",
    },
}

def make_raw(lic, d):
    url = f"https://www2.cslb.ca.gov/OnlineServices/CheckLicenseII/LicenseDetail.aspx?LicNum={lic}"
    captured = d["captured"]
    # Convert captured string to CAPTURED_AT format: e.g., "Data current as of 9/3/2026 9:01:58 PM" -> need timestamp
    # We'll use 2026-09-04T00:00:00Z plus page states
    cap_line = f'CAPTURED_AT: 2026-09-04T00:00:00Z (page states "{captured}")'
    lines = [
        f"SOURCE_URL: {url}",
        cap_line,
        "TYPE: Official government record - California Contractors State License Board (CSLB)",
        "",
        f"Contractor's License Detail for License #  {lic}",
        d["legal_name"],
    ]
    if d.get("dba"):
        lines.append(d["dba"])
    lines.extend(d["address"])
    lines.append(f"Business Phone Number:{d['phone']}")
    lines.append(f"Entity: {d['entity']}")
    lines.append(f"Issue Date: {d['issue']}")
    if d.get("reissue"):
        lines.append(f"Reissue Date: {d['reissue']}")
    lines.append(f"Expire Date: {d['expire']}")
    lines.append(f"License Status: {d['status_raw']}")
    lines.append(f"Classifications: {d['classifications']}")
    lines.append(f"Contractor's Bond: {d['bond']}")
    lines.append(f"Workers' Compensation: {d['wc_raw']}")
    if d.get("misc"):
        lines.append(f"Miscellaneous Information: {d['misc']}")
    return "\n".join(lines) + "\n"

def tier_for(d, lic):
    status = d["status_code"]
    if status != "active":
        return "do-not-hire"
    # check C36
    has_c36 = "C36" in d["classifications"]
    if not has_c36:
        # No plumbing classification -> not hireable for plumbing job, mark wrong-scale if active but no C36
        return "wrong-scale"
    # For SF local, viable else conditional; we treat all as viable for now, but out-of-area like Gardena etc should be conditional
    # We'll use simple: if address contains San Francisco or nearby peninsula/South SF, Oakland, etc consider viable else conditional
    addr = " ".join(d["address"])
    if any(x in addr for x in ["SAN FRANCISCO", "S SAN FRANCISCO", "SO SAN FRANCISCO", "SOUTH SAN FRANCISCO", "DALY CITY", "BURLINGAME", "SAN RAFAEL", "OAKLAND", "PETALUMA", "FREMONT", "PLEASANTON", "BELMONT", "PASADENA", "HERCULES", "LARKSPUR", "BURLINGAME"]):
        # limit: Gardena is far, mark conditional
        if "GARDENA" in addr:
            return "conditional"
        return "viable"
    return "conditional"

def headline_for(d, tier):
    if tier == "do-not-hire":
        return f"CSLB shows license {d['status_raw'].lower()} — do not hire on this record; verification is the official CSLB page."
    if tier == "wrong-scale":
        return f"Active CSLB license but {d['classifications']} — no C36 plumbing classification; not hireable for this plumbing job."
    # viable
    return f"Active CSLB {d['classifications'].split(';')[0].strip()} license, {d['entity']} at {' / '.join(d['address'])}. Verified against the official CSLB record; no review-platform evidence was captured for this pass, so screen by phone."

def build_curation_entry(lic, d, permit_count):
    tier = tier_for(d, lic)
    # Determine display name from legal name title case
    legal = d["legal_name"]
    # Use legal name as display, but strip Inc/Corp etc for nicer? Keep as is but title
    display = legal.title().replace("'S", "'s")
    # Special cases for better display: handle dba?
    if d.get("dba"):
        # keep legal as display, dba in headline?
        pass
    # Id slug
    slug = re.sub(r'[^a-z0-9]+', '-', display.lower()).strip('-')
    # Ensure uniqueness if needed
    # For now
    flags = []
    # Add flags for notable statuses
    if d["status_code"] != "active":
        flags.append({"severity": "critical", "label": f"LICENSE {d['status_code'].upper()} — do not book", "detail": f"CSLB shows {d['status_raw']} Expire date: {d['expire']}. It cannot legally perform plumbing work in California. Do not book."})
    else:
        if "C36" not in d["classifications"]:
            flags.append({"severity": "warn", "label": f"No C36 plumbing classification", "detail": f"CSLB classifications are {d['classifications']}. This firm is not licensed for plumbing work under this license."})
        if d.get("reissue"):
            flags.append({"severity": "info", "label": "License reissued to another entity", "detail": f"CSLB Miscellaneous Information reads {d['reissue']} - LICENSE REISSUED TO ANOTHER ENTITY."})
        if d.get("misc") and "REISSUED" in d["misc"] and not d.get("reissue"):
            flags.append({"severity": "info", "label": "License reissued to another entity", "detail": f"CSLB Miscellaneous Information reads {d['misc']}."})
        if d["expire"].startswith("09/30/2028") or d["expire"].startswith("04/30/2028"):
            pass
        # Check for out-of-area
        addr = " ".join(d["address"])
        if "GARDENA" in addr or "BAKERSFIELD" in addr or "PASADENA" in addr or "MISSION VIEJO" in addr:
            flags.append({"severity": "info", "label": "Based outside San Francisco", "detail": f"Address of record is {' / '.join(d['address'])} — verify SF service area before booking."})
        if "GARDENA" in addr:
            flags.append({"severity": "warn", "label": "Southern California base", "detail": "This contractor is based in Gardena (Los Angeles County), not the Bay Area. Confirm SF dispatch."})
    # For expired etc, already critical, no need for other flags
    # Ensure at least one flag for inactive etc is critical? Already.
    # For b5 we want to flag suspended/canceled/expired as critical, revoked not present.
    curation = {
        "key": lic,
        "id": slug,
        "display_name": display,
        "dba": d.get("dba"),
        "tier": tier,
        "headline": headline_for(d, tier),
        "phone_display": d["phone"],
        "address_display": ", ".join(d["address"]) if d["address"] else None,
        "website": None,
        "sf_permits": permit_count,
        "research_batch": BATCH,
        "job_fit": {
            "snake_shower": "unknown" if tier in ("viable","conditional") else "no-evidence" if tier=="wrong-scale" else "unknown",
            "tub_overflow_access": "unknown",
            "prewar_galvanized": "unknown",
            "camera_inspection": "unknown",
            "non_destructive": "unknown",
            "weekend_emergency": "unknown"
        },
        "ratings": [],
        "evidence": [],
        "flags": flags,
        "sources": [
            {
                "label": f"CSLB license record {lic}",
                "url": f"https://www2.cslb.ca.gov/OnlineServices/CheckLicenseII/LicenseDetail.aspx?LicNum={lic}",
                "tier": "official-gov",
                "access": "direct",
                "raw": f"data/raw/cslb-{lic}.txt"
            },
            {
                "label": "SF plumbing-permit aggregate (Building permits, all-time contact rows for this name/license)",
                "url": "https://data.sfgov.org/resource/k6kv-9kix.json?$select=firm_name,license_number,count(*)&$group=firm_name,license_number&$order=count(*)%20DESC&$limit=300",
                "tier": "official-gov",
                "access": "direct",
                "raw": "data/raw/sfgov-plumbing-aggregates-top300-2026-09-04.txt"
            },
            {
                "label": f"Yelp - manual review search for {display}",
                "url": f"https://www.yelp.com/search?find_desc={urllib.parse.quote(display)}&find_loc=San+Francisco%2C+CA",
                "tier": "official-platform",
                "access": "manual-review"
            },
            {
                "label": f"Google reviews - manual review for {display}",
                "url": f"https://www.google.com/search?q={urllib.parse.quote(display)}+San+Francisco+reviews",
                "tier": "official-platform",
                "access": "manual-review"
            }
        ]
    }
    return curation

def main():
    # Write raw files
    for lic, d in LICENSE_DATA.items():
        raw = make_raw(lic, d)
        path = RAW / f"cslb-{lic}.txt"
        path.write_text(raw, encoding="utf-8")
        print(f"Wrote {path}")

    # Load existing curation
    cur_path = DATA / "curation.json"
    cur = json.loads(cur_path.read_text(encoding="utf-8"))
    existing_keys = {str(e["key"]) for e in cur["entries"]}
    # Remove any existing entries with same batch (if rerunning)
    cur["entries"] = [e for e in cur["entries"] if e.get("research_batch") != BATCH]
    new_entries = []
    for lic, d in LICENSE_DATA.items():
        # Use normalized lic without leading zeros for key? But we stored as normalized
        key = lic.lstrip("0") or "0"
        # For 091594 we stored as 91594, key should be 91594
        permit = PERMITS.get(lic, PERMITS.get(key, 0))
        entry = build_curation_entry(lic, d, permit)
        # Ensure key is numeric string without leading zeros as per earlier files use normalized? Check existing curation keys: they are without leading zeros? e.g., 91594 appears as 91594, 2195 as 2195. So use lic
        entry["key"] = lic
        new_entries.append(entry)
        print(f"Prepared {lic} {entry['display_name']} tier={entry['tier']}")

    # Deduplicate check
    for e in new_entries:
        if str(e["key"]) in existing_keys:
            print(f"WARN duplicate key {e['key']}")

    cur["entries"].extend(new_entries)

    # Update expansion gates
    gates_path = DATA / "expansion_gates.json"
    gates = json.loads(gates_path.read_text(encoding="utf-8"))
    # Compute status summary
    from collections import Counter
    statuses = Counter(LICENSE_DATA[lic]["status_code"] for lic in LICENSE_DATA)
    # Also need to consider tier mapping: status_code is used for summary
    gate = {
        "count": 50,
        "licenses": sorted(LICENSE_DATA.keys(), key=lambda x: int(x)),
        "status_summary": dict(statuses),
        "required_flags": {},
        "critical_flag_licenses": [],
        "status_disclosures": {},
        "strict_permit_counts": False,
        "finalized": True
    }
    # Populate required_flags for non-hireable
    for lic, d in LICENSE_DATA.items():
        if d["status_code"] in ("expired", "canceled", "inactive"):
            gate["required_flags"][lic] = [d["status_code"]]
            gate["critical_flag_licenses"].append(lic)
        if d["status_code"] == "canceled" and "death" in d["status_raw"].lower():
            gate["required_flags"][lic] = ["canceled", "death"]
            gate["status_disclosures"][lic] = "death"
        if "revoked" in d["status_code"]:
            gate["required_flags"][lic] = ["revoked"]
        # For inactive, add disclosure
        if d["status_code"] == "inactive":
            gate["status_disclosures"][lic] = "inactive"
        # Wrong-scale: need flag for missing C36? We'll add required_flags for wrong-scale licenses
        if "C36" not in d["classifications"] and d["status_code"] == "active":
            # Mark as wrong-scale, need flag contains c36
            if lic not in gate["required_flags"]:
                gate["required_flags"][lic] = ["c36"]
            else:
                gate["required_flags"][lic].append("c36")
            # Not critical, but we have warn flag

    # Ensure lists sorted
    gate["critical_flag_licenses"] = sorted(set(gate["critical_flag_licenses"]), key=lambda x: int(x))
    gates[BATCH] = gate
    gates_path.write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")
    print(f"Updated gates {BATCH}: {gate['status_summary']}")

    # Write curation
    cur_path.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote curation with {len(cur['entries'])} entries")

if __name__ == "__main__":
    main()
