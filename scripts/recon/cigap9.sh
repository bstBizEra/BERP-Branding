#!/bin/bash
cd /home/frappe/frappe-bench
F=apps/frappe/frappe
echo "=== how desktop_icons is used in sidebar.js / utils.js ==="
for f in $F/public/js/frappe/ui/sidebar/sidebar.js $F/public/js/frappe/ui/sidebar/sidebar_header.js $F/public/js/frappe/utils/utils.js; do
  echo "-- $(basename $f)"
  grep -n -B3 -A6 'desktop_icons' "$f" 2>/dev/null | head -30 | sed 's/^/    /'
done
echo
echo "=== built-bundle context (the served form) ==="
cat sites/assets/frappe/dist/js/desk.bundle.*.js 2>/dev/null | grep -oE '.{110}desktop_icons.{60}' | head -6 | sed 's/^/    /'
