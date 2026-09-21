# Copyright (c) 2026, BizEra / BSTBizEra and contributors
# License: GNU General Public License v3. See license.txt

"""
bERP platform branding, and per-tenant white-label over it.

Two layers, in the order BERP-WL-001 §4 requires:

    PLATFORM  the bERP identity this app ships in public/images/. A site that
              configures nothing shows bERP — not ERPNext. That is the whole
              point of the app.
    TENANT    site_config.json keys, laid over the platform layer, so one bench
              serves several tenants from the same code with no per-site fork.

    {
      "berp_brand_name":    "LaoCap ERP",
      "berp_brand_logo":    "/files/laocap-logo.svg",
      "berp_brand_favicon": "/files/laocap-favicon.png",
      "berp_brand_splash":  "/files/laocap-banner.png"
    }

Where the values actually have to land is not obvious, and getting it wrong is why
the first cut of this app only changed the portal navbar. Frappe resolves the Desk
and login logo through `get_app_logo()`:

    Website Settings.app_logo  ->  Navbar Settings.app_logo  ->  hooks app_logo_url

and the hook branch takes `logos[0]` unless exactly two apps declare it. Measured
on Frappe v16 2026-09-19: with frappe and erpnext declaring it and this app
declaring nothing, the list is two long and the fallback resolves to ERPNext's
logo; declaring it here would make the list three and send the fallback to
Frappe's. Either way the hook is not ours to win. The login page reads
`Website Settings.app_name` the same way. So the dependable place to put tenant
branding is **Website Settings**, which is what `apply_branding` writes.

One surface does not read Website Settings at all. `desk/page/desktop/desktop.py`
resolves its logo as Navbar Settings.app_logo, else
`get_hooks("app_logo_url", app_name="frappe")[0]` — Frappe's own, unconditionally.
So the legacy /desk page renders the Frappe logo however well Website Settings is
configured. `apply_branding` therefore writes Navbar Settings too. See
NAVBAR_LOGO_FIELD below.
"""

from html import escape

import frappe
from frappe import _
from frappe.utils import cint

DEFAULT_BRAND = "bERP"
MAX_BRAND_LENGTH = 120

#: Where this app's own assets are served from once `bench build` has run.
ASSET_ROOT = "/assets/berp_branding/images"

#: The bERP platform identity. This is what a site shows when site_config names no
#: tenant branding at all — the point of the app is that a fresh install presents
#: bERP, not ERPNext. Every one of these is overridable per tenant through the
#: site_config keys in BRAND_FIELDS.
#:
#: These paths MUST exist under berp_branding/public/; `bench build --app
#: berp_branding` is what publishes them. A default that points at a missing file
#: is worse than no default, because a broken image becomes the platform identity
#: (BERP-WL-001 §45). shipped_assets() checks them and branding_status() reports it.
PLATFORM_DEFAULTS = {
	"app_name": DEFAULT_BRAND,
	"app_logo": f"{ASSET_ROOT}/berp-logo.svg",
	"favicon": f"{ASSET_ROOT}/berp-favicon.png",
	# The Desk loading screen. Frappe renders
	#     {{ splash_image or "/assets/frappe/images/frappe-framework-logo.svg" }}
	# so leaving this unset means every bERP site shows the FRAPPE logo while the
	# Desk boots — the one moment a user stares at a blank screen and reads it.
	#
	# The mark, not a lockup: Frappe caps the splash at max-width 200px, and
	# CI-001 §3 puts the horizontal lockup's absolute minimum at 220px, below
	# which the tagline must not be preserved. CI-001 §3 also calls for a
	# dedicated small-size lockup without tagline as an official asset; the kit
	# has no such file, so the mark alone is the spec-correct choice here.
	"splash_image": f"{ASSET_ROOT}/berp-logo.svg",
}

#: site_config key -> Website Settings fieldname
#:
#: `berp_brand_splash` used to map to `banner_image`, which is the PORTAL banner,
#: not a splash of any kind. The name promised one surface and delivered another,
#: and it meant nothing was writing `splash_image` — the field Frappe actually
#: uses for the Desk loading screen. Corrected here, with `berp_brand_banner`
#: added for the portal banner it used to mean. Safe to change: no tenant has
#: these keys set, they are still proposed values in the README.
#: Navbar Settings.app_logo is written as a MIRROR of the resolved app_logo.
#:
#: Not because get_app_logo() needs it — that already prefers Website Settings —
#: but because desk/page/desktop/desktop.py reads Navbar Settings and nothing
#: else before falling back to Frappe's own hook. Measured on the dev bench:
#: Navbar Settings.app_logo was None, so that page rendered the Frappe logo while
#: every other surface showed bERP. Mirroring closes the last surface.
NAVBAR_LOGO_FIELD = "app_logo"

BRAND_FIELDS = {
	"berp_brand_name": "app_name",
	"berp_brand_logo": "app_logo",
	"berp_brand_favicon": "favicon",
	"berp_brand_splash": "splash_image",
	"berp_brand_banner": "banner_image",
}


# ─── Reading configuration ────────────────────────────────────────────────────


def brand_name() -> str:
	"""The tenant label, always a usable non-empty string."""
	label = frappe.conf.get("berp_brand_name")
	if not isinstance(label, str):
		return DEFAULT_BRAND
	return label.strip()[:MAX_BRAND_LENGTH] or DEFAULT_BRAND


def _brand_asset(key: str) -> str | None:
	"""
	A configured asset path, or None.

	Only site-relative paths and https URLs are accepted. A value that is neither
	is dropped rather than rendered: these end up in `src` attributes, and
	site_config is edited by hand.
	"""
	value = frappe.conf.get(key)
	if not isinstance(value, str):
		return None

	value = value.strip()
	if not value:
		return None

	if value.startswith("/") and not value.startswith("//"):
		return value
	if value.startswith("https://"):
		return value

	frappe.logger("berp_branding").warning(
		f"berp_branding: ignoring {key} — expected a site-relative path or an https URL, got {value!r}"
	)
	return None


def branding() -> dict:
	"""
	What this site should display: the bERP platform identity, with any tenant
	override laid over it.

	Resolution is PLATFORM_DEFAULTS <- site_config, which is the bottom two rungs
	of the BERP-WL-001 §4 chain (platform -> tenant -> company -> document). A key
	absent from site_config falls back to the platform default, never to ERPNext's.
	"""
	values = dict(PLATFORM_DEFAULTS)
	values["app_name"] = brand_name()
	for key, fieldname in BRAND_FIELDS.items():
		if fieldname == "app_name":
			continue
		asset = _brand_asset(key)
		if asset:
			values[fieldname] = asset
	return values


def shipped_assets() -> dict:
	"""
	Whether each platform default asset is actually on disk and served.

	Reports READY / MISSING / UNKNOWN and never collapses UNKNOWN into MISSING: a
	check that could not run has not found a defect. UNKNOWN here means the bench
	path could not be resolved, which is not the same as the file being absent.
	"""
	import os

	results = {}
	for fieldname, path in PLATFORM_DEFAULTS.items():
		if not path.startswith(ASSET_ROOT):
			continue
		try:
			site_path = frappe.get_site_path("..", "assets")
		except Exception:
			results[fieldname] = {"path": path, "status": "UNKNOWN"}
			continue
		relative = path[len("/assets/") :]
		results[fieldname] = {
			"path": path,
			"status": "READY" if os.path.exists(os.path.join(site_path, relative)) else "MISSING",
		}
	return results


# ─── Applying it ──────────────────────────────────────────────────────────────


@frappe.whitelist()
def apply_branding(force: int = 0) -> dict:
	"""
	Write the configured branding into Website Settings.

	This is what actually reaches the Desk navbar, the browser tab and the login
	page. It is idempotent and safe to re-run; `after_migrate` calls it so a
	site_config change takes effect on the next migrate.

	A value already set in Website Settings is left alone unless `force` is set,
	so an operator who set a logo by hand does not have it overwritten on every
	migrate. Nothing is ever blanked: a key absent from site_config means "leave
	this as it is", not "clear it".
	"""
	frappe.only_for("System Manager")

	settings = frappe.get_single("Website Settings")
	wanted = branding()
	changed = {}

	for fieldname, value in wanted.items():
		current = settings.get(fieldname)
		if current and not cint(force):
			continue
		if current == value:
			continue
		settings.set(fieldname, value)
		changed[fieldname] = value

	if changed:
		settings.flags.ignore_permissions = True
		settings.save()
		frappe.clear_cache()
		frappe.logger("berp_branding").info(f"berp_branding: applied branding {changed}")

	navbar_changed = _apply_navbar_logo(wanted.get("app_logo"), force=force)
	if navbar_changed:
		changed["navbar_settings.app_logo"] = navbar_changed

	return {"applied": changed, "configured": wanted, "site": frappe.local.site}


def _apply_navbar_logo(logo: str | None, force: int = 0) -> str | None:
	"""
	Mirror the resolved logo into Navbar Settings.

	The legacy /desk page reads this field and nothing else, so leaving it unset
	means that one page keeps the Frappe logo. Same force semantics as the
	Website Settings write: an operator's existing value is preserved unless
	forced, and nothing is ever blanked.

	Failure here must not fail the whole apply: Website Settings is the surface
	that matters, and this is a secondary mirror.
	"""
	if not logo:
		return None
	try:
		current = frappe.db.get_single_value("Navbar Settings", NAVBAR_LOGO_FIELD)
		if current and not cint(force):
			return None
		if current == logo:
			return None
		navbar = frappe.get_single("Navbar Settings")
		navbar.set(NAVBAR_LOGO_FIELD, logo)
		navbar.flags.ignore_permissions = True
		navbar.save()
		frappe.clear_cache()
		return logo
	except Exception as exc:  # pragma: no cover - defensive
		frappe.logger("berp_branding").warning(
			f"berp_branding: could not mirror logo into Navbar Settings: {exc}"
		)
		return None


def after_install():
	apply_branding(force=1)


def after_migrate():
	# Not forced: a migrate must not undo an operator's manual change.
	apply_branding()


# ─── Render-time context ──────────────────────────────────────────────────────


def update_website_context(context):
	"""Portal pages: navbar brand and application name."""
	label = brand_name()
	context["app_name"] = label
	context["brand_html"] = escape(label, quote=True)

	logo = _brand_asset("berp_brand_logo")
	if logo:
		context["app_logo"] = logo

	favicon = _brand_asset("berp_brand_favicon")
	if favicon:
		context["favicon"] = favicon


def boot_session(bootinfo):
	"""
	Expose the brand to Desk JavaScript.

	Frappe fills `bootinfo.app_logo_url` from Website Settings before this runs,
	so that value is already correct once `apply_branding` has run. `berp_brand`
	is added for client code that wants the label without re-deriving it.
	"""
	bootinfo.berp_brand = {"name": brand_name(), "site": frappe.local.site}
	_brand_boot_app_data(bootinfo)


#: Logos that mean "no bERP identity here" and may be replaced.
UPSTREAM_LOGOS = (
	"/assets/frappe/images/frappe-framework-logo.svg",
	"/assets/erpnext/images/erpnext-logo.svg",
)


def _brand_boot_app_data(bootinfo) -> None:
	"""
	Put the bERP mark into the Desk chrome.

	`bootinfo.app_logo_url` is NOT what the v16 Desk sidebar renders. Measured on
	the bench: `sidebar_header.js` falls back to

	    get_default_icon() { return frappe.boot.app_data[0].app_logo_url }

	and `boot.py` builds each `app_data` entry as

	    app_logo_url = <add_to_apps_screen logo>
	                   or get_hooks("app_logo_url", app_name=<this app>)
	                   or get_hooks("app_logo_url", app_name="frappe")

	Index 0 is `frappe`, so the Desk rendered the FRAPPE logo while the login
	page, the browser tab and the splash all showed bERP. A scan of the live Desk
	found zero images from this app.

	The third branch also returns a **list**, not a string — so any app that
	declares no `app_logo_url` of its own ends up with `["/assets/frappe/..."]`
	in a field the JavaScript uses directly as a URL. Both `berp_lao` and this
	app were in that state.

	Both are corrected here. `boot_session` runs after `boot.py` has assembled
	`app_data`, so this is a normal published hook doing normal work — no
	upstream file is touched and nothing depends on hook ordering between apps.

	An app that ships a mark of its own keeps it; only Frappe's and ERPNext's
	logos and the unconfigured list-valued fallback are replaced, because those
	are precisely the upstream identity this app exists to displace.
	"""
	logo = branding().get("app_logo")

	for app in bootinfo.get("app_data") or []:
		if logo:
			current = app.get("app_logo_url")
			if isinstance(current, list | tuple):
				# Unconfigured: boot.py handed back the hook list rather than a URL.
				current = current[0] if current else None
			if not current or current in UPSTREAM_LOGOS:
				app["app_logo_url"] = logo
			else:
				# Normalise, so a list never reaches the client even when kept.
				app["app_logo_url"] = current

		# boot.py assembles app_title from the `add_to_apps_screen` hook or the
		# `app_title` hook and passes it through NO translation, so the Desk
		# sidebar subtitle and the apps screen render the raw upstream name —
		# "ERPNext", "Frappe Framework" — however the site's language is set.
		#
		# Running it through _() here is deliberately the whole fix: it keeps the
		# app's translation CSVs as the single source of truth for brand strings
		# and simply applies the translation upstream omitted, rather than
		# hardcoding a second copy of the mapping in Python. A site that adds a
		# language adds a CSV; nothing here changes.
		title = app.get("app_title")
		if isinstance(title, str) and title:
			app["app_title"] = _(title)


# ─── Operator helper ──────────────────────────────────────────────────────────


@frappe.whitelist()
def branding_status() -> dict:
	"""
	Report what is configured, what is stored, and where the logo resolves from.

	Read-only. This is the call to run when a tenant says the branding looks wrong
	— it shows which of the three sources Frappe will actually use.
	"""
	frappe.only_for("System Manager")

	from frappe.core.doctype.navbar_settings.navbar_settings import get_app_logo

	settings = frappe.get_single("Website Settings")
	stored = {field: settings.get(field) for field in BRAND_FIELDS.values()}
	navbar_logo = frappe.db.get_single_value("Navbar Settings", "app_logo")

	if stored.get("app_logo"):
		source = "Website Settings"
	elif navbar_logo:
		source = "Navbar Settings"
	else:
		source = _("hooks app_logo_url (first app wins — usually Frappe's own logo)")

	return {
		"site": frappe.local.site,
		"configured": branding(),
		"stored_in_website_settings": stored,
		"navbar_settings_logo": navbar_logo,
		"resolved_logo": get_app_logo(),
		"resolved_from": source,
		"platform_defaults": PLATFORM_DEFAULTS,
		"shipped_assets": shipped_assets(),
	}
