/**
 * bERP brand — the surfaces CSS cannot reach.
 *
 * WHY THIS FILE EXISTS AT ALL
 * `frappe/www/desk.html` hardcodes the browser-chrome colour in its <head>:
 *
 *     <meta name="theme-color" content="#0089FF">
 *     <meta name="msapplication-navbutton-color" content="#0089FF">
 *
 * That is Frappe blue, it tints the address bar and task-switcher on Android
 * and Windows, and no stylesheet can touch a <meta> element. The usual Tier 3
 * answer — extend the template and override a block — is not available either:
 * measured on this version, `desk.html` contains ZERO `{% block %}` tags, so
 * `{% extends %}` would have nothing to override. Copying the file instead is
 * exactly the vendoring DS-001A §B4 prohibits.
 *
 * `app_include_js` is therefore the lowest available instrument, and a two-line
 * DOM write is the whole of it. BERP-DS-001A §B2, Stage 4.
 *
 * NO COLOUR IS HARDCODED HERE. The value is read back from the live token layer
 * so the meta tag can never drift from the theme (DS-001 §39). It also follows
 * the light/dark switch, which a static tag in the template never could — so
 * this ends up more correct than the markup it replaces, not merely rebranded.
 */
(() => {
	"use strict";

	// theme-color should match the surface ADJACENT to the browser chrome —
	// the navbar — not the brand accent. A saturated brand bar above a white
	// app reads as a rendering artefact on mobile.
	const SOURCE_TOKEN = "--berp-surface-default";
	const TARGETS = ["theme-color", "msapplication-navbutton-color"];

	// Deliberately NOT touched: apple-mobile-web-app-status-bar-style. That
	// property takes a KEYWORD (default | black | black-translucent), never a
	// colour, so upstream's `#0089FF` is an invalid value that Safari ignores —
	// it is already inert whatever the tag order. (desk.html declares the tag
	// twice, once with the hex and once with `white`; which one a browser
	// prefers was not measured, and this fix does not depend on it.) Writing a
	// colour here would propagate the original mistake rather than fix it.

	function currentSurface() {
		const value = getComputedStyle(document.documentElement)
			.getPropertyValue(SOURCE_TOKEN)
			.trim();
		return value || null;
	}

	function apply() {
		const colour = currentSurface();
		if (!colour) return; // token layer absent — leave upstream's value alone
		for (const name of TARGETS) {
			let tag = document.querySelector(`meta[name="${name}"]`);
			if (!tag) {
				tag = document.createElement("meta");
				tag.setAttribute("name", name);
				document.head.appendChild(tag);
			}
			if (tag.getAttribute("content") !== colour) {
				tag.setAttribute("content", colour);
			}
		}
	}

	apply();

	// Frappe's theme switcher flips data-theme on <html> at runtime. Without
	// this the chrome would keep the light surface colour behind a dark Desk.
	if (window.MutationObserver) {
		new MutationObserver(apply).observe(document.documentElement, {
			attributes: true,
			attributeFilter: ["data-theme", "data-theme-mode"],
		});
	}
})();
