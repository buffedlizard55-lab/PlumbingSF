# Official City & County of San Francisco open data source

SOURCE_URL: https://data.sfgov.org/api/views/k6kv-9kix.json
HUMAN_URL: https://data.sfgov.org/Housing-and-Buildings/Plumbing-Permits-Contacts/k6kv-9kix
CAPTURED_AT: 2026-09-03 (fetched via tool)
TYPE: Official municipal dataset - provenance "official", category "Housing and Buildings"
PUBLISHER: City & County of San Francisco (data.sfgov.org / domainCName data.sf.gov)

## Dataset metadata (verbatim excerpts)
"id" : "k6kv-9kix",
"name" : "Plumbing Permits Contacts",
"category" : "Housing and Buildings",
"description" : "Contacts of contractors for Plumbing Permits",
"downloadCount" : 19396,
"provenance" : "official",
"rowsUpdatedAt" : 1788439853,
"licenseId" : "PDDL",

## Columns (verbatim excerpts)
"name" : "Permit Number", "fieldName" : "permit_number", non_null 511532
"name" : "Firm Name", "fieldName" : "firm_name", non_null 510527
"name" : "License Number", "fieldName" : "license_number", non_null 511316
"name" : "Address", "fieldName" : "address", non_null 502476

## Why this source matters
This is an official City record of every plumbing permit contact in San Francisco. It lets us
(a) cross-check a contractor's CSLB license number against a second independent official source, and
(b) count how many SF plumbing permits a firm has actually pulled, which is an objective proxy for
hands-on experience inside San Francisco buildings (including pre-1950 housing stock).
