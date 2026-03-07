# Client Vetting Pipeline - API & Database Research
## Compiled: 2026-03-06

---

# A. GOVERNMENT DEBARMENT / EXCLUSION LISTS

---

## A1. SAM.gov Exclusions API

| Field | Detail |
|-------|--------|
| **URL** | `https://api.sam.gov/entity-information/v4/exclusions` |
| **Alpha/Test** | `https://api-alpha.sam.gov/entity-information/v4/exclusions` |
| **Cost** | FREE |
| **Format** | REST API, JSON or CSV responses |
| **Auth** | API key from SAM.gov account (get at https://sam.gov/profile/details) |
| **Registration** | Create account at https://sam.gov, request "Public API Key" from Account Details page |

### Rate Limits
- No role (basic account): **10 requests/day**
- Non-federal user with role: **1,000 requests/day**
- Federal user: **1,000 requests/day**
- Federal system account: **10,000 requests/day**

### Search Parameters
- `exclusionName` - name of excluded entity
- `classification` - Firm, Individual, Special Entity Designation
- `exclusionType`, `exclusionProgram`
- `stateProvince`, `country`, `zipCode`
- `ueiSAM` - Unique Entity Identifier
- `cageCode` - CAGE code
- `npi` - National Provider Identifier
- `excludingAgencyCode`
- Date ranges: `activationDate`, `creationDate`, `updateDate`, `terminationDate`
- Supports operators: AND (`&`), OR (`~`), NOT (`!`), wildcard (`*`)

### Data Returned
- Entity name, classification, exclusion type/program
- Excluding agency
- UEI-SAM, CAGE code, NPI
- Address (primary and secondary)
- Activation/termination dates
- Record status, investigation status
- Vessel details (when applicable)

### Bulk Download
- Extract endpoint: `https://api.sam.gov/entity-information/v4/download-exclusions`
- Provides full list of all currently active exclusions
- Email notification when file is ready

---

## A2. SAM.gov Entity Management API

| Field | Detail |
|-------|--------|
| **URL** | `https://api.sam.gov/entity-information/v4/entities` |
| **Cost** | FREE |
| **Format** | REST API, JSON (sync) or CSV (async extract) |
| **Auth** | Same API key as Exclusions API |
| **Rate Limits** | Same tiers as Exclusions API |

### What It Provides (beyond exclusions)
- Entity registration details (who is registered to do business with the government)
- Core data: hierarchy, addresses, business info
- Assertions: goods/services, disaster relief
- Representations & certifications
- Points of contact
- **Integrity information** (relevant for vetting)
- Sync responses: 10 records/page; async extracts: up to 1,000,000 records

### Search Parameters
- UEI, CAGE code, business name
- Registration dates, location
- NAICS codes, PSC codes, business types
- 50+ additional filters

---

## A3. HHS OIG LEIE (List of Excluded Individuals/Entities)

| Field | Detail |
|-------|--------|
| **URL** | https://oig.hhs.gov/exclusions/exclusions_list.asp |
| **Search UI** | https://exclusions.oig.hhs.gov/ |
| **Cost** | FREE |
| **Format** | Downloadable database files (CSV) |
| **Auth** | None required for download |
| **API** | NO dedicated REST API -- download only |

### What It Covers
- Individuals and entities excluded from participation in Federal health care programs (Medicare, Medicaid, etc.)
- Updated monthly
- Complete database download includes all currently active exclusions
- Reinstated parties are removed from the file

### Relevance to Vetting
- Healthcare fraud exclusions
- Separate from SAM.gov (SAM covers government contracting; LEIE covers healthcare programs)
- Both should be checked for comprehensive vetting

---

## A4. OFAC SDN List (Specially Designated Nationals)

| Field | Detail |
|-------|--------|
| **URL** | https://sanctionslist.ofac.treas.gov/Home/SdnList |
| **Consolidated List** | https://sanctionslist.ofac.treas.gov/Home/ConsolidatedList |
| **Search Tool** | https://sanctionssearch.ofac.treas.gov/ |
| **Custom Dataset** | https://sanctionslist.ofac.treas.gov/Home/CustomizeSanctionsDataset |
| **Cost** | FREE |
| **Format** | XML, CSV, fixed-field, delimited files |
| **Auth** | None required for download |
| **API** | No official REST API -- file download + search tool |

### What It Covers
- Individuals, entities, groups designated under US sanctions programs
- Maritime vessels and aircraft
- Multiple sanctions programs (customizable by user)
- Delta files available for incremental updates

### Programmatic Integration
- Download XML/CSV files and parse locally
- Open-source tools exist (e.g., Moov OFAC -- Go library + HTTP API for parsing SDN data)
- GitHub: https://github.com/moov-io/watchman

---

# B. BANKRUPTCY FILINGS

---

## B1. PACER Case Locator (PCL) API

| Field | Detail |
|-------|--------|
| **URL** | `https://pcl.uscourts.gov/` (web) |
| **API Docs** | https://pacer.uscourts.gov/help/pacer/pacer-case-locator-pcl-api-user-guide |
| **Cost** | $0.10 per page; **fees waived if <=$30/quarter** |
| **Format** | REST API, JSON or XML |
| **Auth** | PACER account (register at https://pacer.uscourts.gov) |
| **Test Environment** | https://qa-pacer.uscourts.gov (free, test data) |

### Search Capabilities
- National index across all federal District, Bankruptcy, and Appellate courts
- Search by: party name, case number, date range, court, case type
- Bankruptcy-specific: chapter, trustee, discharge date, plan confirmation date

### Cost Analysis for Vetting
- At $0.10/page with $30/quarter waiver, a small-to-medium vetting operation could potentially stay under the waiver threshold
- Approximately 300 searches per quarter before incurring charges (assuming 1 page per search)
- Production searches are ALWAYS billable (even "no matches found" results incur charges)

### Key Limitations
- No free tier for production use
- Results pages are billed even if no matches
- Must register for a PACER account

---

## B2. CourtListener / RECAP Archive (Free Law Project)

| Field | Detail |
|-------|--------|
| **URL** | `https://www.courtlistener.com/api/rest/v4/` |
| **Bankruptcy Search** | https://www.courtlistener.com/recap/ |
| **Cost** | FREE |
| **Format** | REST API, JSON |
| **Auth** | Token auth (register at https://www.courtlistener.com, get token from account page) |
| **Rate Limit** | 5,000 requests/hour for authenticated users |

### Bankruptcy-Specific Features
- `/bankruptcy-information` endpoint with chapter, trustee info, key dates
- Linked via one-to-one relationship to Docket objects
- Populated for dockets acquired from bankruptcy courts via PACER

### Data Coverage
- Nearly 500 million PACER-related objects (dockets, entries, documents, parties, attorneys)
- Basic metadata scraped for every unsealed bankruptcy case since early 2021
- Regularly scrapes new case metadata from all courts
- Case name, docket number, date filed, date of last filing, date terminated
- Bankruptcy: assigned judge, chapter, plan confirmation date, debtor discharge date

### Key Advantages for Vetting
- **Free** -- best free option for bankruptcy searches
- Good coverage of basic metadata
- Full documents may not always be available (depends on RECAP user contributions)
- API supports filtering by Django-style field lookups

### Limitations
- Not 100% complete (depends on RECAP browser extension users uploading documents)
- Basic metadata is comprehensive, but full docket entries may be incomplete for some cases

---

## B3. Other Bankruptcy Search Options

### BankruptcyWatch (Commercial)
- **URL**: https://www.bankruptcywatch.com/
- **API Docs**: https://documenter.getpostman.com/view/13540419/TVmLAxnr
- **Cost**: Paid (pricing not public)
- Provides access to almost every piece of bankruptcy data found in the PACER system

### UniCourt (Freemium)
- **URL**: https://unicourt.com/
- Lookup PACER cases for free via web interface
- Paid "Legal Data as a Service" (LDaaS) API for bulk access
- Covers all US Bankruptcy Courts

### Epiq AACER (Commercial)
- **URL**: https://www.epiqglobal.com/
- 37+ million bankruptcy cases, 200+ million document pages
- Enterprise-grade; pricing via consultation

---

# C. PROPERTY / ASSET RECORDS

---

## C1. ATTOM Data Solutions (Aggregated County Assessor Data)

| Field | Detail |
|-------|--------|
| **URL** | https://api.developer.attomdata.com/docs |
| **Cost** | PAID -- starts at ~$95-500/month; ~$0.01-0.10 per API report |
| **Free Trial** | 30-day free trial available |
| **Format** | REST API, JSON and XML |
| **Auth** | API key (register at developer portal) |
| **Coverage** | 158+ million US properties, 3,000+ counties, 99% US population |

### Data Available
- Property addresses, building characteristics
- Ownership details, transaction history
- Deeds, mortgages, sales trends
- Tax assessor data (assessed values, tax amounts)
- Building permits
- 9,000+ attributes per property, 70+ billion rows total

### Search Methods
- Property address
- Parcel number (APN)
- ATTOM ID
- Longitude/latitude coordinates

### Relevance to Vetting
- Verify property ownership claims
- Identify asset holdings
- Cross-reference addresses

---

## C2. Zillow API

| Field | Detail |
|-------|--------|
| **Status** | HIGHLY RESTRICTED -- approval process takes weeks/months, frequently rejected |
| **URL** | https://www.zillowgroup.com/developers/ |
| **Cost** | Free if approved, but approval is the bottleneck |

### Current Reality
- Zillow has become increasingly restrictive about API access
- Older endpoints have been shut down
- Requires extensive documentation of use case
- NOT practical for a vetting pipeline
- **Recommendation: Skip Zillow; use ATTOM or alternatives**

---

## C3. Redfin

| Field | Detail |
|-------|--------|
| **Status** | NO public API available |
| **Data Center** | https://www.redfin.com/news/data-center/ (free downloadable market data by geography) |

### Available Without API
- Downloadable housing market data (CSV) by: National, Metro, State, County, City, Zip Code, Neighborhood
- This is aggregate market data, NOT individual property records
- **Not useful for individual property vetting**

### Unofficial Options
- Community-maintained Python wrapper: https://github.com/reteps/redfin
- Third-party scraping services exist but raise legal concerns

---

## C4. Other Property Record APIs

### Pubrec/PropMix
- **URL**: https://pubrec.propmix.io/
- 151M+ US properties
- Parcel, assessment, transactional county data
- 15+ years of historical data
- **Cost**: Paid (contact for pricing)

### First American Data & Analytics
- **URL**: https://dna.firstam.com/api
- Enterprise property data API
- **Cost**: Paid (enterprise pricing)

### County Open Data Portals (Free but Fragmented)
- Some counties offer free electronic records (e.g., Sacramento County, LA County)
- No standardized API across counties
- Would require building individual integrations per county
- Example: https://assessor.lacounty.gov/open-data-initiative/

---

# D. PEP (POLITICALLY EXPOSED PERSONS) DATABASES

---

## D1. OpenSanctions (Best Free/Open Option)

| Field | Detail |
|-------|--------|
| **URL** | https://www.opensanctions.org/ |
| **API** | https://api.opensanctions.org |
| **Cost** | FREE for non-commercial use; Paid for business ($0.10/API call or data license) |
| **Free Trial** | 30-day trial API key with business email |
| **Format** | REST API, JSON; also bulk downloads (JSON, CSV) |
| **Auth** | API key (register at opensanctions.org) |
| **Source Code** | https://github.com/opensanctions/opensanctions (MIT License) |

### PEP Coverage
- Identifies and classifies political positions in national, international, and regional governments
- Tracks individuals currently holding those positions
- Multiple source datasets aggregated

### Additional Data (Beyond PEPs)
- **US SAM Exclusions**: https://www.opensanctions.org/datasets/us_sam_exclusions/
- **US HHS OIG Exclusions**: https://www.opensanctions.org/datasets/us_hhs_exclusions/
- **World Bank Debarred Providers**: https://www.opensanctions.org/datasets/worldbank_debarred/
- **Interpol Red Notices**: https://www.opensanctions.org/datasets/interpol_red_notices/
- International sanctions lists from multiple countries

### API Capabilities
- **Search API**: Query the database by name, entity type, etc.
- **Matching API**: Entity matching/deduplication against the database
- **Batch screening**: Check multiple entities against all lists at once

### Self-Hosting Option
- Open source; can download entire dataset and run locally
- Eliminates per-call costs
- Requires infrastructure to maintain and update

---

## D2. World Bank Debarment List

| Field | Detail |
|-------|--------|
| **URL** | https://www.worldbank.org/en/about/unit/sanctions-system/osd/brief/gsd-directory-2025 |
| **Cost** | FREE |
| **API** | NO dedicated API for debarment list |
| **Format** | Downloadable list (via website) |

### Access Methods
- Download directly from World Bank website
- Better option: Access via OpenSanctions (already aggregated): https://www.opensanctions.org/datasets/worldbank_debarred/
- IDB (Inter-American Development Bank) also publishes sanctions data with cross-debarment info: https://data.iadb.org/dataset/dataset-of-sanctioned-firms-and-individuals

### What It Covers
- Companies and individuals debarred from participating in World Bank-financed contracts
- Includes cross-debarment from other multilateral development banks

---

## D3. Interpol Red Notices

| Field | Detail |
|-------|--------|
| **URL** | `https://ws-public.interpol.int/notices/v1/red` |
| **Web Search** | https://www.interpol.int/en/How-we-work/Notices/Red-Notices/View-Red-Notices |
| **Cost** | FREE |
| **Format** | REST API, JSON |
| **Auth** | NONE required for basic public searches |
| **Rate Limit** | Not officially documented; practical limit of 160 results per query |

### Endpoints
- `GET /notices/v1/red` -- Search/filter Red Notices
- `GET /notices/v1/red/{noticeID}` -- Get specific Red Notice details
- `GET /notices/v1/red/{noticeID}/images` -- Get associated images

### Search Parameters
- `forename`, `name` -- first/last name
- `nationality`
- `ageMax`, `ageMin`
- `freeText`
- `arrestWarrantCountryId`
- `page`, `resultPerPage`

### Limitations
- Only ~30% of Interpol data is publicly accessible
- Maximum 160 results per search query (hard cap regardless of pagination)
- Data updated hourly
- Anti-bot measures (User-Agent validation)
- Intended for public viewing; heavy automated use may be blocked

### Alternative Access
- OpenSanctions aggregates Interpol Red Notices: https://www.opensanctions.org/datasets/interpol_red_notices/
- GitHub community tools: https://github.com/bundesAPI/interpol-api

---

## D4. Other Free PEP/Sanctions Screening Tools

### OpenScreening (Linkurious)
- **URL**: https://resources.linkurious.com/openscreening
- Free access to sanctions lists + PEP databases
- Sources: ICIJ Offshore Leaks, OpenSanctions, OpenOwnership
- Web-based tool (not an API)

### PepChecker
- **URL**: https://pepchecker.com/
- 10 free PEP searches
- API available (paid)

### dilisense
- **URL**: https://dilisense.com/en
- Free trial for sanctions screening + PEP checks
- Includes OFAC SDN list screening

---

# E. SOCIAL MEDIA

---

## E1. X (Twitter) API

| Field | Detail |
|-------|--------|
| **URL** | https://developer.x.com/ |
| **Format** | REST API v2, JSON |
| **Auth** | OAuth 2.0 + API key (Bearer token) |

### Pricing Tiers (Current as of early 2026)

| Tier | Cost | Read Access | Write Access |
|------|------|-------------|--------------|
| **Free** | $0 | Essentially NONE (~1 req/15min) | 500 posts/month |
| **Basic** | $200/month | 10,000 tweets/month | 3,000 posts/month |
| **Pro** | $5,000/month | 1,000,000 tweets/month | 300,000 posts/month |
| **Enterprise** | $42,000+/month | Custom | Custom |

### What's Available for Vetting
- **Free tier**: USELESS for vetting (write-only, essentially no read access)
- **Basic ($200/mo)**: User lookup by username or ID, tweet search (limited), basic user profile data
- **Pro ($5,000/mo)**: Full search API, full archive search, user lookup, tweet counts
- User search, tweet search, profile data retrieval all require at minimum the Basic tier

### Pay-Per-Use Pilot (Feb 2026)
- Credit-based system; pay only for requests made
- Still in closed beta as of early 2026
- Could reduce costs for low-volume vetting

### Practical Assessment for Vetting
- Minimum viable: **Basic tier at $200/month** for user lookups and basic tweet search
- Full search capability requires Pro at $5,000/month
- Consider third-party alternatives for cost savings

---

## E2. LinkedIn API

| Field | Detail |
|-------|--------|
| **URL** | https://developer.linkedin.com/ |
| **Cost** | FREE (if approved as partner) but approval is required |
| **Format** | REST API, JSON |
| **Auth** | OAuth 2.0 |

### Critical Limitation for Vetting
- **You CANNOT look up arbitrary public profiles without user consent**
- All profile access requires explicit OAuth authorization from the profile owner
- Must be an approved LinkedIn Partner to access most APIs
- LinkedIn strictly prohibits scraping and automated data collection

### What Partners Can Access (With User Consent)
- Profile API: name, headline, location, profile photo
- Connections API (with user permission)
- Company Pages API

### Practical Assessment for Vetting
- **NOT viable for unilateral vetting** -- you cannot look up a person's LinkedIn profile without their cooperation
- Only useful if the vetting target provides their own LinkedIn OAuth authorization
- No legitimate programmatic way to search LinkedIn profiles for vetting purposes

---

## E3. Meta (Facebook/Instagram) Graph API

| Field | Detail |
|-------|--------|
| **URL** | https://developers.facebook.com/docs/graph-api |
| **Cost** | Free (with approved app) |
| **Auth** | OAuth 2.0, App Review required |

### Current Capabilities
- Pages Search API: Search public Facebook Pages
- Profile data: Extremely restricted since Cambridge Analytica (2018)
- Public Page data: Name, category, description, follower counts
- NO ability to search/lookup individual user profiles programmatically

### Content Library API (Research Access)
- Available to qualified researchers
- Broader access to public content
- Requires application and approval

### Practical Assessment for Vetting
- **NOT useful for individual person vetting** via official API
- Can search public business Pages (useful if vetting entities/companies)
- Individual profile lookup is not available through official channels

---

## E4. Social Media Aggregator APIs

### Data365
- **URL**: https://data365.co/
- **Platforms**: Instagram, TikTok, YouTube, LinkedIn, Facebook, X
- **Cost**: Paid (pricing via consultation)
- **Format**: JSON
- Unified API for cross-platform data retrieval
- Focus on data retrieval and analytics

### Ayrshare
- **URL**: https://www.ayrshare.com/
- **Platforms**: 15+ platforms (LinkedIn, Facebook, Instagram, X, TikTok, YouTube, Pinterest, Reddit, Telegram)
- **Cost**: Paid tiers starting at ~$15/month
- Primary focus is posting/scheduling, not search/lookup

### Meltwater
- **URL**: https://www.meltwater.com/
- **Cost**: Enterprise pricing (thousands/month)
- Social listening and media intelligence
- Real-time monitoring, export, and streaming endpoints
- Best suited for ongoing monitoring rather than point-in-time lookup

### SerpApi (Facebook/Social Search)
- **URL**: https://serpapi.com/
- Can scrape public social media profiles from search engine results
- **Cost**: Starts at $50/month
- Returns structured JSON from search results

---

## E5. Practical Social Media Summary for Vetting

| Platform | Can You Search/Lookup People? | Min Cost | Practical? |
|----------|-------------------------------|----------|-----------|
| X/Twitter | Yes, with Basic tier | $200/month | Moderate |
| LinkedIn | NO (requires subject's consent) | N/A | No |
| Facebook | NO (individual profiles blocked) | N/A | No |
| Instagram | Limited via Meta API | Approved app | Minimal |
| TikTok | Limited public data | Via aggregator | Minimal |

**Bottom line**: For social media vetting, X/Twitter Basic ($200/mo) is the only major platform with legitimate, affordable programmatic access for looking up individuals without their consent.

---

# RECOMMENDED PRIORITY STACK FOR MVP

Based on cost, coverage, and ease of integration:

## Tier 1: Free / Immediate (Should implement first)
1. **SAM.gov Exclusions API** -- Free, REST API, covers federal debarment
2. **SAM.gov Entity Management API** -- Free, REST API, entity integrity info
3. **CourtListener/RECAP API** -- Free, REST API, bankruptcy metadata
4. **OpenSanctions** (self-hosted or non-commercial API) -- PEPs, sanctions, debarments from multiple sources in one place
5. **Interpol Red Notices API** -- Free, no auth required, public notices
6. **OFAC SDN List** -- Free download, parse locally (or use Moov watchman)
7. **HHS OIG LEIE** -- Free download, parse locally

## Tier 2: Low Cost
8. **PACER PCL API** -- $0.10/page, waived if <$30/quarter (for cases not in CourtListener)
9. **X/Twitter Basic** -- $200/month for user lookups and tweet search

## Tier 3: Paid / As Needed
10. **ATTOM Data** -- ~$95-500+/month for property records
11. **OpenSanctions commercial license** -- $0.10/API call for business use
12. **BankruptcyWatch or UniCourt** -- For comprehensive bankruptcy data beyond CourtListener

## Not Recommended for This Use Case
- Zillow API (too restrictive to obtain)
- Redfin (no public API)
- LinkedIn API (cannot look up people without consent)
- Facebook/Instagram API (cannot look up individual profiles)
