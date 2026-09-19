# Copyright (c) 2026, BizEra / BSTBizEra and contributors
# License: GNU General Public License v3. See license.txt

app_name = "berp_branding"
app_title = "bERP Branding"
app_publisher = "BSTBizEra"
app_description = "bERP platform branding and per-tenant white-label for Frappe/ERPNext"
app_email = "dev@bstbizera.com"
app_license = "GNU General Public License (v3)"
required_apps = ["frappe/erpnext"]

# ─── No app_logo_url hook, on purpose ─────────────────────────────────────────
# Frappe v16, navbar_settings.get_app_logo() — read from the running source, not
# recalled:
#
#     app_logo = Website Settings.app_logo or Navbar Settings.app_logo
#     if not app_logo:
#         logos = frappe.get_hooks("app_logo_url")
#         app_logo = logos[0]
#         if len(logos) == 2:
#             app_logo = logos[1]
#
# The hook branch is correct only at a list length of exactly two, which no app
# can guarantee, because the length depends on how many OTHER apps declare the
# same hook. Measured on dev.berp.bizera.la 2026-09-19:
#
#     get_hooks("app_logo_url") -> ['/assets/frappe/images/frappe-framework-logo.svg',
#                                   '/assets/erpnext/images/erpnext-logo.svg']
#     len == 2  ->  resolver picks logos[1]  ->  the ERPNEXT logo.
#
# Declaring the hook here would make that list three long, `len(logos) == 2`
# would be false, and the resolver would fall back to logos[0] — FRAPPE's logo.
# So the hook is not merely unreliable; on the exact shape bERP ships, adding it
# makes the fallback strictly worse.
#
# NOTE (changed when the app began shipping public/images/): the original reason
# for omitting this hook was that it would have served an asset that did not
# exist. That reason is gone — the asset now exists. The hook stays absent on the
# surviving reason above, which is positional unreliability. Test B9 in
# scripts/check_branding.py guards the absence.
#
# Branding is written to Website Settings AND Navbar Settings instead. Website
# Settings is what get_app_logo() checks first. Navbar Settings is needed
# separately because desk/page/desktop/desktop.py reads ONLY Navbar Settings and
# then falls back to frappe's own hook — it never consults Website Settings, so
# without this the legacy /desk page renders the Frappe logo. See brand.py.

# ─── Desk theme ───────────────────────────────────────────────────────────────
# A real bundle, not a raw /assets/ path. `bundled_asset()` passes a raw path
# straight through with no content hash and no cache-busting query, so a browser
# that cached it keeps serving the stale file after a deploy — which cost most of
# a session once already. A *.bundle.scss is compiled by `bench build` into a
# content-hashed file registered in assets.json. BERP-DS-001A §B5.2.
#
# This entry appends to the END of the aggregated app_include_css list, after
# frappe's and erpnext's, because berp_branding installs last. That source-order
# position is what lets the theme win at equal specificity with no !important.
app_include_css = "berp_desk.bundle.css"

# ─── Portal and Desk context ──────────────────────────────────────────────────
update_website_context = "berp_branding.brand.update_website_context"
boot_session = "berp_branding.brand.boot_session"

# ─── Setup ────────────────────────────────────────────────────────────────────
after_install = "berp_branding.brand.after_install"
after_migrate = "berp_branding.brand.after_migrate"
