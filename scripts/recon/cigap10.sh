#!/bin/bash
cd /home/frappe/frappe-bench
F=apps/frappe/frappe
echo "=== frappe.utils.desktop_icon — the emission site ==="
grep -n -A24 'desktop_icon(icon_name' $F/public/js/frappe/utils/utils.js 2>/dev/null | head -34 | sed 's/^/  /'
echo
echo "=== every template literal that builds a desktop_icons src ==="
grep -rhoE '.{0,40}(src|href)=[^>]{0,30}assets/\$\{[^}]*\}/icons/desktop_icons[^`"'"'"']{0,40}' $F/public/js 2>/dev/null | head -6 | sed 's/^/  /'
echo
echo "=== img tags emitted with desktop_icons, from the BUILT bundle ==="
cat sites/assets/frappe/dist/js/desk.bundle.*.js 2>/dev/null | grep -oE '<img[^>]{0,160}desktop_icons[^>]{0,60}' | head -6 | sed 's/^/  /'
cat sites/assets/frappe/dist/js/desk.bundle.*.js 2>/dev/null | grep -oE '.{80}icons/desktop_icons.{80}' | head -8 | sed 's/^/  /'
