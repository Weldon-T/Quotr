# Quotr Test Plan and Release Management v0.7

**Date**: 2026-08-03
**Environment**: test.quotr.ai
**Based on**: Product exploration of the live test site (login, 4 modules, 15+ API endpoints, localStorage structure)

---

## Table of Contents

1. [Product Understanding](#1-product-understanding)
2. [Test Strategy by Type](#2-test-strategy-by-type) (16 sub-sections: functional, security, payment, compatibility, a11y, migration, concurrency, AI, performance)
3. [Test Execution System](#3-test-execution-system)
4. [Quality Assurance System](#4-quality-assurance-system)
5. [PR Test Management](#5-pr-test-management)
6. [Release Gate](#6-release-gate)
7. [Automation Framework](#7-automation-framework)
8. [Product and Delivery](#8-product-and-delivery)

---

## 1. Product Understanding

### 1.1 Technology Stack

| Layer | Technology | Verified |
|-------|-----------|----------|
| Frontend | React SPA + Ant Design v5 + React Router v6 | Yes |
| Auth | Supabase Auth JWT, stored in localStorage | Yes |
| API | POST-based (non-RESTful), uniform response `{code, message, data}` | Yes |
| Monitoring | Sentry (error tracking) + Amplitude (session replay/analytics) | Yes |
| CDN | Cloudflare, static assets under `/quort_static/` | Yes |

### 1.2 localStorage Key Fields

| Key | Content | Test Focus |
|-----|---------|------------|
| `auth_v2_session` | JWT access token (object) | Must exist after login; expiry handling |
| `token` | JWT raw token (string) | Synced with auth_v2_session |
| `user` | User profile JSON (id, email, org_owner, etc.) | Field completeness |
| `organization` | Current org ID (e.g., "384") | Multi-org switching correctness |
| `quotr_onboarding_state` | Onboarding progress | New user flow should not freeze |
| `selectedTemplate` | Current template type (material/room) | Template module dependency |
| `quotr:last-workspace-org-id` | Last workspace ID | Cross-session recovery |

### 1.3 API Endpoint Map

> Note: This list is based on browser network traffic capture during exploration. It includes only observed API calls. Create/update/delete endpoints likely exist but were not observed. Obtain the full API spec (Swagger/OpenAPI) after onboarding.

**Auth:**
| Endpoint | Method | Purpose | Risk |
|----------|--------|---------|------|
| `/api/auth/v2/signin` | POST | Login, returns JWT | P0 — login failure = all-site unavailable |
| `/api/auth/v2/sign-out-reason` | POST | Log sign-out reason | Monitor: unexpected calls may clear session |

**Org & Projects:**
| Endpoint | Method | Purpose | Risk |
|----------|--------|---------|------|
| `/api/query-org` | POST | Query org info | P0 — **failure = Dashboard white screen** |
| `/api/get-projects` | POST | Project list | P0 — core data source |
| `/api/get-versions` | POST | Estimation versions | P1 |
| `/api/get-roomTypes` | POST | Room type data (by building type) | P1 |

**Templates & Suppliers:**
| Endpoint | Method | Purpose | Risk |
|----------|--------|---------|------|
| `/api/get-customer-templates` | POST | Custom templates | P2 |
| `/api/get-default-templates` | POST | System templates | P2 |
| `/api/get-customer-supplier-list` | POST | Supplier list | P1 |

**Collaboration & Notifications:**
| Endpoint | Method | Purpose | Risk |
|----------|--------|---------|------|
| `/api/qms/v1/meetings` | GET | Meeting list | P2 |
| `/api/qms/v1/bell` | GET | Notification bell | P2 |
| `/api/get-unread-count` | POST | Unread message count | P2 |

### 1.4 Module Navigation

```
/dashboard/project          → Project management (main workspace)
/dashboard/project/{id}     → Project detail (currently returns 404)
/dashboard/database         → Material/cost database
/dashboard/template         → Template management (Material / Room)
/dashboard/suppliers/manage → Supplier management (Manage / RFQ / Quotes)
```

### 1.5 Existing Test Data

| Resource | Details |
|----------|---------|
| Project | `test_pro1` (id: 703, Singlefamily House, zip: 00000) |
| Estimation | `test_est1` (id: 3434, Economy quality, Residential, PDF: 1.png) |
| Supplier | `test_sup1` (CS0126, Electrical trade, contact: aabb@ccdd.com) |
| Custom Templates | None |
| Organization | id: 384 (trial_eligible: false) |

### 1.6 Top Quality Risks (by impact)

1. **`/api/query-org` failure** — Dashboard white screen, equivalent to full outage
2. **AI "high-confidence errors"** — Model outputs wrong estimates with high confidence, users act on them
3. **Data persistence failure** — Hours of estimation work lost
4. **IDOR / unauthorized access** — User A accesses User B's financial data (quotes, estimates), leading to business data leaks
5. **Cross-module data inconsistency** — Project → Database → Template → Procurement data chain breaks
6. **Anti-bot false positives** — Legitimate users blocked, SPA renders blank; also breaks CI pipeline
7. **Stripe payment disruption** — Subscription creation/renewal failure, direct revenue impact

---

## 2. Test Strategy by Type

### 2.1 Module Overview

| Module | Status | Key Risks | Priority |
|--------|--------|-----------|----------|
| **Project** | API returns data but list doesn't render rows; no "New Project" entry; `/project/703` → 404 | Unusable | P0 |
| **Database** | **Bug**: renders only sidebar, main content area empty | Completely unusable | P0 |
| **Template** | Normal: Material/Room tabs, New Template & Example buttons | CRUD correctness | P1 |
| **Suppliers** | Normal: 3 tabs, Add New Supplier, has test data | CRUD + data sync | P1 |
| **Auth** | Login API OK but SPA rendering unstable (anti-bot); sign-out-reason anomaly | Login stability | P0 |

### 2.2–2.8 Module Test Strategies (Project, Database, Template, Suppliers, Auth, Empty State, API)

Each module follows this test pattern:

| Scenario | Method | Priority |
|----------|--------|----------|
| Page loads without white screen | Navigate → verify `is_white_screen()` = False | P0 |
| API returns 200 | Browser fetch → verify status + response format | P0 |
| Content renders correctly | Verify tables/tabs/buttons visible | P0 |
| CRUD operations | Create → read → update → delete → verify list | P1 |
| Empty state handling | Delete all → verify empty guidance UI | P2 |

**Known Bugs Monitored:**
- Database: `is_bug_nav_bar_only` property detects the blank content area
- Project: detail route returns 404 (test skipped), no create button visible (test skipped)

### 2.9 Security Testing

**Auth & Authorization:**
| Scenario | Method | Priority |
|----------|--------|----------|
| IDOR — cross-user project access | Use User A's token to request User B's project → expect 403/404 | P0 |
| IDOR — cross-org data access | Modify org_id in API body → expect rejection | P0 |
| Unauthenticated API access | Call all protected endpoints without token → expect 401 | P0 |
| JWT tampering | Modify token payload (role, org_id) → expect rejection | P0 |
| Token replay | Use logged-out token → expect rejection | P1 |
| Weak password policy | Verify minimum length, complexity requirements | P1 |

**Frontend Security:**
| Scenario | Method | Priority |
|----------|--------|----------|
| localStorage XSS risk | Audit CSP headers, input escaping, 3rd-party script isolation | P0 |
| XSS — project name injection | `<script>alert(1)</script>` in name field → verify escaped | P1 |
| XSS — supplier field injection | Script tags in supplier name/email/address → verify escaped | P1 |
| Sensitive info leak | Review API responses for password hashes, internal IDs, debug info | P1 |
| File upload security | Upload non-image as .png → verify MIME type and file header validation | P1 |

**API Security:**
| Scenario | Method | Priority |
|----------|--------|----------|
| Rate limiting | Rapid requests to same API → verify 429 or throttle response | P1 |
| SQL injection | Inject SQL fragments in search/filter → verify parameterized queries | P1 |
| Large file DoS | Upload 500MB+ file → verify size limit enforced | P2 |

### 2.10 Payment Testing

System integrates Stripe (`stripe_customer_id` field).

| Scenario | Method | Priority |
|----------|--------|----------|
| Subscription creation | Select plan → Stripe test card → verify activation | P0 |
| Subscription upgrade/downgrade | Change tier → verify prorated billing → verify feature access | P1 |
| Subscription cancellation | Cancel → verify correct termination at period end → verify data retention | P1 |
| Payment failure | Stripe decline card (4000000000000002) → verify friendly error → verify not activated | P1 |
| Invoice generation | Verify invoice details (amount, period, company) match actual | P1 |
| Trial expiration | Expired trial → verify paywall guidance → verify data intact | P1 |
| Stripe Webhook | Simulate payment_intent.succeeded/failed, subscription.deleted → verify system response | P1 |

### 2.11 Compatibility Testing

**Browsers:**
| Browser | Method | Priority |
|---------|--------|----------|
| Chrome (latest) | Full regression | P0 (baseline) |
| Edge (latest) | Smoke + core flows | P1 |
| Firefox (latest) | Smoke + core flows | P1 |
| Safari (macOS + iOS) | Login + Dashboard + drawing view | P1 |
| Anti-bot compatibility | All above browsers login without false-positive blocking | P1 |

**Devices:**
| Device | Method | Priority |
|--------|--------|----------|
| iPad (1024×768 landscape + portrait) | Login → project list → drawing view → pinch zoom | P1 |
| Laptop (1440×900) | Baseline resolution, full testing | P0 |
| Large display (1920×1080) | Verify no layout distortion | P2 |

**OS:** Windows 10/11 (P0 baseline), macOS (P1), iOS Safari (P1).

### 2.12 Accessibility Testing

ADA compliance for US market.

| Scenario | Method | Priority |
|----------|--------|----------|
| Keyboard navigation | Tab/Shift+Tab through all interactive elements → Enter/Space activate → Escape close → no keyboard traps | P1 |
| Focus management | Modal open → focus moves in; close → focus returns; page switch → focus to content | P1 |
| Screen reader | NVDA (Windows) / VoiceOver (macOS): nav readable, form labels correct, errors perceivable | P1 |
| Color contrast | Key text ≥ 4.5:1 (WCAG AA) | P2 |
| Alt text | Icon buttons have `aria-label`, drawings have reasonable `alt` | P2 |
| Form accessibility | All inputs have `<label>` or `aria-labelledby`, required fields marked, errors via `aria-describedby` | P1 |

Automated via `@axe-core/playwright`; manual screen reader/keyboard verification for new features.

### 2.13 Data Migration Testing

| Scenario | Method | Priority |
|----------|--------|----------|
| Migration syntax | Dry-run in staging → verify no syntax errors | P0 |
| Data integrity | Pre-migration row count + checksum → post-migration comparison → verify no loss | P0 |
| Business logic | Spot-check migrated data: defaults reasonable, NOT NULL filled, foreign keys valid | P0 |
| Rollback | Run rollback → verify schema and data restored | P1 |
| Backward compatibility | Old code can read/write after migration (for canary deploys) | P1 |

### 2.14 Concurrency Testing

| Scenario | Method | Priority |
|----------|--------|----------|
| Concurrent project edit | Two users edit same estimate → later saver gets conflict warning or merge | P1 |
| Concurrent supplier edit/delete | User A editing while User B deletes → A gets clear error | P1 |
| API idempotency | Send same create request twice rapidly → no duplicate data | P1 |
| Double-click prevention | All submit buttons → disable on click → no duplicate records | P1 |

### 2.15 AI Model Testing

Quotr's core value is AI drawing parsing and estimation. The AI pipeline:

```
Drawing → AI Parsing (element detection/classification/counting) → Retrieve cost data (Database) → Generate estimate
         └── Vision + NLP ──┘                   └── RAG ──┘           └── Structured output ──┘
```

#### Evaluation Tool Matrix

| Stage | Tool | Evaluates | Usage |
|-------|------|-----------|-------|
| Element detection | Structured comparison (P/R/F1) | Element type, count, position correctness | JSON output vs ground truth field-by-field |
| Text semantics | **BERTScore** | Material names, room descriptions semantic similarity to human labels | `bert-score` library: F1 on text pairs |
| Retrieval quality | **RAGAs** — Context Relevance | Whether retrieved cost data is relevant to drawing elements | Score each retrieval against query |
| Generation trustworthiness | **RAGAs** — Faithfulness | Whether estimates are grounded in retrieved data (not "made up") | Decompose estimate into atomic claims, verify each |
| Output completeness | **RAGAs** — Answer Relevance | Whether estimate fully answers "how much does this drawing cost" | Semantic coverage vs expected estimate |
| Structured output | JSON Schema validation | Ensure output consumable by downstream systems | `jsonschema` library |

#### Metrics Summary

| Tool | Metric | GO Range | NO-GO Red Line |
|------|--------|----------|----------------|
| Structured | Detection F1 | Degradation ≤ 2% | Drop > 5% |
| Structured | Quantity error | ≤ 10% | > 20% |
| Structured | Schema compliance | 100% | Non-100% → Block |
| BERTScore | Text semantic F1 | ≥ 0.90 | < 0.85 |
| RAGAs | Context Relevance | ≥ 0.85 | < 0.75 |
| RAGAs | Faithfulness | ≥ 0.90 | < 0.80 |
| RAGAs | Answer Relevance | ≥ 0.85 | < 0.75 |
| Business | Total cost error | ≤ 10% | > 20% |

#### Implementation (`tests/ai/test_baseline.py`)

`AIBaselineEvaluator` — Class-based evaluator, independent of pytest:
- `load_samples(baseline.json)` → load Golden Baseline sample set
- `run_ai_pipeline(drawing_path)` → invoke AI pipeline (pending API access)
- `evaluate_structured(output, gt)` → (f1, qty_error, schema_ok)
- `evaluate_bertscore(preds, refs)` → float
- `evaluate_ragas(questions, contexts, answers, gts)` → (cr, faith, ar)
- `summary()` → human-readable report

Dependencies: `pip install bert-score ragas datasets`. Falls back gracefully (-1) if not installed.

### 2.16 Performance Verification

#### Benchmarks

| Scenario | Metrics | Method |
|----------|---------|--------|
| Drawing upload + parsing | P50/P95/P99 total time | Fixed test drawing set, Playwright wall-clock measurement |
| API concurrency (100 req) | P95, RPS, error rate | Locust or k6, staging environment |
| Dashboard first paint | FCP, LCP | Playwright Performance API or Lighthouse CI |
| Proposal export | P95 generation time, file size | Playwright trigger export, measure response |

#### Criteria

- "Faster": P95 drops ≥ 10%
- "Slower": P95 rises ≥ 5%
- Average of 3 runs per version
- Optimization PRs must pass functional regression before benchmarking

#### Implementation (`tests/performance/`)

- `LatencyCollector`: warmup → 20 rounds → P50/P95/P99 → baseline comparison → degradation alerts
- `measure_page_load()`: Playwright Performance API collects FCP/LCP per Dashboard page
- Baselines stored as JSON (`latency_baseline.json`, `rendering_baseline.json`)
- Not a weekly RC blocking gate; results inform the Release Readiness report

---

## 3. Test Execution System

### 3.1 Release Stage Trigger Model

Tests are organized by release stage, not by weekday:

```
PR Submit → Merge to main → Nightly → Release Candidate → Release
   │            │              │             │                │
   ▼            ▼              ▼             ▼                ▼
Pre-merge    Post-merge      Daily      Pre-Release       Release Day
 (auto)       (auto)        (auto)     (auto+manual)     (manual confirm)
```

### 3.2 Pre-Merge (Per PR, Fully Automated)

Trigger: PR submit / update

| Test | Content | Tool | Duration |
|------|---------|------|----------|
| Lint / Type Check | Code standards, type safety | ESLint, tsc, mypy | < 1min |
| Unit Test | Pure functions, utils, API handlers | Jest, pytest | < 2min |
| L0 Smoke | Login success/failure, 4 nav accessible, `/api/query-org` 200, localStorage integrity | Playwright | ~10min |
| Security headers | CSP, HSTS, X-Frame-Options presence | Playwright | < 30s |
| Dependency vuln scan | New dependencies have known CVEs? | `pip audit` / `npm audit` | < 1min |

QA role: CI failure → block merge. No manual intervention.

Gate: all must pass before merge.

### 3.3 Post-Merge / Nightly (Daily, Fully Automated)

Trigger: 3:00 UTC daily, or main branch new commit

| Test | Content | Tool | Duration |
|------|---------|------|----------|
| L1 Critical Path | L0 all + basic CRUD + API contract tests | Playwright | ~30min |
| Security full suite | IDOR, unauth access, JWT tampering, XSS injection | Playwright | ~8min |
| A11y scan | WCAG violation detection on all key pages | `@axe-core/playwright` | ~5min |
| Compatibility smoke | Chrome/Edge/Firefox + iPad viewport: login + nav | Playwright (multi-project) | ~15min |
| Concurrency basics | API idempotency, double-submit prevention | Playwright | ~5min |

QA role: 10am review report. Failures → investigate environment vs real regression → file bug if real.

### 3.4 Pre-Release (RC, Auto + Manual)

Trigger: Dev confirms "RC ready" (typically Wednesday)

#### Automatic

| Test | Content | Duration |
|------|---------|----------|
| L2 Full Regression | All module full scenarios + cross-module data flows + empty states | ~2.5h |
| AI Baseline auto-eval | Structured F1 + quantity/cost error + BERTScore + RAGAs (CR/Faith/AR) | ~3h (parallel with L2) |
| Performance baseline | API latency (P50/P95/P99 + degradation) + Dashboard FCP/LCP | ~15min |
| Security full regression | Full security suite | ~8min |
| A11y full | WCAG scan for new/changed pages | ~8min |
| Compatibility full | Chrome/Edge/Firefox/Safari + iPad core flows | ~20min |
| Payment Webhook | Stripe test mode event replay | ~5min |
| Concurrency full | Concurrent edits, supplier conflicts, template usage | ~8min |

> Heavy-load benchmarks (large file upload, stress test) are on-demand — triggered by architecture changes or quarterly audits only.

#### Manual (cannot be automated)

| Test | Why Manual | Duration |
|------|-----------|----------|
| Exploratory testing | Automation only verifies known paths | 1-2h |
| AI output quality review | Machine reports deviation %, human judges acceptability | 1h |
| Screen reader verification | axe-core detects only ~30% of a11y issues | 30min |
| Visual/UX review | Automation doesn't do pixel-level judgment | 30min |
| Payment E2E (manual) | Full card interaction flow needs human confirmation once | 15min |
| Keyboard navigation | Focus management logic needs human verification | 15min |
| Migration data spot-check | Checksum pass doesn't guarantee business logic correctness | 15min |

### 3.5 Release Day (Thursday, Confirm + Decide)

Goal: no new testing — only verify known fixes + confirm automation results + release decision.

| Activity | Auto/Manual | Duration |
|----------|-------------|----------|
| Nightly report review | Auto (QA reads) | 10min |
| Security smoke (P0 subset) | Auto | 2min |
| Bug fix re-verification | Manual | 30-60min |
| Migration formal validation (if any) | Auto + manual spot-check | 15min |
| Release Readiness Checklist | Manual | 30min |
| Release Meeting | — | 1h |
| Post-deploy monitoring (Sentry 30min) | Auto (QA watches dashboard) | 30min |

### 3.6 Auto vs Manual Overview

14 of 22 test types automated (~64%). Manual tests focus on areas requiring human judgment.

| Type | Auto | Manual | Frequency |
|------|:----:|:------:|-----------|
| L0 Smoke | ✅ | — | Per PR |
| Unit Test | ✅ | — | Per PR |
| Security headers | ✅ | — | Per PR |
| Dependency vulns | ✅ | — | Per PR |
| L1 Critical Path | ✅ | — | Daily |
| Security full | ✅ | — | Daily |
| A11y scan | ✅ | — | Daily |
| Compatibility smoke | ✅ | — | Daily |
| Concurrency basics | ✅ | — | Daily |
| L2 Full Regression | ✅ | — | RC trigger |
| Payment Webhook | ✅ | — | RC trigger |
| Concurrency full | ✅ | — | RC trigger |
| AI Baseline auto-eval | ✅ | — | RC trigger |
| Performance baseline | ✅ | — | RC trigger |
| Migration exec + checksum | ✅ | — | RC / Release day |
| Exploratory testing | — | ✅ | RC |
| AI output quality review | — | ✅ | RC |
| Screen reader | — | ✅ | RC |
| Visual/UX review | — | ✅ | RC |
| Payment E2E (manual) | — | ✅ | RC |
| Keyboard navigation | — | ✅ | RC |
| Migration data spot-check | — | ✅ | Release day |
| Bug fix re-verification | — | ✅ | Release day |

---

## 4. Quality Assurance System

### 4.1–4.7 (PR tracking, regression strategy, bug verification, data management, flaky prevention, human error prevention)

Key points:

**PR Impact Declaration** (developer must fill):
- Change type: New feature / Bug fix / Refactor / Config / **Security fix**
- Modules affected: Frontend / Backend / DB / AI / **Payment (Stripe)** / **Auth/Permissions**
- Data migration needed: Yes / No (if Yes → attach migration + rollback scripts + staging execution screenshot)
- New API added: Yes / No (if Yes → must add IDOR test case)
- Payment involved: Yes / No (if Yes → must verify in Stripe test mode)
- Suggested test scope

**Regression Strategy by PR Type:**
- New feature → Full regression + security baseline
- Core module bug fix → Full regression + security baseline
- Security fix → **Full security regression** + core smoke
- Payment change → Full payment regression + core smoke
- Auth/permission change → Full regression (full permission matrix)
- Non-core bug fix → Local regression + smoke
- Data migration → Migration validation + smoke
- Refactor → Local regression + auto smoke
- Config change → Local verification + smoke
- Dependency upgrade → Full regression + security scan

**Flaky Prevention:**
- Auto-retry 3x (pass any = pass, but mark flaky)
- Same case flaky 3 consecutive builds → `@pytest.mark.flaky` isolation
- Weekly flaky triage, fix within 2 weeks

**Test Data & Environment:**
- Credentials in `.env`, zero hardcode, `.gitignore` excluded
- Versioned fixture files for reproducibility
- Multi-account needed for IDOR and concurrency tests (request after onboarding)
- Known limitation: Project creation broken, Database blank — automated tests handle these with conditional skips

---

## 5. PR Test Management

- PR Status: `not_started` → `in_progress` → `verified` → `blocked`
- Core path PRs: must include or update automation cases
- Bug fix PRs: must add regression case to prevent recurrence
- Changes > 100 lines without automation → reject, request coverage
- Unclear PRs: comment with missing scenarios; blocking → reject; dev insists → Risk Acceptance

---

## 6. Release Gate

### 6.1 GO Conditions

| Dimension | Condition |
|-----------|-----------|
| Function | P0 pass rate = 100%; P1 ≥ 98% |
| Performance | P99 ≤ baseline × 1.1; error rate ≤ 0.05% |
| AI | All metrics within GO range defined in 2.15 |
| Bugs | No open P0; P1 fixed or signed off |
| Regression | Core regression checklist 100% |
| PRs | All release PRs verified or signed off |
| API | `/api/query-org` 200, P95 < 500ms |
| Sentry | 30min post-release, new error rate ≤ baseline × 1.5 |
| Dashboard | 4 nav items all clickable, no white screen |
| localStorage | `auth_v2_session` / `user` / `organization` correctly written |
| Security | No P0 vulns; IDOR tests pass; CSP header configured |
| Payment | Stripe subscription create/cancel Webhook verified in test mode |
| Migration | If applicable: staging success + data integrity + rollback verified |

### 6.2 NO-GO (Block Release)

- Any open P0 bug
- ≥ 1 open P1 without sign-off
- Core flow automation pass rate < 95%
- Any AI metric hits 2.15 NO-GO red line
- Data loss or corruption
- Payment/permission errors
- `/api/query-org` not 200
- Dashboard white screen or core nav broken
- Any IDOR vulnerability
- Unauthenticated access to protected API
- Migration script fails in staging
- Stripe core payment flow (subscription create/Webhook) broken

### 6.3 Bug Severity Levels

| Level | Definition | Examples |
|-------|-----------|----------|
| **P0** | Core function unavailable; data loss/corruption; security vuln | Cannot login, Dashboard white screen, `/api/query-org` failure, Database module blank, cannot create project |
| **P1** | Core function works but severe defect | Estimation error > 20%, export data missing, token anomaly |
| **P2** | Non-core defect, workaround exists | UI misalignment, unhelpful error message |
| **P3** | Minor | Typo, color deviation |

---

## 7. Automation Framework

### 7.1 Technology: Playwright + Pytest

- React SPA: Playwright natively supports React async render waiting
- `page.evaluate()` for direct localStorage JWT assertions
- Pytest fixture/conftest for auth state reuse
- Cross-platform (Windows/macOS/Linux)
- Single `.venv` dependency management

### 7.2 Test Layers

```
L0 Smoke (per PR, ~10 min)
  ├── Login success / failure (~3min each, anti-bot wait included)
  ├── 4 nav accessible (200 + non-white-screen)
  ├── /api/query-org health check
  └── localStorage key field integrity

L1 Critical Path (daily, ~30 min)
  ├── L0 all
  ├── API contract tests (all known endpoints)
  ├── Security full (IDOR / unauth / JWT / XSS)
  ├── A11y scan (axe-core)
  ├── Compatibility smoke (Chrome/Edge/Firefox + iPad)
  └── Database/Template/Suppliers basic CRUD

L2 Full Regression (RC trigger, ~3h)
  ├── L1 all
  ├── All modules full scenarios + cross-module + empty state
  ├── AI Golden Baseline (BERTScore + RAGAs + structured F1 + Schema)
  ├── Performance baseline (API P50/P95/P99 + Dashboard FCP/LCP)
  └── Payment Webhook / Concurrency full / Compatibility full
```

### 7.3 Directory Structure

```
tests/
├── conftest.py              # Fixtures + pytest hooks for HTML report generation
├── pytest.ini               # Markers: smoke, security, performance, ai, etc.
├── core/                    # Design pattern infrastructure
│   ├── page_factory.py      # Registry: lazy creation + caching of Page Objects
│   └── decorators.py        # @retry / @screenshot_on_failure
├── config/
│   ├── settings.py          # .env reader + WAIT timing constants
│   └── routes.py            # Route constants + localStorage key constants
├── pages/                   # Page Object Model (composition via PageFactory)
│   ├── base_page.py         # goto(), is_white_screen(), ls_get(), screenshot()
│   ├── login_page.py        # login() / login_failure_expected()
│   ├── dashboard_page.py    # Sidebar nav, module traversal
│   ├── project_page.py      # Project list, create entry (partially unavailable)
│   ├── database_page.py     # Database page + bug detection (is_bug_nav_bar_only)
│   ├── template_page.py     # Template CRUD, tab switch, example templates
│   └── procurement_page.py  # Supplier CRUD, tab switch, Edit/Delete
├── api/
│   ├── client.py            # HTTP client + Playwright fetch (bypass anti-bot)
│   └── test_api_contract.py # All known endpoints: response format + unauth 401
├── smoke/                   # L0 — per PR
│   ├── test_login.py        # Login success/failure, token persistence, redirect
│   ├── test_navigation.py   # Nav accessibility + white screen + query-org health
│   └── test_auth_state.py   # localStorage integrity, sign-out-reason anomaly
├── regression/              # L2 — RC trigger
│   ├── test_project.py      # List/create/detail (with known-bug skips)
│   ├── test_database.py     # Bug monitor + CRUD (enabled after fix)
│   ├── test_template.py     # Tab switch, create form, examples, selectedType
│   ├── test_procurement.py  # Supplier list, create, Edit/Delete, 3 tabs
│   └── test_cross_module.py # Cross-module nav sequence, org ID consistency
├── security/
│   ├── test_headers.py      # CSP / HSTS / X-Content-Type-Options / X-Frame-Options
│   ├── test_auth.py         # Unauth 401, empty/garbage/expired token rejection
│   ├── test_xss.py          # XSS payload injection (reflected + stored placeholders)
│   ├── test_idor.py         # Cross-org data access (needs second account)
│   └── test_rate_limit.py   # Consecutive requests shouldn't trigger premature blocking
├── performance/             # API latency + frontend rendering
│   ├── test_api_latency.py  # P50/P95/P99 collection + baseline compare + alerts
│   └── test_rendering.py    # Dashboard FCP/LCP Web Vitals collection
├── payment/                 # Stripe tests (awaiting test mode config)
├── a11y/                    # Accessibility (active, found BUG-006/007 — WCAG violations)
├── migration/               # Migration tests (awaiting staging DB access)
├── concurrency/             # Concurrency tests (awaiting second account)
├── ai/
│   ├── test_baseline.py     # Golden Baseline + BERTScore + RAGAs evaluator
│   └── fixtures/            # baseline_v1.json sample set
├── utils/
│   ├── helpers.py           # human_pause, wait_for_spa, goto_spa, snap, dump_text
│   ├── antd_selectors.py    # Ant Design component helpers
│   ├── reporter.py          # TestReporter: summary(), to_json()
│   └── html_reporter.py     # HtmlReport: auto-generates HTML + Bug KB
├── reports/                 # Auto-generated HTML reports (latest.html + timestamped)
└── fixtures/                # Shared test data
```

### 7.4 Key Design Decisions

**PageFactory (Registry pattern)** — `tests/core/page_factory.py`:
Tests use `app.login.login()` instead of manually instantiating `LoginPage(page)`. All page objects lazily created and cached.

**Decorators** — `tests/core/decorators.py`:
`@retry(times=3)` for anti-bot/network flaky handling; `@screenshot_on_failure` for auto-capture on failure.

**Wait Strategy** — `tests/config/settings.py` `WAIT` constant class:
All timing/throttle values centralized in `WAIT` object. Page objects prefer `wait_for(state="visible/hidden")` over `wait_for_timeout()`.

**HTML Report Auto-generation** — `tests/utils/html_reporter.py`:
`HtmlReport` class collects results via three pytest hooks (`pytest_configure`, `pytest_runtest_makereport`, `pytest_sessionfinish`). Generates self-contained HTML to `tests/reports/` after every run. Includes a Bug Knowledge Base that automatically matches known product bugs (security headers, dashboard redirect, database blank) to failed tests, providing descriptions, impact analysis, and fix suggestions.

**Test Runner (`run_ci.py`) — sole execution entry point:**
- `python run_ci.py` — Full suite, single session, no expiry, with layer tags
- `python run_ci.py --layer smoke` — L0 Smoke (GitHub Actions PR trigger)
- `python run_ci.py --layer critical` — L1 Critical Path (GitHub Actions scheduled)
- `python run_ci.py --layer regression` — L2 Full Regression (GitHub Actions manual)
- Full mode: layers inferred from module paths (smoke→L0, security/api→L1, regression/perf/ai→L2, payment etc.→BLOCKED)
- Single-layer mode: `QUOTR_CI_LAYER` env var tagging, per-layer JSON merge for report
- Output logs: `tests/reports/pytest_*.log`, HTML report: `tests/reports/latest.html`

**CI Integration (production — `.github/workflows/ci.yml`):**
- `pull_request` → L0 Smoke job (~15min timeout)
- `schedule` (daily 3:00 UTC) → L1 Critical Path job (~45min timeout)
- `workflow_dispatch` (manual trigger) → L2 Full Regression job (~240min timeout), selectable layer
- `pull_request` → Dependency audit job (`pip audit`)
- Credentials via GitHub Secrets (`QUOTR_EMAIL`, `QUOTR_PASSWORD`)
- Failure auto-notification via `slackapi/slack-github-action`
- HTML reports uploaded as build artifacts via `actions/upload-artifact`

---

## 8. Product and Delivery

### 8.1 Issue Classification

| Type | Criteria | Handling |
|------|----------|----------|
| **Bug** | Feature not working per spec | File bug, drive fix |
| **UX Issue** | Works but poor experience | Discuss with designer/PM |
| **Product Gap** | Missing feature users need | Feed to PM, roadmap |
| **User Education** | Feature exists but unknown | Suggest docs/tutorials/tooltips |

If a user cannot complete a core task → highest priority regardless of classification.

### 8.2 Speed, Quality, Experience Balance

- P0 must fix, P1 try to fix, P2 can defer
- High-risk new features use Feature Flags, internal-only first, gradual rollout
- Release Meeting makes trade-off explicit: "Ship this week, known risk X; delay, business impact Y"

### 8.3 Reduce Recurring Bugs

- Every P0/P1 fix → ask "why didn't testing catch this" → add automation
- Quarterly bug data review → identify patterns → systemic improvement
- Maintain "Common Issues & Test Strategies" doc

### 8.4 User Feedback Loop

- Suspected bug → reproduce immediately → bug process
- Missing feature → discuss with PM → roadmap
- Adopted feedback: note "Based on user feedback" in Release Notes

---

> **Version**: v0.7 | **Date**: 2026-08-03 | **Next Review**: Quarterly or on major product changes
