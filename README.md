# Verified San Francisco Plumbers — one specific job

A research system and a published website that answers a narrow question properly:

> **Which San Francisco plumbers are actually qualified and currently licensed to snake a slow
> shower drain and safely free a stuck bathtub overflow trip lever in a c.1940 house — without
> cutting into walls — and how do you verify that yourself?**

The property is a rent-controlled SF rental, so the legal context is part of the answer, not an
afterthought.

**Live site:** published from `docs/` via GitHub Pages (see *Deploying* below).

---

## What this is not

This is not a scraped list of Yelp ratings. Every business on the master list was resolved to a
California Contractors State License Board license number, the official CSLB license detail page was
captured verbatim, and the business was accepted or rejected **on that record alone**. Review
platforms were then used only to assess job fit — never to establish whether a contractor may
lawfully do the work.

That distinction turned out to matter a great deal. See [Findings that changed the answer](#findings-that-changed-the-answer).

---

## Results at a glance

| | |
|---|---|
| Businesses on the master list | **37** |
| CSLB license records captured and checked | **37** |
| Businesses with a verified **ACTIVE** C36 license | **27** |
| Quotes and aggregates checked verbatim against captures | **96** |
| Critical irregularities flagged | **15** |
| Raw capture files in `data/raw/` | **46** (.txt + .json) |
| Validator status | **PASS — 0 errors, 0 warnings** |

All figures are regenerated on every build and are read from `data/validation_report.json`.

---

## The job

- Bathtub draining at roughly **20%** of normal flow.
- Shower draining at roughly **60–80%**.
- Bathtub **overflow trip lever seized**, tub not accessible from below.
- House built **c.1940**, likely original **galvanized** drain piping.
- Rent-controlled San Francisco rental.

**Hard requirement:** the plumber must be able to snake the shower drain *and* safely remove the
stuck trip-lever assembly **without replacing or reopening plumbing behind walls**.

### The single most useful thing discovered

San Francisco Building Code / Plumbing Code **§104.2 (Exempt Work)** says:

> "(2) Unstopping of traps, sewers, vents or waste pipes not requiring cutting into or removal of
> traps or piping"

— is **exempt work: no permit required**. Meanwhile [sf.gov](https://www.sf.gov/apply-plumbing-and-mechanical-permit)
states a permit *is* needed "before cutting into or replacing pipes, particularly pipes that will be
covered by a wall", and that only "a licensed contractor registered with the City of San Francisco"
may pull it.

So the tenant's constraint is not merely a preference — it is the legally simpler, faster, cheaper
path. And it yields a screening question that instantly separates good bidders from bad ones:

> **"Can you pull the trip-lever linkage out through the overflow plate, or do you need wall
> access?"**

---

## Findings that changed the answer

These are the reasons a ratings-first approach would have produced a wrong answer.

1. **Bright Ideas Plumbing and Rooter** — Thumbtack shows a **"License verified" badge**, BBB shows
   **A+**, Thumbtack shows **4.9 stars over 241 reviews**, and it has the single best captured review
   in the entire dataset for this exact job (a clogged bathtub drain diagnosed and fixed without
   demolition). CSLB license **1018638 EXPIRED 09/30/2024** and the bond was canceled 03/27/2025.
   The Thumbtack badge is dated **Apr 19, 2021** — three and a half years before the license lapsed —
   and is still displayed. **Not hireable.**

2. **ACE Plumbing and Rooter** — Yelp **4.7 across 1,512 reviews**, **3,172 SF plumbing permits**
   (the second-highest of any firm examined). CSLB license **829071 is under Contractors Bond
   Suspension**, bond canceled 09/01/2026. **Not hireable.**

3. **Servadei Service Inc** — **1,586 SF plumbing permits**, which would rank it above Atlas, Lutz,
   Mulgrew, Cabrillo and Citywide on permit volume alone. CSLB license **168371 was CANCELED
   11/30/2002** with a Secretary of State dissolution. Every permit predates the cancellation by
   more than two decades. **Permit volume is evidence of history, never of current authority.**

4. **Mr. Rooter Plumbing of San Francisco** has **three** license entities. `SFGDL Industries Inc dba
   Mr Rooter of San Francisco` (**974194**) **EXPIRED 08/31/2021** and is registered to Frederick,
   **Colorado**. The live license is **453536** (Ferguson Plumbing Inc, Oakland). A third entity,
   `Br Troika Inc. dba Mr Rooter Plumbing` (**812845**), holds **318** SF permits and was **not**
   verified in this pass. BBB also publishes an expiry date for 453536 that is two years earlier than
   CSLB's — the aggregator's license cache is stale.

5. **Discount Plumbing & Rooter** — all **2,623** SF permit records belong to `Discount Plumbing Co`
   (**755272**), **CANCELED 09/13/2025**. The two live LLCs (1140843, 1144424) have **no permit rows
   at all**. Both live licenses are ACTIVE with current bonds and workers' comp, so this is a
   corporate-continuity question rather than a disqualification — but the impressive track record is
   historical.

6. **Repipe Specialists** was provisionally linked to license **1099220**. The official SF open-data
   permit extract names 1099220 as **"X-Ray Plumbing And Drain Llc"** — a different business. The
   attribution was **withdrawn and corrected in-repo**. An unverified attribution is exactly the
   failure mode this project exists to prevent, so the mistake is recorded rather than quietly
   deleted.

7. **Crusader Plumbing** is recommended in SF community threads. No CSLB license number could be
   located and an explicit zero-result SF permit query was recorded. **Not hireable on this evidence.**

8. **Gateway Plumbing (846292)**, **Ace (829071)** and **Joseph Tinsley / Fast Response (1024971)**
   all show the same bond carrier and the same **09/01/2026** cancellation date. That looks like one
   systemic event affecting several SF plumbing licenses rather than three unrelated failures —
   re-check all three before ruling any of them out permanently. CSLB itself notes a bond "may have
   been received by the Board but not yet processed", in which case suspension lifts retroactively.

9. **Red Wrench Plumbing** is an excellent, BBB A+ accredited plumber that two independent captures
   agree **does not perform drain cleaning or sewer work**. Wrong half of this job.

10. **A G Quality Plumbing** is BBB **A+** and Yelp **4.6/177** but carries an Angi overall rating of
    **1.0**. When platforms disagree that sharply, the review score is worthless and the CSLB record
    plus permit history (229) becomes the only usable signal.

---

## How verification works

Nothing in this repo is asserted from memory. There is a hard, mechanical chain:

```
data/raw/*.txt              verbatim captures, each with SOURCE_URL / CAPTURED_AT / ACCESS / TIER
      │
      ├─ scripts/extract_cslb.py ──► data/_cslb_extract.json   (official license facts only)
      │
data/curation.json          the analytical layer: tiers, job fit, evidence pointers, flags
      │
      └─ scripts/build_data.py ────► data/plumbers.json + data/master_list.csv
                                            │
                                     scripts/validate.py  ◄── re-reads data/raw/ and FAILS the build
                                            │               if any quote, license field or status
                                            │               is not found verbatim
                                            ▼
                                     scripts/build_site.py ──► docs/index.html
                                            (refuses to run unless validation_report.json says PASS)
```

`scripts/validate.py` enforces:

1. **Raw-file integrity** — every referenced capture exists and carries a `SOURCE_URL`.
2. **License provenance** — every license number has a `cslb-<number>.txt` whose `SOURCE_URL`
   contains that number.
3. **License field parity** — `legal_name`, `status_code`, `entity`, `issue_date`, `expire_date`,
   `classifications` and `cslb_phone` must match the official capture exactly.
4. **Status parity** — `active` requires the capture to literally say *"current and active"*;
   `suspended` requires suspension language; `expired` requires the word *expired*.
5. **Quote parity** — every review quote, rating figure, legal citation and code section must appear
   verbatim (whitespace-normalised) **inside the `SOURCE` block of the capture whose URL it cites**.
6. **Source hygiene** — every URL must be well-formed and its host must be on an allow-list of
   domains actually visited. A fabricated URL cannot pass.
7. **Tier legality** — no business may be `recommended`/`viable`/`conditional` unless its CSLB status
   is `active`; none may be `do-not-hire` while active.
8. **Access honesty** — if the data says a datapoint is `direct` but the capture header says
   `indirect-search-snippet`, that is an error.
9. **Coverage** — at least 20 distinct businesses with a verified ACTIVE license.
10. **Vocabulary** — every `job_fit` value comes from a declared, documented set.

---

## Provenance and access log

Honesty about *how* each number was obtained is part of the deliverable.

| Source | Tier | Access |
|---|---|---|
| `www2.cslb.ca.gov` LicenseDetail | official-gov | **direct** — 37 records captured |
| `data.sfgov.org` Socrata API (`k6kv-9kix`) | official-gov | **direct** — 56 rows |
| `leginfo.legislature.ca.gov` (Civ. Code §1941.1) | official-gov | **direct** |
| `codelibrary.amlegal.com` (SF Building Code §104) | official-gov | **direct** |
| `sftu.org` (SF Tenants Union) | tenant-advocacy-org | **direct** |
| `sf.gov` permit pages | official-gov | indirect (search text) |
| `bbb.org` | official-platform | **direct** |
| `thumbtack.com` | official-platform | **direct** |
| `yelp.com` | official-platform | **BLOCKED — HTTP 403.** All Yelp data is search-snippet only |
| `reddit.com` | community | **BLOCKED — HTTP 403** on www, old.reddit and `.json` |
| Google Maps / Business Profile | official-platform | indirect (aggregator) |

Everything obtained indirectly is badged as such on the site, inline, next to the figure — it is
never silently presented as a direct read.

---

## Trust tiers

| Tier | Weight |
|---|---|
| `official-gov` | **Decisive.** Overrides every other source. CSLB, SF open data, SF Building Code, California Civil Code. |
| `official-platform` | Strong for what the platform publishes (accreditation, review text). **Weak for license status, which platforms cache.** BBB, Thumbtack, Yelp, Google. |
| `tenant-advocacy-org` | Strong on tenant process. Not legal advice. SF Tenants Union, Housing Rights Committee. |
| `third-party-aggregator` | Corroborating only, never decisive. ConsumerAffairs, Angi, BuildZoom, Yahoo Local. |
| `community` | Directional only. Generates candidates and screening questions; never establishes a fact. Reddit. |
| `vendor-self-reported` | Lowest. Service scope and contact details only. Company websites. |

---

## Tenant rights (verified, official)

Because this is a rent-controlled rental, the site carries the governing texts rather than a summary:

- **California Civil Code §1941.1(a)(2)** — a dwelling is untenantable if it substantially lacks
  *"Plumbing or gas facilities that conformed to applicable law in effect at the time of
  installation, maintained in good working order."* A tub at 20% and a shower at 60–80% engages this.
- **§1941.1(a)(3)** — hot and cold running water connected to an approved sewage disposal system.
- **San Francisco Tenants Union** remedies ladder: written notice → DBI inspection and order to
  correct (usually 30 days) → Rent Board *Decrease in Housing Services* petition → repair-and-deduct
  (max one month's rent, twice per 12 months) → rent withholding.
- **Civil Code §1942.4** — statutory damages of up to **$5,000** in a habitability lawsuit.
- **The 35-day rule** — a landlord cannot demand rent, evict for nonpayment, or raise rent where
  serious housing code violations have gone uncorrected for at least 35 days after an order to
  correct.
- **SF Administrative Code §37.10B** — it is illegal for a landlord, in bad faith, to *"Fail to
  provide repairs or maintenance promised by contract or required by law."*
- **Rent control coverage** — a c.1940 building predates June 14, 1979 and is almost certainly
  covered by the San Francisco Rent Stabilization and Arbitration Ordinance.
- **Warning carried verbatim from the SF Tenants Union** — *"Do not call DBI if you live in an
  illegal unit."* DBI may order the unit legalised or shut down, and the tenant may be evicted.

---

## Repository layout

```
data/
  raw/                     46 verbatim source captures (.txt with provenance headers, .json API dumps)
    cslb-<license>.txt     one per CSLB license record, with SOURCE_URL and CAPTURED_AT
    legal-regulatory.txt   Civ. Code 1941.1, SF Building Code 104, SF Tenants Union, Rent Ordinance
    reviews-bbb.txt        BBB profiles and search results
    reviews-thumbtack.txt  Thumbtack credentials and named reviews
    reviews-yelp-indirect.txt      Yelp — search-snippet only (403 blocked direct)
    reviews-reddit-indirect.txt    Reddit — search-snippet only (403 blocked direct)
    reviews-google-indirect.txt    Google — aggregator only
    reviews-aggregators.txt        ConsumerAffairs, Angi, BuildZoom, Yahoo Local, Expertise
    reviews-company-sites.txt      vendor self-reported service scope
    sfgov-permit-counts.json       56 rows: firm_name / license_number / permit count
    sfgov-plumbing-permits-contacts.md
  curation.json            the analytical layer (human reasoning, with pointers into data/raw/)
  _cslb_extract.json       parsed official license facts (generated)
  plumbers.json            the master list (generated)
  master_list.csv          flat mirror for spreadsheets (generated)
  validation_report.json   the validator's verdict (generated)
scripts/
  extract_cslb.py          parse CSLB captures → _cslb_extract.json
  build_data.py            merge official facts + curation → plumbers.json, master_list.csv
  validate.py              the anti-hallucination gate; non-zero exit blocks publication
  build_site.py            render docs/index.html; refuses to run if validation failed
docs/                      the published GitHub Pages site (generated)
```

---

## Running it

Requires only Python 3.10+ — no third-party packages.

```bash
make all        # extract → build → validate → site
make validate   # just the gate
make check      # validate + site, i.e. what CI runs
make serve      # preview docs/ locally on :8080
```

Or explicitly:

```bash
python3 scripts/extract_cslb.py
python3 scripts/build_data.py
python3 scripts/validate.py     # exits non-zero on any error
python3 scripts/build_site.py
```

---

## Deploying

The site is plain static HTML with no build step at serve time. The build emits the site to `docs/`
and also writes a small root `index.html` redirect stub plus `.nojekyll`, so the site works under
**either** Pages configuration:

| Pages source | What serves | Notes |
|---|---|---|
| branch `arena/01a06996-plumbingsf`, path `/docs` | `docs/index.html` directly | Canonical. No redirect hop. |
| branch `main`, path `/` | root `index.html` → redirects to `docs/index.html` | Works as soon as this branch is merged, with no settings change. |

To set the canonical configuration: **Settings → Pages → Build and deployment → Source: Deploy from
a branch**, branch `arena/01a06996-plumbingsf`, path `/docs`. This requires repository admin rights —
the automation token used to build this work can push but cannot change Pages settings.

The site is published at `https://buffedlizard55-lab.github.io/PlumbingSF/`.

`.github/workflows/ci.yml` runs the full extract → build → **validate** → site pipeline on every push
and pull request and **fails the build if any quote or license field cannot be traced to a capture**.
`docs/.nojekyll` is committed so Pages serves the files untouched.

To redeploy after merging to `main`, switch the Pages branch to `main` / `/docs`.

---

## Caveats

- **CSLB statuses change.** Re-check any license at
  [cslb.ca.gov → Check a License](https://www2.cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx)
  on the day you book. Three suspensions in this dataset share one bond-cancellation date and may be
  administrative and curable.
- **Yelp, Reddit and Google figures are indirect.** Those platforms blocked automated access
  (HTTP 403 / JS-only rendering). Every such figure is badged on the site and must be re-checked by
  hand before you rely on a specific number.
- **Permit counts corroborate SF activity; they do not prove current authority.** Servadei Service
  Inc is the worked example.
- **Absence of a permit row is weak evidence.** The extract used a top-60 ranking plus targeted
  firm-name queries, so a firm may simply not have been in the queried name set. Only `CRUSADER` was
  explicitly confirmed as a zero-result query.
- **Not legal advice, and not an endorsement.** Entries are ranked by verified licence status,
  captured evidence of the specific work required, and SF permit history.
