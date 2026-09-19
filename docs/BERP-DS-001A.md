# BERP-DS-001A — ERPNext Rebranding Surface Inventory & Override Contract

**Version:** 0.3 — Stage 0 and Stage 1 implemented and verified on the dev bench.
Part D ruled by OP-Vily, 2026-09-19. §D2 corrected on reading both parents in full.
**Status:** Controlled unit. Mandated by BERP-DS-001 §"next controlled unit", which
gates further theme code behind this document.
**Authority:** Subordinate to BERP-CI-001 (brand primitives) and BERP-DS-001
(component system). Where this document and those disagree, §D records the
conflict rather than resolving it unilaterally.
**Scope:** The Frappe Desk and every ERPNext surface rendered inside it. The
authentication surface is already shipped and is treated here as the reference
implementation, not as new scope.
**Measured on:** `dev.berp.bizera.la` (private `berp-linux`), 2026-09-19.
Frappe v16 / ERPNext v16; asset bundles built 2026-09-09.
**Author:** Claude (Cowork) for OP-Vily, BizEra.

---

## 0. Executive summary

The Desk can be rebranded without touching a single file inside `frappe/` or
`erpnext/`. This was not assumed; it was measured.

Three findings decide the architecture.

**The cascade is already ours.** Frappe injects every Desk stylesheet through one
mechanism — the `app_include_css` hook, looped in `desk.html` — and aggregates
that hook across apps in installed order. On the dev bench the resolved list is
`desk.bundle.css, report.bundle.css, erpnext.bundle.css, lao_berp.bundle.css`.
`berp_branding` is the last installed app, so a stylesheet it declares loads
after everything upstream ships. At equal specificity we win on source order,
without `!important` and without forking.

**The majority of the Desk is already variable-driven.** The built desk bundle
carries 2,617 `var()` references against 1,453 hex literals and 181 `rgb()/rgba()`
literals across roughly 6,982 rule blocks, and declares 565 distinct custom
properties across 23 `:root` blocks. Retargeting custom properties is therefore
the primary instrument, not a workaround. Critically, **ERPNext declares zero
custom properties of its own** — it consumes Frappe's. One token layer reaches
both applications.

**The literal tail is real and must be budgeted.** 1,453 hex literals are beyond
the reach of any variable. They are not evenly spread: `#171717` (52), `#7c7c7c`
(50), `#e03636` (30), `#28a745` (28), `#383838` (27) account for the bulk, and
they concentrate in the `espresso/` primitive layer, which holds 282 of the 293
hardcoded values in Frappe's entire SCSS tree. This is the measured size of the
selector-override work, and it is the part that carries upgrade risk.

The contract in §B converts these findings into four permitted tiers and one
prohibition. The sequenced plan in §E puts roughly 80% of the visible Desk change
in Tier 1, where upgrade risk is lowest.

Two defects in the currently shipped branding were found during this inventory
and are recorded in §A7: the legacy `/desk` page still resolves to the **Frappe**
logo, and the `app_logo_url` hook chain would resolve to the **ERPNext** logo if
Website Settings were ever cleared. Both are corrected in §E, Stage 0.

---

## 1. The acceptance criterion, and what it means mechanically

DS-001 sets one non-negotiable test:

> A bERP UI change must survive an ERPNext/Frappe upstream upgrade without
> requiring edits inside the upstream repositories.

Mechanically this forbids four things and permits everything else:

| Forbidden | Why it fails the test |
|---|---|
| Editing any file under `apps/frappe/` or `apps/erpnext/` | Lost on `bench update`; conflicts on every upgrade |
| Copying upstream markup into a bERP template | Upstream changes the markup; the copy silently diverges and keeps rendering the old form |
| Patching upstream SCSS or rebuilding upstream bundles | Overwritten by `bench build`; no provenance |
| Monkey-patching upstream Python at import time | Breaks on signature change, with no compile-time signal |

Everything permitted therefore has to arrive through a published extension point.
§A1 enumerates every such point that exists in this version, measured rather than
recalled.

---

## 2. Method

Every number in this document was read off the running bench on 2026-09-19 via a
scripted probe executed inside `berp-dev-backend-1`. Nothing is quoted from
memory or from documentation. The probe is preserved as
`berp_branding/scripts/recon_desk_surface.sh` so the inventory can be regenerated
after any upstream upgrade and diffed against this baseline — which is the
practical form the acceptance criterion takes as a repeatable test (§C4).

Per REVIEW-METHOD P2, a negative result from any instrument is not trusted until
the instrument has been validated against a known-good case. Two instrument
failures from the preceding session are carried into §C5 as standing warnings,
because both produced confidently wrong conclusions before they were caught.

---

# Part A — Surface Inventory

## A1. Injection points available to `berp_branding`

Measured against Frappe v16 on the dev bench. These are the only sanctioned ways
into the Desk.

| # | Extension point | Kind | Reaches | Cascade position |
|---|---|---|---|---|
| 1 | `app_include_css` | hook (list) | Every Desk page. Looped in `www/desk.html` line 24, inside `<head>` | **Last** — appended after frappe and erpnext |
| 2 | `app_include_js` | hook (list) | Every Desk page. Looped in `desk.html` line 65, end of `<body>` | Last |
| 3 | `app_include_icons` | hook (list) | SVG symbol sprite fetched into `#all-symbols` | Last |
| 4 | `web_include_css` / `web_include_js` | hook | Portal/website only, not the Desk | Last |
| 5 | `website_theme_scss` | hook | Portal only, compiled through the Website Theme DocType | n/a |
| 6 | `app_logo_url` | hook (positional) | Desk navbar, apps screen — **unreliable, see A7** | n/a |
| 7 | `brand_html` | hook | Portal navbar only (`templates/includes/navbar/navbar.html`) | n/a |
| 8 | `add_to_apps_screen` | hook | The apps switcher tile | n/a |
| 9 | `sounds` | hook | Audio elements | n/a |
| 10 | Jinja template override via `www/` | file resolution | Any `www` page; resolved `reversed(get_installed_apps())` | Last app wins |
| 11 | Website Settings fields | **data** | `app_name`, `app_logo`, `favicon`, `splash_image`, `banner_image` | n/a |
| 12 | Navbar Settings `app_logo` | **data** | Legacy `/desk` page (**and only that**, see A7) | n/a |

Points 11 and 12 are data, not code. They survive upgrades unconditionally, which
is why the contract ranks them first.

## A2. Asset pipeline and load order

`desk.html` contains no `<link>` to any stylesheet other than the
`app_include_css` loop and the favicon. Frappe's own `desk.bundle.css` arrives
through the same hook as ours. There is no separate, privileged upstream channel.

Resolved on the bench:

```
installed_apps   : ['frappe', 'erpnext', 'lao_berp', 'berp_branding']
app_include_css  : ['desk.bundle.css', 'report.bundle.css',
                    'erpnext.bundle.css', 'lao_berp.bundle.css']
```

`berp_branding` currently declares none. When it does, its entry appends to the
end of that list.

**Path resolution.** `bundled_asset()` looks a path up in `assets.json` only when
the path contains `.bundle.` and does not start with `/assets`. Anything else is
passed straight through `abs_url()`. Two consequences, both load-bearing:

- A plain file such as `/assets/berp_branding/css/berp_desk.css` **is** a legal
  `app_include_css` value. No esbuild entry is required.
- That path receives **no content hash and no cache-busting query**. A browser
  that has cached it will keep serving the old file after a deploy. This is not
  hypothetical: a stale cache made a corrected SVG keep rendering as a sliver for
  a long stretch of the previous session, and every visual conclusion drawn in
  that window was wrong.

**Therefore the contract requires a real bundle** — `public/scss/*.bundle.scss`,
compiled by `bench build` into a content-hashed file registered in `assets.json`.
The plain-path form is permitted only for the already-shipped `berp_auth.css`,
which is loaded by an explicit `<link>` in a template we control and can version
by hand.

**Deployment hazard, container-specific.** Confirmed during the Stage 1 deploy,
and the mechanism is more specific than first recorded. `/srv/berp/data/dev/sites`
*is* bind-mounted into the frontend, but `sites/assets` is a **symlink** to
`frappe-bench/assets`, which is container-local. Proof: the two containers'
`assets.json` differed in size (3,929 vs 3,745 bytes) while the backend had
`berp_branding/dist/` and the frontend did not.

Two traps follow, both of which cost a deploy cycle here:

- Under `assets/`, each app directory is *itself* a symlink to
  `apps/<app>/<app>/public`. `docker cp` copies the **link**, not the target, so
  the frontend ends up with a dangling symlink and still 404s. Use
  `tar chf -` (`-h` dereferences) and extract inside the container.
- The frontend runs as uid 1000 (`frappe`) while `assets/` is root-owned, so the
  extract needs `docker exec -u root`.

A compose change that shares one assets volume is the durable fix. Until then the
deploy step is: `tar ch` from the backend's `apps/<app>/<app>/public`, `docker cp`
the tarball, extract as root over `assets/<app>`, and copy `assets.json` across.

## A3. The token surface

Frappe v16 carries **two token systems simultaneously**, and this is the single
most important structural fact for bERP.

| Layer | Location | Unique properties | Hardcoded hex | `var()` uses | Role |
|---|---|---|---|---|---|
| `espresso/` | `_colors, _typography, _spacing, _borders, _shadows` | 293 | **282** | 11 | **Primitive layer.** Raw values. `--gray-500: #999999`, `--ink-*`, `--surface-*`, `--outline-*` |
| `common/` | `css_variables.scss` and siblings | 120 | 3 | 543 | **Semantic layer.** Maps primitives to roles: `--control-bg: var(--gray-100)` |
| `desk/` | `css_variables.scss` and 47 siblings | 198 | 29 | 1,322 | **Component layer.** Desk-specific dimensions and states |
| `website/` | `css_variables.scss` | 16 | 4 | 113 | Portal only |
| `element/` | `checkbox, radio` | 0 | 0 | 21 | Pure consumer |

The espresso layer is where the raw colour lives, and it is declared in two
blocks — a `:root` block for light and a `[data-theme="dark"]` block. The
semantic layer is where brand meaning is assigned. **bERP must retarget the
semantic layer, not the primitive layer.** Overwriting `--gray-500` globally
would recolour every neutral in both applications including states that are
deliberately neutral; overwriting `--control-bg` changes exactly the surface that
means "control background".

Built output, which is the ground truth of what is actually served:

```
desk.bundle.RXWII534.css   661,188 bytes
  rule blocks (approx)      6,982
  var() references          2,617
  hex literals              1,453
  rgb()/rgba() literals       181
  distinct custom props       565
  :root blocks                 23
```

## A4. Leverage map — which variables actually do work

Usage counts in the built desk bundle. This is the ranking that should drive
Tier 1 effort; a variable with 1 use is not a theme knob however promising its
name.

| Variable | Uses | Current value | bERP target (proposed) |
|---|---:|---|---|
| `--text-color` | 112 | `var(--gray-900)` chain | Charcoal per CI-001 |
| `--border-color` | 111 | `var(--gray-200)` | Structural neutral |
| `--border-radius` | 109 | upstream | 8px control / see §D2 |
| `--text-muted` | 75 | `var(--gray-600)` chain | **Neutral 500 — see B5.4** |
| `--fg-color` | 49 | `white` | Surface white |
| `--bg-color` | 42 | `white` | Neutral 50 page background |
| `--control-bg` | 41 | `var(--gray-100)` | Control surface |
| `--primary` | 20 | **`#171717`** | **Teal 700 `#117461`** |
| `--heading-color` | 9 | upstream | Charcoal |
| `--sidebar-width` | 7 | upstream | per DS-001 |
| `--font-stack` | 6 | Inter stack | Inter + Noto Sans Lao |
| `--navbar-height` | 6 | 48px | per DS-001 |
| `--primary-color` | 5 | `var(--gray-900)` | Teal 700 |
| `--btn-height` | 5 | 28px | **44 Comfortable / 32 Compact (§D2)** |
| `--sidebar-hover-color` | 5 | upstream | Teal tint |
| `--sidebar-select-color` | 3 | upstream | Teal tint |
| `--btn-primary` | 2 | `var(--gray-900)` | Teal 700 |
| `--input-height` | 2 | 28px | **44 Comfortable / 32 Compact (§D2)** |
| `--control-bg-on-gray` | 2 | `var(--gray-200)` | Control on tinted surface |
| `--navbar-bg` | 1 | upstream | Surface white |
| `--brand-color` | **0** | `var(--primary)` | **Dead — do not spend effort here** |

Two notes with consequences.

`--primary` resolves to `#171717` in the built output but is **declared nowhere
in Frappe's SCSS or CSS source tree**. It arrives from outside the greppable app
tree (vendored `frappe-ui`/espresso build input). Treat it as upstream-owned and
retargetable, but do not expect to find or reason about its declaration site in
the repo.

`--brand-color` is declared (`var(--primary)`) and referenced **zero times** in
the Desk. Its name invites exactly the wrong bet. Setting it accomplishes nothing.

`--text-muted`, at 75 uses, is the fourth-heaviest knob in the Desk and is the
one that decides whether the product passes AA at caption size. It is the exact
pair that failed on the login surface at Neutral 400. It must be set to Neutral
500 or darker and measured, not estimated (B5.4).

`--btn-height` (5), `--input-height` (2) and the two density-bearing dimensions
are deliberately listed even though their use counts are low: they cascade
through Bootstrap-derived rules that consume them indirectly, and they carry the
§D2 density ruling — 44px Comfortable, 32px Compact, selected by a body-level
attribute rather than by a second stylesheet.

## A5. The literal tail — what variables cannot reach

1,453 hex literals in the built bundle are immune to token retargeting. Census of
the top values:

| Hex | Count | What it is | Reachable by |
|---|---:|---|---|
| `#171717` | 52 | gray-900 / near-black | Mostly Tier 1 via `--gray-900`; residue Tier 2 |
| `#7c7c7c` | 50 | gray-600 muted text | Tier 1 / Tier 2 |
| `#e03636` | 30 | danger red | Tier 1 (`--red-*`) where semantic; Tier 2 otherwise |
| `#28a745` | 28 | Bootstrap success green | **Tier 2 only** — Bootstrap vendor residue |
| `#383838` | 27 | gray-800 | Tier 1 / Tier 2 |
| `#e2e2e2`, `#f3f3f3`, `#ededed`, `#c7c7c7` | 75 combined | neutral scale | Tier 1 |
| `#00b2ff` | 18 | accent blue | **Tier 2** — a brand-adjacent colour bERP must replace |
| `#ffc107`, `#17a2b8` | 34 combined | Bootstrap warning / info | **Tier 2 only** |
| `#4a5464` | 10 | slate | Tier 2 |
| `#ffffff`, `#dadada` | 16 combined | white / rule grey | Tier 1 |
| `#999999`, `#525252` | 16 combined | neutral scale | Tier 1 |
| `#efefef`, `#dedede` | 14 combined | neutral scale | Tier 1 |
| `#5cc4ef` | 7 | secondary accent blue | **Tier 2** — see `#00b2ff` |

The Bootstrap residue (`#28a745`, `#ffc107`, `#17a2b8`) is the clearest case
where a scoped selector override is the only instrument available, and it is
bounded: roughly 63 occurrences across success, warning and info states.

`#00b2ff` deserves separate attention — 18 occurrences of a saturated blue that
reads as a competing brand accent inside a teal product.

## A6. Surface-by-surface inventory

48 SCSS files compose the Desk, imported by `desk/index.scss` in a fixed order.
Ranked by size, with hardcoded-literal count as the Tier 2 risk proxy:

| Surface | Lines | Hex | `var()` | Priority | Notes |
|---|---:|---:|---:|---|---|
| `desktop.scss` | 1,403 | 4 | 131 | **P1** | Workspace / home. Largest single surface, almost fully tokenised |
| `global.scss` | 730 | 0 | 62 | **P1** | Typography, base, links. Zero literals — pure Tier 1 |
| `list.scss` | 720 | 0 | 48 | **P1** | List view. Zero literals |
| `form_sidebar.scss` | 665 | 1 | 65 | P2 | |
| `form.scss` | 598 | 2 | 82 | **P1** | Form view |
| `global_search.scss` | 496 | 0 | 59 | P2 | Awesomebar |
| `kanban.scss` | 427 | 0 | 50 | P3 | |
| `sidebar.scss` | 405 | **4** | 27 | **P1** | Left nav. Declares own `:root` + dark block |
| `report.scss` | 379 | 0 | 24 | P2 | |
| `notification.scss` | 375 | 1 | 28 | P3 | |
| `mobile.scss` | 361 | 0 | 10 | P2 | Breakpoint behaviour |
| `dark.scss` | 271 | **4** | 130 | **P1** | The entire dark theme — see A8 |
| `page.scss` | 254 | 1 | 25 | **P1** | Page head, 48px `--page-head-height` |
| `calendar.scss` | 241 | 0 | 22 | P3 | |
| `image_view.scss` | 238 | 0 | 22 | P3 | |
| `avatar.scss` | 225 | 0 | 54 | P2 | Own `:root` + dark block |
| `frappe_datatable.scss` | 202 | 1 | 24 | P2 | Vendored datatable, `--dt-*` namespace |
| `timeline.scss` | 197 | 0 | 43 | P3 | |
| `settings_dialog.scss` | 191 | 0 | 24 | P2 | |
| `navbar.scss` | 189 | 0 | 19 | **P1** | Top bar. Zero literals |
| `tree.scss` | 173 | 1 | 24 | P3 | |
| `print_preview.scss` | 169 | **6** | 16 | P2 | Highest literal density; Lao print relevance |
| `toast.scss` | 150 | 0 | 21 | P3 | |
| `slides.scss` | 142 | 0 | 33 | P3 | Setup wizard — first-run impression |
| `module.scss` | 143 | 1 | 3 | P3 | |
| `variables.scss` | 135 | 1 | 37 | — | Declaration site |
| `file_view.scss` | 131 | 0 | 22 | P3 | |
| `filters.scss` | 129 | 0 | 8 | P2 | |
| `theme_switcher.scss` | 115 | 0 | 25 | **P1** | See A8 |
| Remaining 18 files | <110 each | 6 total | — | P3 | breadcrumb, card, menu, tags, version, etc. |

P1 is nine surfaces. They cover the navbar, sidebar, workspace, page head, list,
form, global typography, the theme switcher and dark mode — which is the whole of
what a user perceives as "the product looks like bERP". Seven of the nine carry
zero to four hardcoded literals, meaning they are reachable almost entirely from
Tier 1.

## A7. Identity surfaces — logo, favicon, splash, title

Each identity surface resolves through a different path. They are not
interchangeable, and two of them do not consult Website Settings at all.

| Surface | Resolution path | Current on bench | Status |
|---|---|---|---|
| Desk navbar logo | `get_app_logo()` → Website Settings `app_logo` → Navbar Settings `app_logo` → `app_logo_url` hooks | `/assets/berp_branding/images/berp-logo.svg` | ✅ correct |
| Login page logo | `www/login.py` → `get_app_logo()` | same | ✅ correct |
| Browser tab title | `desk.html` `{{ app_name }}` ← Website Settings | `bERP` | ✅ correct |
| Favicon | `desk.html` `{{ favicon or frappe-favicon.svg }}` | `berp-favicon.png` | ✅ correct |
| Desk splash | `templates/includes/splash_screen.html`, `{{ splash_image or frappe-framework-logo.svg }}`, `max-width: 200px` | `berp-logo.svg` | ⚠️ works, but see §D5 |
| **Legacy `/desk` page** | `desk/page/desktop/desktop.py` → **Navbar Settings only** → else `get_hooks("app_logo_url", app_name="frappe")[0]` | **Frappe logo** | ❌ **defect** |
| Apps screen tile | `boot.py` → `add_to_apps_screen` logo → app's `app_logo_url` → frappe's | frappe/erpnext | ⚠️ unbranded |
| Portal navbar | `brand_html` hook or Website Settings `banner_image` | `banner_image: None`, no `brand_html` hook | ⚠️ unbranded |
| `<meta name="theme-color">` | **hardcoded `#0089FF`** in `desk.html`, three variants | Frappe blue | ❌ unreachable by CSS |

**The `app_logo_url` positional trap, now measured.** The upstream resolver is:

```python
logos = frappe.get_hooks("app_logo_url")
app_logo = logos[0]
if len(logos) == 2:
    app_logo = logos[1]
```

On this bench `get_hooks("app_logo_url")` returns exactly two entries — frappe's
and erpnext's — so the fallback resolves to **the ERPNext logo**. The recon
script asserts this directly:

```
app_logo_url hooks: ['/assets/frappe/images/frappe-framework-logo.svg',
                     '/assets/erpnext/images/erpnext-logo.svg']
                    | len=2 | resolver picks: /assets/erpnext/images/erpnext-logo.svg
```
 Had
`berp_branding` declared the hook, the list would be three, `len(logos) == 2`
would be false, and the fallback would resolve to **frappe's** logo. The hook is
correct only at a list length of exactly two, which no app can guarantee. The
existing decision in `hooks.py` to declare no `app_logo_url` and drive identity
from Website Settings instead is hereby confirmed by measurement, and the comment
in that file should cite this resolver rather than describing the reason in
general terms.

**Two corrections follow immediately** (§E Stage 0): set Navbar Settings
`app_logo` so the legacy `/desk` page stops resolving to Frappe, and override the
`theme-color` meta through a `www/desk.html` template extension or accept it as a
documented residue.

## A8. Theme modes

`<html>` carries both `data-theme-mode` and `data-theme`, set from the user's
Desk Theme preference and toggled at runtime by `theme_switcher.js`. Frappe
declares its light values under `:root, [data-theme="light"]` and its dark values
under `[data-theme="dark"]`. **Fifteen files declare a dark block**:
`espresso/_colors.scss`, `desk/dark.scss` (271 lines, 130 `var()` references),
`common/{about,buttons,quill}.scss`, `desk/{avatar,form,kanban,print_preview,
settings_dialog,sidebar,tags,theme_switcher,version}.scss` and
`website/website_avatar.scss`.

**Contract consequence:** any bERP token retarget written only against `:root`
will be overridden in dark mode by upstream's `[data-theme="dark"]` block, which
is both later in the cascade within upstream's own sheet and equally specific.
Because our sheet loads after upstream's entirely, a `:root`-only override *will*
win in light mode and *will* win in dark mode too — which is worse: it forces
bERP's light values onto the dark theme and produces unreadable surfaces.

Every bERP token block must therefore be written twice — `:root, [data-theme="light"]`
and `[data-theme="dark"]` — with a dark-mode value derived per CI-001. Shipping
light-only is a defect, not an increment. If dark mode is out of scope for v1,
the correct action is to scope the override to `[data-theme="light"]` alone and
leave dark unbranded, not to write `:root`.

This is a testable rule and §C3 makes it one.

**Scope, per the §D6 ruling:** both themes ship in v1. Every foundations token is
therefore dual-valued from the outset, and the dark value is derived, not
inverted — Teal 700 `#117461` fails contrast on a dark surface and needs a
lighter step. Light and dark are kept as **separate token maps** rather than
interleaved, so that scoping back to light alone remains a deletion rather than
a rework if the timeline tightens.

## A9. Typography

`desk.bundle.scss` imports `frappe/public/css/fonts/inter/inter.scss` — **Inter is
already bundled and self-hosted by Frappe**, which satisfies CI-001's Latin face
with no work and no external font CDN.

`--font-stack` has only 6 uses, all near the root of the cascade, so it inherits
broadly; it is a viable single knob for the Latin/Lao stack.

The Lao face is the open item. Per the established Lao PDF font contract, server
rendering requires **static faces installed in the server font environment**, never
`@font-face`. Screen rendering is the opposite: the Desk needs a web font. These
are two different deliverables for the same typeface and must not be conflated —
the previous session's font work covered the server side only, and the Desk still
has no Lao web face. Noto Sans Lao is the CI-001 choice.

---

# Part B — The Override Contract

Five tiers. A change must be implemented at the **lowest-numbered tier that can
achieve it**. Moving up a tier requires the justification named in that tier's
rule, recorded in the commit message. Tier 4 is prohibited outright.

## B0. Tier 0 — Data

**Instrument:** Website Settings, Navbar Settings, and any other DocType field
upstream already reads.

**Reaches:** Identity — name, logo, favicon, splash, portal banner.

**Upgrade risk:** None. Data survives every upgrade unconditionally.

**Rule:** Any branding expressible as a stored value is expressed as a stored
value. Code that hardcodes what a field could carry is a defect, even when it
works. The one exception is `PLATFORM_DEFAULTS` in `brand.py`, which writes those
fields on install so an unconfigured site is bERP rather than ERPNext; tenant
values still override, per WL-001 §4.

**Verification:** `branding_status()` must report `resolved_from: Website Settings`
and every platform asset `READY`.

## B1. Tier 1 — Token retarget

**Instrument:** A single stylesheet declared through `app_include_css`,
redeclaring upstream's **semantic** custom properties.

**Reaches:** Per A4/A6, the large majority of visible Desk colour, radius,
typography and spacing — including all of ERPNext, which declares no properties
of its own.

**Upgrade risk:** Low. Upstream renaming a semantic property is a visible,
greppable break, not a silent one, and §C4's regeneration drill catches it.

**Rules:**

- **B1.1 — Semantic only.** Retarget `--control-bg`, `--primary`, `--text-color`
  and their peers. Never redeclare a primitive (`--gray-500`, `--ink-gray-4`,
  `--surface-gray-2`). Primitives carry deliberate non-brand meaning across both
  themes; overwriting them recolours states that must stay neutral.
- **B1.2 — Both themes, always.** Every block is written twice, against
  `:root, [data-theme="light"]` and `[data-theme="dark"]` (A8). A `:root`-only
  block is a defect. Per §D6 both themes are in v1 scope, and the dark value is
  derived from CI-001 for a dark surface, never produced by inverting the light
  value.
- **B1.6 — Density is a token set.** Per §D2, control and row dimensions resolve
  through `--berp-control-height` / `--berp-row-height`, which take Comfortable
  (44px) or Compact (32px / 30px) values selected by a body-level attribute.
  A component that hardcodes either figure is a defect. Compact is the default
  for list, report, kanban and grid views.
- **B1.3 — Tokens come from the token source.** Values are references into the
  bERP foundations layer, not hex literals typed at the point of use. DS-001 §39
  forbids raw values in governed component code; this is that rule applied.
  See §D3 — the shipped `berp_auth.css` does not yet comply.
- **B1.4 — Declare the flow.** Every retargeted property is listed in a manifest
  with its upstream name, its bERP source token, and its measured use count, so
  the next upgrade diff is a comparison and not an investigation.
- **B1.5 — No `!important` at this tier, ever.** Source order already wins.
  Needing `!important` here means the property is not the mechanism, and the
  change belongs at Tier 2 with a measurement.

## B2. Tier 2 — Scoped component override

**Instrument:** Selector rules in the same bERP stylesheet, targeting upstream
classes.

**Reaches:** The literal tail of A5 — Bootstrap state colours, `#00b2ff`, and any
component whose appearance is not expressed as a variable.

**Upgrade risk:** Medium. Upstream class renames break silently: the rule stops
matching and the surface reverts to upstream's appearance with no error.

**Rules:**

- **B2.1 — Measure, then match depth.** Before writing an override, measure the
  competing rule's specificity. Match its depth rather than escalating. This is
  not theory: the login primary button stayed `#171717` under a 0,2,0 override
  because upstream's rule is `.for-login .page-card .page-card-actions .btn-login`
  at 0,4,0. Matching the depth fixed it with no `!important`.
- **B2.2 — `!important` is a bounded last resort.** Permitted only when a live
  four-class test has been shown to lose, and only inside a bERP-owned scope
  class. Each use carries an inline comment stating what was measured and why.
  The shipped `berp_auth.css` has exactly two such uses, both on input height and
  padding, both documented — that is the ceiling of what is acceptable, not a
  starting budget.
- **B2.3 — Every rule is scoped or inventoried.** A Tier 2 rule either sits under
  a bERP-owned scope class, or is recorded in the override manifest with the
  upstream selector it shadows. Unscoped, uninventoried rules are how a theme
  becomes unmaintainable across two upgrades.
- **B2.4 — No structural rewriting.** Tier 2 changes appearance. It does not
  reposition, reparent or hide upstream structure to simulate a different layout.
  That is Tier 3.

## B3. Tier 3 — Template extension

**Instrument:** A `www/` or `templates/` file in `berp_branding` that **extends**
the upstream template and wraps a block with `{{ super() }}`.

**Reaches:** Layout and structure — the split auth surface, additional brand
panels, the `theme-color` meta.

**Upgrade risk:** Medium-low *if the rule below is kept*; high if it is broken.

**Rules:**

- **B3.1 — Extend, never copy.** `{% extends "frappe/www/<same>.html" %}` and wrap
  with `{{ super() }}`. Not one line of upstream markup is copied. This is the
  proven pattern: the three shipped auth templates inherit
  `update-password.html`'s 220-line `{% block script %}` untouched, so an upstream
  change to the fields is inherited rather than fought.
- **B3.2 — Activation is by installed order, and must be verified.** Frappe
  resolves `www` pages with `reversed(get_installed_apps())`; `berp_branding`
  installs last and therefore wins. This is verified directly against
  `TemplatePage`, asserting `app == "berp_branding"` — not inferred from the page
  looking right.
- **B3.3 — One scope class per template.** Each template introduces exactly one
  bERP-owned class (`.berp-auth`, `.berp-desk`, …) under which all of its CSS
  lives, so a stylesheet physically cannot reach a surface its template does not
  own.
- **B3.4 — Justify the tier.** A Tier 3 change states in its commit message which
  Tier 1/2 instrument was insufficient and why.

## B4. Tier 4 — Prohibited

Editing upstream files; copying upstream markup; patching upstream SCSS or
rebuilding upstream bundles; monkey-patching upstream Python; vendoring a
modified copy of a Frappe or ERPNext asset. No justification admits these. A need
that appears to require Tier 4 is escalated to a governance decision, not
implemented.

## B5. Cross-cutting rules

**B5.1 — Asset namespacing.** Every SVG shipped by bERP has its `id`, its
`url(#…)` references **and its `xlink:href="#…"` references** namespaced together.
Missing the third left ten gradients dangling and rendered the mark as a sliver;
the preflight check D7 now guards it. Namespacing two of the three is worse than
namespacing none, because it fails only in some renderers.

**B5.2 — Cache busting is mandatory.** Desk CSS ships as a `*.bundle.scss`
compiled by `bench build` into a content-hashed file. Raw-path `app_include_css`
is prohibited for Desk CSS (A2).

**B5.3 — Translatable strings.** Every literal string a bERP template renders is
wrapped in `{{ _() }}`. A Lao translation file for `berp_branding` is an
outstanding deliverable, not an optional extra, for a product whose market is
Lao PDR.

**B5.4 — Accessibility is a gate, not a review note.** WCAG 2.2 AA contrast is
verified by measurement on every text/background pair the theme introduces. The
concrete precedent: Neutral 400 `#8B8D90` measures 3.3:1 on white and fails at
caption size; Neutral 500 `#595A5C` measures 6.4:1 and passes. Estimates are not
acceptable — the first figure written for that pair was "~9:1" by eye and was
wrong by a factor that would have shipped a failing surface.

**B5.5 — Nothing ships unmeasured.** Every claim that a surface now looks correct
is backed by a DOM measurement (`getBoundingClientRect`, `getComputedStyle`,
`elementFromPoint`) or a preflight assertion. Screenshots are illustration, never
evidence (§C5).

---

# Part C — Conformance and verification

## C1. Definition of done for a Desk surface

A surface is done when all five hold:

1. It renders per the CI-001/DS-001 specification in **both** themes.
2. Every contrast pair it introduces is **measured** at AA.
3. Its implementation sits at the lowest viable tier, with any escalation
   justified in the commit message.
4. `scripts/check_branding.py` passes, including the new Desk checks of C2.
5. The upgrade drill of C4 has been run against the current upstream and the
   inventory diff is empty or explained.

## C2. Preflight extensions required

`scripts/check_branding.py` currently runs 38 bench-free checks in about a
second. The Desk work requires a new section E, in the same style — mechanical,
dependency-free assertions that fail loudly:

| Check | Asserts |
|---|---|
| E1 | The Desk stylesheet is a `*.bundle.scss`, not a raw path (B5.2) |
| E2 | `app_include_css` is declared and names that bundle |
| E3 | Every custom property the bERP sheet declares appears in the override manifest (B1.4) |
| E4 | No bERP block redeclares a primitive token (B1.1) |
| E5 | Every `:root, [data-theme="light"]` block has a matching `[data-theme="dark"]` block (B1.2, A8) |
| E6 | No `!important` outside a bERP-owned scope class, and each carries a comment (B2.2) |
| E7 | No hex literal appears in a governed block; values are token references (B1.3) |
| E8 | Every declared asset path exists on disk (existing D6, extended to Desk) |
| E9 | Every measured contrast pair in the manifest is ≥ 4.5:1, or ≥ 3:1 with a large-text annotation (B5.4) |

E5 and E7 are the two that would have caught the defects this inventory found.

## C3. Bench verification

Bench-side, per surface: assert the computed value of each retargeted property
against the manifest under `data-theme="light"` **and** `data-theme="dark"`, and
assert `TemplatePage` resolution for any Tier 3 template. Both run headless; no
screenshot is involved.

## C4. The upgrade drill — the acceptance criterion as a repeatable test

DS-001's criterion is currently a sentence. This makes it a procedure:

1. Re-run `berp_branding/scripts/recon_desk_surface.sh` against the upgraded bench.
2. Diff its output against the §A baseline recorded in this document.
3. Any custom property in the override manifest that has disappeared, or any
   Tier 2 selector that no longer matches, is an upgrade break — fix before
   promoting.
4. Re-run the preflight and the bench assertions of C3.
5. Record the new baseline as DS-001A vNext.

An upgrade that produces an empty diff has proven the criterion for that
upgrade. This is the only form in which that criterion can actually be enforced.

## C5. Standing instrument warnings

Three instruments have produced confidently wrong or empty results in this
workstream and are not to be trusted without a control.

**Browser screenshots.** The browser pane repeatedly returned pre-layout frames
while warning that the app window may be behind another. Every visual conclusion
drawn from those frames was wrong, while `getBoundingClientRect`,
`elementFromPoint` and canvas pixel sampling were correct every time. Screenshots
are illustration for the reader; they are not evidence.

**ImageMagick as an SVG judge.** With no `rsvg-convert` present, the MSVG
fallback renders even the *known-good* kit file as a sliver. The instrument was
caught only because it was pointed at a control first. Any SVG rendering check
must be validated against a file known to be correct before its negative results
are believed.

**A probe that filters its own output.** The recon script of §2 was validated
against the hand-measured figures of Part A and reproduced all of them exactly —
and its live-checks section still returned twelve blank lines. The cause was in
the script, not the bench: `bench console` is IPython, its `In [n]:` prompts
carry ANSI colour codes, and an anchored `^In \[[0-9]+\]:` filter therefore
matched nothing and discarded every line of real output. Had that section been
trusted, this document would have reported the live hook resolution as
unavailable. The fix — emit a sentinel from inside the console and extract on it,
never parse the prompt — is now in the script with the reason recorded beside it.

The lesson generalises past this one script: **an instrument that passes on the
part you checked is not validated on the part you did not.** The static sections
were verified against known values; the live section had no control, and that is
exactly where it failed.

All three are instances of REVIEW-METHOD P2, which has now earned its keep five
times in this workstream. The general rule stands: **a negative or empty
diagnostic is untrustworthy until the mechanism has been validated against a
known-good case.**

---

# Part D — Governance decisions

These were conflicts between controlled documents, or between a controlled
document and shipped code. **All six were ruled by OP-Vily on 2026-09-19** and
are recorded here as decisions. Each entry keeps the original analysis, so the
reasoning behind the ruling survives; the **Ruling** line is what governs.

Two rulings depart from the recommendation given — D6 (dark mode) and part of
D4 (palette). Both are recorded as given, with the cost of each stated plainly
so the next session inherits the trade-off and not just the outcome.

## D1. The login surface contradicts DS-001 §1

DS-001 §1 specifies an *Authentication Card* in White `#FFFFFF` on a *Page
Background* of Neutral 50 `#F7F7F8`, card radius 16px, with a `[ bERP logo ]`
inside the auth panel. What shipped, and what was approved visually in this
workstream, is a full-bleed split layout with no card and the in-panel logo
suppressed in favour of the brand panel's mark.

The shipped design is the better one and the approval is recent, but DS-001 is
the controlled document and it currently describes something else.

**Recommendation:** amend DS-001 §1 to the split layout and retire the card
specification, rather than rebuilding the login to match a superseded spec. A
controlled document that disagrees with approved, shipped, tested work should be
corrected, not obeyed.

> **RULING (2026-09-19): amend DS-001 §1 to the split layout.** The shipped auth
> surface is authoritative. DS-001 §1's card specification is superseded and is
> not to be inherited by Desk components. Action: revise DS-001 §1; no code
> change.

## D2. Control height — CI-001 §21 vs DS-001 §16

> **CORRECTION (2026-09-19, after the ruling).** The conflict described below is
> not real, and the ruling was therefore made on a false premise. Reading both
> parents in full: **CI-001 §21's Compact/Standard/Comfortable are three SIZES OF
> ONE CONTROL** (32–36 / 40 / 44–48), while **DS-001 §16's Comfortable/Compact are
> two DENSITY MODES**, each with five contracts. Different axes, overlapping
> vocabulary. They reconcile exactly:
>
> | DS-001 §16 contract | Comfortable | Compact | CI-001 §21 equivalent |
> |---|---:|---:|---|
> | Standard control | 40px | 32px | Standard 40 / Compact 32–36 |
> | Large control | 48px | 40px | Comfortable 44–48 (upper) |
> | Table row | 44px | 36px | Comfortable 44–48 (lower) |
> | Navigation item | 40px | 36px | — |
> | Card internal spacing | 24px | 16px | CI-001 §12 card padding |
>
> **DS-001 §16 is adopted verbatim** and governs. The ruling's intent is satisfied
> — 44px survives as the Comfortable table row, which is where row height
> actually matters — and no amendment to either parent is needed after all.
>
> One consequence: under §16 a form input at Comfortable is **40px**, so the
> shipped login input at 44px was one step oversized. Corrected to 40px in Stage
> 0.3, which still clears CI-001 §20's 40×40 interactive-area floor.
>
> This was my error, not the documents'. It is left in place below rather than
> deleted so the ruling can be read against what prompted it.


CI-001 §21 puts Comfortable inputs at 44–48px. DS-001 §16 puts the Comfortable
standard control at 40px. Two authority documents disagree on a primitive that
propagates through every form in the product. The login shipped at 44px.

Upstream's `--btn-height` is 28px and `--input-height` 28px, so **either figure is
a large departure** and will cascade into list rows, filters, the awesomebar and
every dialog. This decision cannot be deferred past Stage 1; it sets the vertical
rhythm of the entire Desk.

**Recommendation:** ratify 44px as Comfortable, matching what shipped and CI-001's
lower bound, and correct DS-001 §16. Additionally define a **Compact** density at
or near upstream's 28–32px, because a 44px control height applied to a dense ERP
list view will cost roughly a third of the visible rows — an operational
regression that no amount of brand fidelity justifies. Density should be a token
set, not a single value.

> **RULING (2026-09-19): 44px Comfortable, plus a Compact density set.** DS-001
> §16 is corrected to 44px. Density becomes a **token set, not a single value**,
> with two named modes:
>
> | Token | Comfortable | Compact |
> |---|---|---|
> | `--berp-control-height` | 44px | 32px |
> | `--berp-row-height` | 44px | 30px (upstream parity) |
> | `--berp-control-padding-y` | scaled to 44 | scaled to 32 |
>
> Comfortable is the default for forms, dialogs and the auth surface. Compact is
> the default for list, report, kanban and grid views, where row count is the
> operational currency. The mode is selected by a body-level attribute so a
> single token block serves both; it is **not** two stylesheets.
>
> Stage 1 must ship both modes together. Shipping Comfortable alone would put a
> 44px row into the list view and cost roughly a third of visible rows — the
> exact regression the Compact set exists to prevent.

## D3. Token layer not yet extracted — DS-001 §35/§39

DS-001 §35 requires tokens to flow `Token Source → berp_branding → tokens.css`,
and §39 forbids raw values in governed component code. `berp_auth.css` currently
hardcodes hex values into `.berp-auth`-scoped custom properties. It works, and it
is scoped, but it is not the required architecture, and Tier 1 of this contract
depends on the foundations layer existing.

**Recommendation:** extract `berp_branding/public/scss/foundations/_tokens.scss`
as the single source, refactor `berp_auth.css` to consume it, and build the Desk
sheet on it from the start. This is a prerequisite for Stage 1, not a follow-up.
Preflight check E7 enforces it thereafter.

> **RULING (2026-09-19): proceed as recommended.** Not raised as an open question
> because DS-001 §§35/39 already mandate it and Tier 1 cannot be built without
> it. Executed as Stage 0.3. The foundations layer must carry the D2 density sets
> and the D6 dark values from the outset, so it is built once rather than
> retrofitted twice.

## D4. `#2EB990` is a locked-palette violation, not an undocumented colour

CI-001 §7 locks the brand palette to Mint, Teal, Slate, Charcoal and White.
Preflight check D8, run against the kit, reports six values in the artwork that
are not in that ramp:

| File | Off-palette values |
|---|---|
| `bERP_Logo_IconBgGreen.svg` | `#2EB990`, `#CFD1D2`, `#FDFEFF` |
| `bERP_Logo_IconBW.svg` | `#231F20`, `#67686B` |
| `bERP_Logo_IconBgWh.svg` | `#231F20`, `#FCFEFE` |

D8 currently reports these as a palette-conformance *warning*. Under §7's locked
palette they are violations of a locked primitive, which is a different severity.
`#2EB990` is the substantive one — a green distinct from the brand teal, sitting
in the icon's background plate.

Note also that three of the six (`#CFD1D2`, `#FDFEFF`, `#FCFEFE`) are
near-white/near-grey values that read as export artefacts rather than design
intent, which suggests the artwork, not the palette, is what needs correcting.

**Recommendation:** decide explicitly — either extend CI-001 §6/§7 to admit
`#2EB990` and the five greys as sanctioned extensions with stated roles, or
correct the artwork to the locked palette. Leaving it as a standing warning means
the preflight's palette check stops carrying information, which is worse than
either resolution.

> **RULING (2026-09-19): both, split by value.** The ruling selected *extend §7
> for `#2EB990`* and *correct the artwork to the locked palette*. Those two
> conflict on `#2EB990` alone, so they are reconciled here by intent — admit the
> one deliberate colour, correct the five accidental ones:
>
> | Value | Disposition | Rationale |
> |---|---|---|
> | `#2EB990` | **Admit** — extend CI-001 §6/§7 with a stated role | Deliberate design: the icon's background plate. Needs a named role and a contrast note, not deletion |
> | `#231F20` | Correct to Charcoal | Near-black off the ramp by 2 points; no design intent |
> | `#67686B` | Correct to the nearest Slate step | Off-ramp grey |
> | `#CFD1D2` | Correct to the nearest neutral step | Off-ramp grey |
> | `#FDFEFF`, `#FCFEFE` | Correct to White `#FFFFFF` | Export artefacts — sub-perceptual offsets from white |
>
> After this, D8 should pass rather than warn, and its severity is raised from
> WARN to FAIL so a future off-palette value cannot accumulate silently.
>
> **If this split misreads the intent**, the alternative readings are: correct
> `#2EB990` too (D8 passes with no §7 change, but the icon plate changes colour),
> or admit all six (no artwork work, but §7 stops being a locked palette in any
> meaningful sense). Flag before Stage 3 if either is preferred.

## D5. `bERP_Logo_hText.svg` is named the master but fails the live-text check

CI-001 §4 names `bERP_Logo_hText.svg` as the LOGO-01 master. That file carries a
live `<text>` tagline set in Inter rather than outlined paths, and preflight check
D4 fails on it. Where Inter is absent — most servers, and wkhtmltopdf — it
silently substitutes: the output does not break, it renders wrong while still
looking finished. This is the same failure shape as the Phetsarath/DejaVu
incident.

The outlined replacements `bERP_Logo_hTextOL.svg` and `vTextOL.svg` exist and
ship as `berp-lockup-horizontal.svg` and `berp-lockup-vertical.svg`, with zero
`<text>` elements and zero font-family references.

**Recommendation:** amend CI-001 §4 to name the outlined file as the LOGO-01
master, and retire `hText.svg` / `vText.svg` from the kit. D4 then passes and the
preflight returns to a clean baseline.

> **RULING (2026-09-19): amend CI-001 §4 to name the outlined file as LOGO-01
> master.** `bERP_Logo_hTextOL.svg` becomes the master; `hText.svg` and
> `vText.svg` are retired from the kit. Preflight D4 then passes and the
> `--assets` baseline returns to clean.

**Related gap:** CI-001 §3 calls for a small-size lockup without tagline. It does
not exist in the kit. The Desk splash constrains to `max-width: 200px` (A7), which
is precisely the case that lockup is for. Until it exists the splash uses the
icon-only mark, which is acceptable but is not what §3 specifies.

> **RULING (2026-09-19): commission the small-size lockup.** Designer deliverable,
> outlined text (per D5), no tagline, legible at 200px wide. It ships as
> `berp-lockup-small.svg` and becomes the splash asset. Until it lands, the splash
> keeps the icon-only mark; this does **not** block Stage 1.

## D6. Dark mode — in or out of v1

A8 makes this a decision rather than a default. Branding the Desk light-only
while leaving `[data-theme="dark"]` upstream produces a coherent, if unbranded,
dark theme. Writing `:root`-only overrides produces a **broken** dark theme.
There is no zero-effort middle option.

**Recommendation:** scope v1 to `[data-theme="light"]` explicitly and leave dark
upstream, with dark-mode tokens as a defined Stage 4. Budget it as real work —
`dark.scss` alone is 271 lines with 130 `var()` references — rather than assuming
it falls out of the light theme.

> **RULING (2026-09-19): both themes in v1.** Dark mode is in scope for Stage 1,
> not deferred to Stage 4. This departs from the recommendation, and the cost is
> stated here so it is inherited deliberately:
>
> - Every token in the foundations layer needs **two values**, not one. The dark
>   value is a derivation, not an inversion — Teal 700 `#117461` on a dark surface
>   fails contrast and needs a lighter step.
> - **Fifteen files** declare dark blocks upstream (A8); `dark.scss` alone is 271
>   lines with 130 `var()` references.
> - Every contrast pair must be measured **twice** (B5.4), roughly doubling the
>   accessibility gate.
> - Realistically this makes Stage 1 about twice the size of the light-only
>   version.
>
> The benefit is a complete identity at first release and no second pass through
> the same token layer, which is the stronger position if the timeline allows it.
> The foundations layer of D3 must therefore be built dual-valued from the
> outset — this is the main reason Stage 0.3 cannot be deferred.
>
> **De-scoping route, if the timeline tightens:** scope the shipped blocks to
> `[data-theme="light"]` and drop the dark values. That degrades to the
> recommended option cleanly and without rework, provided the foundations layer
> keeps light and dark as separate token maps rather than interleaving them.
> Build it that way.

---

# Part E — Sequenced plan for the Desk rebrand

Staged so that the highest-visibility, lowest-risk change lands first. **All six
§D decisions are ruled, so no stage is blocked on governance.** The rulings
change two things against the draft plan: dark mode moves from Stage 4 into
Stage 1, and density becomes a two-mode token set rather than a single value.

## Stage 0 — Corrections and prerequisites (no new theme code)

Blocked by: nothing. Unblocks: everything. **Start here.**

| # | Action | Tier | Source |
|---|---|---|---|
| 0.1 | Set Navbar Settings `app_logo`; add it to `BRAND_FIELDS` and `PLATFORM_DEFAULTS` so the legacy `/desk` page stops resolving to the Frappe logo | 0 | A7 |
| 0.2 | Update the `hooks.py` comment to cite the measured `app_logo_url` resolver and the two-entry list observed on the bench | — | A7 |
| 0.3 | Extract `foundations/_tokens.scss` — **dual-valued (light + dark, separate maps) and carrying both density modes** from the outset; refactor `berp_auth.css` to consume it | — | D3, D2, D6 |
| 0.4 | Add preflight section E (E1–E9) | — | C2 |
| 0.5 | Commit `scripts/recon_desk_surface.sh` and record the §A baseline | — | C4 |
| 0.6 | Resolve the `lao_regional` module collision (`lao_berp` and `berp_lao` both declare it) | — | open item |
| 0.7 | Durable compose fix for the frontend container's asset overlay | — | A2 |
| 0.8 | Amend **DS-001 §1** to the split login layout; amend **DS-001 §16** to 44px and add the Compact set | — | D1, D2 |
| 0.9 | Amend **CI-001 §4** to name `hTextOL.svg` as LOGO-01 master; retire `hText`/`vText`. Amend **§6/§7** to admit `#2EB990` with a stated role | — | D5, D4 |
| 0.10 | Correct the five off-palette artwork values; raise preflight D8 from WARN to FAIL | — | D4 |
| 0.11 | Commission `berp-lockup-small.svg` (outlined, no tagline, legible at 200px) — does not block Stage 1 | — | D5 |

## Stage 1 — Token layer (Tier 1)

Blocked by: 0.3 only.

Ship `berp_branding/public/scss/berp_desk.bundle.scss`, declared through
`app_include_css`, retargeting the semantic properties of A4 against **both**
`:root, [data-theme="light"]` and `[data-theme="dark"]` (§D6), with the two
density modes of §D2.

Expected reach on the measured evidence: the nine P1 surfaces of A6, seven of
which carry four or fewer hardcoded literals. This is the stage that makes the
Desk read as bERP, and it contains no selector overrides at all.

**Size, stated honestly.** The §D6 ruling roughly doubles this stage against the
light-only version: every token dual-valued, fifteen upstream dark-declaring
files to check, and every contrast pair measured twice. Budget accordingly. If
the timeline tightens mid-stage, the de-scope route in §D6 is a deletion of the
dark maps, not a rework — provided 0.3 kept them separate.

Gate: C2 preflight green (including E5, which fails a light-only block); C3
computed-value assertions green in **both** themes; contrast measured on every
new pair in both themes; Compact and Comfortable both verified on a list view.

## Stage 2 — Typography (Tier 1 + asset)

Blocked by: Stage 1.

Retarget `--font-stack` to the Inter + Noto Sans Lao stack. Inter is already
bundled by Frappe (A9) and needs nothing. Ship self-hosted Noto Sans Lao web
faces in `berp_branding/public/fonts/` with `@font-face` in the bERP bundle.

This is the Desk-side counterpart to the already-completed server-side font
install. The two must not be conflated: the server faces serve wkhtmltopdf, the
web faces serve the browser, and neither substitutes for the other.

Gate: Lao text renders with correct combining-mark order in the Desk — verified
by rendering a known Lao string and comparing against a reference, not by
appearance. A missing Lao face reorders marks rather than showing boxes, so
"it looks fine" is not a result.

## Stage 3 — Component tail (Tier 2)

Blocked by: Stage 1. (§D4 is ruled; 0.10 carries the artwork correction.)

Scoped selector overrides for the literal tail of A5, in priority order:
`#00b2ff` (18 occurrences, a competing brand accent), then the Bootstrap state
residue `#28a745` / `#ffc107` / `#17a2b8` (≈63 occurrences), then
`print_preview.scss` (highest literal density, and directly relevant to Lao
document output).

Every rule specificity-measured per B2.1 and inventoried per B2.3.

## Stage 4 — Structural (Tier 3)

Blocked by: Stages 1–3.

Any layout change the Desk requires, via `{{ super() }}` template extension only,
and the `theme-color` meta override. **Dark mode has moved out of this stage into
Stage 1** per §D6, which is what leaves Stage 4 small.

## Stage 5 — Identity completion

Blocked by: delivery of `berp-lockup-small.svg` (0.11) for the splash item only;
the rest is unblocked.

Portal navbar branding, the apps-screen tile, the splash lockup once 0.11 lands,
and the Lao translation file for `berp_branding`.

---

# Part G — Stage 0 / Stage 1 implementation record

Implemented and verified on `dev.berp.bizera.la`, 2026-09-19. This section
records what the implementation *proved* about Part A and Part B, and the two
places where doing the work corrected the inventory.

## G1. The contract's central claim, verified at the selector level

Part B rests on one assertion: that a stylesheet berp_branding declares wins at
equal specificity because it loads last. Both halves are now measured rather
than reasoned.

**Load order.** With `app_include_css = "berp_desk.bundle.css"` declared, the
resolved hook list on the bench is:

```
['desk.bundle.css', 'report.bundle.css', 'erpnext.bundle.css',
 'lao_berp.bundle.css', 'berp_desk.bundle.css']
```

Ours is fifth of five.

**Specificity.** Every property Stage 1 retargets is declared upstream at
`:root` or `[data-theme=dark]` — 0,1,0 in both cases, identical to ours:

| Property | Upstream selector | Upstream value |
|---|---|---|
| `--primary` | `:root` | `#171717` |
| `--text-color` | `:root` / `[data-theme=dark]` | `var(--gray-800)` / `var(--gray-50)` |
| `--text-muted` | `:root` / `[data-theme=dark]` | `var(--gray-700)` / `var(--gray-400)` |
| `--border-radius` | `:root` | `8px` |
| `--btn-height` | `:root,[data-theme=light]` | `28px` |
| `--list-row-height` | `:root,[data-theme=light]` | `30px` |
| `--navbar-bg` | `:root,[data-theme=light]` | `var(--neutral)` |
| `--font-stack` | `:root` | `"InterVariable", "Inter", …` |

Equal specificity, later in source order. **Stage 1 contains no `!important` at
all**, which is the contract working as designed rather than a stylistic
preference.

One upstream rule deliberately outranks us and should stay that way:
`[data-theme=dark] .print-format { --text-color: var(--gray-900) }` at 0,2,0.
Print output wants dark text even in dark mode; our 0,1,0 dark block correctly
does not reach it.

## G2. Frappe's shape is closer to CI-001 than expected

`--border-radius: 8px`, `--border-radius-lg: 12px`, `--border-radius-xl: 16px`
upstream — which is CI-001 §13's control / card / modal scale **exactly**. Only
the two intermediate steps (`sm` 8→6, `md` 10→8) move. The radius layer needed
almost no work, which was not visible from the source SCSS and only appeared in
the built bundle.

Frappe also self-hosts and bundles Inter through `desk.bundle.scss`, so the
Latin half of CI-001 §10 is satisfied with no font shipping and no external
font host.

## G3. End-to-end verification, in a browser

The whole chain — CI-001 value → primitive → semantic map → compiled bundle →
browser computed style — was read back from the running page, not inferred:

| | Light | Dark |
|---|---|---|
| `--berp-action-primary` | `#117461` | `#117461` |
| `--berp-text-primary` | `#1F2021` | `#FFFFFF` |
| `--berp-text-link` | `#117461` | **`#8BCCBF`** |
| `--berp-surface-default` | `#FFFFFF` | `#2F3031` |
| `--berp-focus-color` | `#117461` | **`#51B29F`** |

The two bold values are where the dark map **diverges from an inversion**, and
they are the reason §B1.2 is written the way it is. Teal 700 as link text on
`neutral.900` measures 2.87:1 and fails AA; teal.300 measures 7.23:1.

Contrast, computed in-page from what actually resolved — all eight pairs pass AA:

| Pair | Light | Dark |
|---|---:|---:|
| text.primary on surface.default | 16.32:1 | 13.22:1 |
| text.secondary on surface.default | 6.90:1 | 6.94:1 |
| text.link on surface.default | 5.68:1 | 7.23:1 |
| white on action.primary | 5.68:1 | 5.68:1 |

Density switching resolves exactly to DS-001 §16: setting
`data-berp-density="compact"` moves `--berp-control-height` 40→32 and
`--berp-row-height` 44→36.

Rendered auth surface: input computes **40px** (was 44 — see the §D2
correction), button background `rgb(17, 116, 97)` = Teal 700, radius 8px, font
stack `Inter, "Noto Sans Lao", …`, and `berp_auth.bundle.OBNPMFCH.css` loads
last of four sheets with a content hash.

## G4. A harness defect, proven rather than assumed

Adding the Navbar Settings mirror turned preflight checks C11 and C17 red. The
stub returned **one** `_Doc` for every `get_single()` call, so the Navbar write
landed on the Website Settings document and two unrelated force-semantics checks
failed against correct product code.

Modelling the two singles properly turns them green with the product code
untouched — which is what distinguishes a harness defect from a real one, and is
REVIEW-METHOD P2 applied to a test double rather than to a diagnostic. Had the
stub not been fixed, the obvious "fix" was to weaken `apply_branding`'s force
semantics to satisfy a fabricated failure.

A second instrument note for §C5: `bench console` cannot render a Desk context.
`www/desk.py:get_context` dies at `get_csrf_token()` (line 35) for want of a
request object — *before* line 39 assembles `app_include_css`. The empty list it
returned was the console's, not the product's. Verifying the rendered Desk head
needs an authenticated HTTP request.

## G5. What Stage 1 did not do

No selector override, no structural change, no `!important`, nothing outside the
token layer. Stage 3's literal tail (A5) is untouched: `#00b2ff` and the
Bootstrap state residue still render upstream's colours. The Desk navbar height
stays at Frappe's 48px rather than CI-001 §19's 56–64px band, because changing it
moves sticky offsets and belongs with the structural work in Stage 4.

Open from this stage:

- `--list-row-height` now resolves to 44px in Comfortable, up from upstream's
  30px. That is DS-001 §16's table-row contract applied faithfully, and it costs
  roughly a third of the visible rows in a list view. §16 says "Tables → Compact
  available"; it does not say Compact is their default. **Recommend making
  Compact the default for list, report and kanban views** and confirming that
  reading of §16 — this is the one place where following the spec literally has
  an operational cost worth a second look.
- The rendered Desk head is verified by source and hook resolution but not yet
  by an authenticated page load (G4).

---

# Part F — Provenance

**Measurement environment.** `dev.berp.bizera.la` on the private `berp-linux` VM,
2026-09-19, probed inside `berp-dev-backend-1`. Frappe v16 / ERPNext v16 as
recorded in SESSION-031; asset bundles built 2026-09-09
(`desk.bundle.RXWII534.css`). Installed apps in order: `frappe`, `erpnext`,
`lao_berp`, `berp_branding`.

**Reproduction.** `berp_branding/scripts/recon_desk_surface.sh` regenerates every
figure in Part A. Run it inside the backend container; set `SITE=<sitename>` to
include the live hook-resolution and identity checks. It is read-only and safe on
production.

**Instrument validation.** The script was run against this bench and reproduced
every hand-measured figure in Part A exactly — bundle size, 6,982 rule blocks,
2,617 `var()` uses, 1,453 hex literals, 565 custom properties, the full hex
census and all 48 per-surface rows. Its live section was separately repaired and
re-verified (§C5). Both the figures and the instrument that produces them are
therefore measured, not asserted.

**Reference implementation.** The shipped authentication surface —
`berp_branding/www/login.html`, `update-password.html`, `complete_signup.html`,
`templates/includes/auth_brand.html`, `public/css/berp_auth.css` — demonstrates
Tier 0, Tier 2 and Tier 3 in their contract-conformant forms, with the §D3
exception noted.

**Standing baseline.** `berp_branding` preflight at time of writing, run as
`python scripts/check_branding.py --assets <kit>/Logo/SVG`: **37 pass, 1 fail
(D4 — live text in `hText.svg`/`vText.svg`, see §D5), 2 warn (D5 generic SVG ids
in the kit; D8 off-palette values, see §D4), 0 skipped.** Run without `--assets`
it is 34 pass, 0 fail, 2 skip — the asset checks are the ones carrying the open
findings, so the `--assets` form is the one that counts. Bench: `berp_branding` 28/28;
`berp_lao` 199 OK, 6 skipped (environment: Lao faces now installed, workers
pending restart).

**Open items carried forward, not in scope here.** Restart bench workers and
re-run the 6 skipped font tests; commit-or-discard `berp_lao/translations/lo.csv`
(~100 uncommitted lines).

**Change log.**

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-09-19 | Initial inventory and contract. Measured on dev bench. Awaiting §D rulings. |
| 0.3 | 2026-09-19 | Stage 0 and Stage 1 implemented and verified (Part G). §D2 corrected — the CI-001/DS-001 density conflict was my misreading; DS-001 §16 adopted verbatim. §A2 deployment mechanism refined after hitting it. |
| 0.2 | 2026-09-19 | All six §D decisions ruled by OP-Vily. D2: 44px Comfortable + 32px Compact as a token set. D6: both themes in v1 (departs from recommendation; cost and de-scope route recorded). D1: DS-001 §1 amended to the split layout. D4: `#2EB990` admitted, five values corrected. D5: outlined file becomes LOGO-01 master; small lockup commissioned. Part E resequenced — no stage now blocked on governance. |
