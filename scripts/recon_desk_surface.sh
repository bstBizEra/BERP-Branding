#!/usr/bin/env bash
# recon_desk_surface.sh — regenerate the BERP-DS-001A Part A surface inventory.
#
# Purpose
#   DS-001A records a measured baseline of the Frappe/ERPNext Desk override
#   surface. This script regenerates every figure in that baseline so an upgrade
#   can be diffed against it (DS-001A section C4, the upgrade drill).
#
# Usage
#   Run INSIDE the Frappe backend container / bench host:
#     bash recon_desk_surface.sh                  # human-readable
#     bash recon_desk_surface.sh > baseline.txt   # for diffing
#     SITE=dev.example.com bash recon_desk_surface.sh   # include live checks
#
#   The live section (hook resolution, Website/Navbar Settings) runs only when
#   SITE is set, because it opens a bench console.
#
# Contract
#   Read-only. Mutates nothing. Safe on production.

set -uo pipefail
BENCH="${BENCH:-/home/frappe/frappe-bench}"
cd "$BENCH" || { echo "FATAL: bench not found at $BENCH" >&2; exit 1; }
F=apps/frappe/frappe
E=apps/erpnext/erpnext

hr() { printf '\n%s\n' "== $* =="; }

hr "A0. ENVIRONMENT"
echo "bench: $BENCH"
echo "apps:  $(ls apps/ | tr '\n' ' ')"
echo "date:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"

hr "A1. INJECTION POINTS DECLARED BY FRAPPE / ERPNEXT / BERP_BRANDING"
for app in frappe erpnext berp_branding; do
  h="apps/$app/$app/hooks.py"
  [ -f "$h" ] || continue
  echo "--- $app ---"
  grep -nE "^(app_include_css|app_include_js|app_include_icons|web_include_css|web_include_js|website_theme_scss|app_logo_url|brand_html|add_to_apps_screen)" "$h" || echo "  (none declared)"
done

hr "A2. DESK HEAD: STYLESHEET MECHANISM"
grep -nE "app_include_css|app_include_js|app_include_icons|favicon|theme-color|splash_screen|app_name" $F/www/desk.html

hr "A3. TOKEN LAYERS (scss tree)"
printf "%-12s %10s %10s %10s\n" FOLDER UNIQUE_VARS HEX VAR_USES
for d in $F/public/scss/*/; do
  u=$(grep -rhoE -- "--[a-zA-Z0-9-]+[[:space:]]*:" "$d" 2>/dev/null | sort -u | wc -l)
  h=$(grep -rhoE "#[0-9a-fA-F]{3,8}\b" "$d" 2>/dev/null | wc -l)
  v=$(grep -rhoE "var\(--" "$d" 2>/dev/null | wc -l)
  printf "%-12s %10s %10s %10s\n" "$(basename "$d")" "$u" "$h" "$v"
done
echo "--- erpnext custom properties declared (expect 0) ---"
grep -rhoE -- "--[a-zA-Z0-9-]+[[:space:]]*:" $E/public/scss/ 2>/dev/null | sort -u | wc -l

hr "A4. BUILT DESK BUNDLE — HEADLINE COUNTS"
B=$(ls -t sites/assets/frappe/dist/css/desk.bundle.*.css 2>/dev/null | grep -v '\.map$' | head -1)
if [ -z "$B" ]; then
  echo "WARN: no built desk bundle found; run 'bench build' first"
else
  echo "bundle          : $B"
  echo "bytes           : $(wc -c < "$B")"
  echo "rule blocks (~) : $(grep -o '{' "$B" | wc -l)"
  echo "var() uses      : $(grep -o 'var(--' "$B" | wc -l)"
  echo "hex literals    : $(grep -oE '#[0-9a-fA-F]{3,8}\b' "$B" | wc -l)"
  echo "rgb/rgba lits   : $(grep -oE 'rgba?\([0-9]' "$B" | wc -l)"
  echo "custom props    : $(grep -oE -- '--[a-zA-Z0-9-]+[[:space:]]*:' "$B" | sort -u | wc -l)"
  echo ":root blocks    : $(grep -o ':root' "$B" | wc -l)"

  hr "A4b. LEVERAGE MAP — var() use counts (drives Tier 1 priority)"
  for v in primary primary-color brand-color btn-primary btn-height text-color \
           fg-color bg-color control-bg control-bg-on-gray border-color \
           border-radius navbar-bg navbar-height sidebar-width \
           sidebar-select-color sidebar-hover-color font-stack input-height \
           heading-color text-muted; do
    printf "  var(--%-22s %5s\n" "$v)" "$(grep -o "var(--$v[),]" "$B" | wc -l)"
  done

  hr "A5. LITERAL TAIL — hex census (Tier 2 workload)"
  grep -oE '#[0-9a-fA-F]{6}\b' "$B" | sort | uniq -c | sort -rn | head -20
fi

hr "A6. SURFACE INVENTORY — desk/*.scss"
printf "%-26s %7s %6s %7s\n" SURFACE LINES HEX VAR_USES
for f in $F/public/scss/desk/*.scss; do
  printf "%-26s %7s %6s %7s\n" "$(basename "$f")" \
    "$(wc -l < "$f")" \
    "$(grep -coE '#[0-9a-fA-F]{3,8}\b' "$f")" \
    "$(grep -coE 'var\(--' "$f")"
done

hr "A7. IDENTITY RESOLUTION PATHS"
echo "--- get_app_logo() resolver (positional trap) ---"
sed -n '/^def get_app_logo/,/^	return app_logo/p' $F/core/doctype/navbar_settings/navbar_settings.py
echo "--- legacy /desk page logo (Navbar Settings ONLY) ---"
grep -n "brand_logo" $F/desk/page/desktop/desktop.py
echo "--- splash constraint ---"
cat $F/templates/includes/splash_screen.html

hr "A8. THEME MODES — files declaring dark-theme blocks"
grep -rln '\[data-theme="dark"\]' $F/public/scss/ | sort

hr "A9. TYPOGRAPHY — fonts bundled by the desk bundle"
grep -n "fonts/" $F/public/scss/desk.bundle.scss

if [ -n "${SITE:-}" ]; then
  hr "LIVE CHECKS on $SITE"
  # bench console is IPython: its prompts are ANSI-coloured, so anchoring on
  # "^In [n]:" silently matches nothing and the section comes back empty.
  # Emit a sentinel and extract on that instead -- robust to prompts, colour
  # codes and any leading text.
  bench --site "$SITE" console <<'BENCHPY' 2>&1 | grep -o 'RECON|.*' | sed 's/^RECON|//'
import frappe
def r(k, v): print(f"RECON|{k}: {v}")
r("installed_apps", frappe.get_installed_apps())
r("app_include_css", frappe.get_hooks("app_include_css"))
r("app_include_js", frappe.get_hooks("app_include_js"))
logos = frappe.get_hooks("app_logo_url")
r("app_logo_url hooks", f"{logos} | len={len(logos)} | resolver picks: "
  f"{logos[1] if len(logos) == 2 else logos[0]}")
ws = frappe.get_single("Website Settings")
for f in ("app_name", "app_logo", "favicon", "splash_image", "banner_image"):
    r(f"WebsiteSettings.{f}", ws.get(f))
r("NavbarSettings.app_logo", frappe.db.get_single_value("Navbar Settings", "app_logo"))
from frappe.core.doctype.navbar_settings.navbar_settings import get_app_logo
r("get_app_logo()", get_app_logo())
BENCHPY
else
  hr "LIVE CHECKS skipped (set SITE=<sitename> to enable)"
fi

hr "END"
