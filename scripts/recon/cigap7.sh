#!/bin/bash
cd /home/frappe/frappe-bench
E=apps/erpnext/erpnext; F=apps/frappe/frappe
echo "=== does erpnext ship public/icons/desktop_icons/ ? ==="
ls -d $E/public/icons/desktop_icons 2>&1
echo "  erpnext/public/icons subdirs:"; ls -d $E/public/icons/*/ 2>/dev/null | sed 's/^/    /'
echo "  erpnext/public/icons top-level svg count: $(ls $E/public/icons/*.svg 2>/dev/null | wc -l)"
echo "  sample:"; ls $E/public/icons/ 2>/dev/null | head -8 | sed 's/^/    /'
echo
echo "=== frappe desktop_icons ==="
ls $F/public/icons/desktop_icons/ 2>/dev/null | head -8 | sed 's/^/    /'
echo "  count: $(ls $F/public/icons/desktop_icons/*.svg 2>/dev/null | wc -l)"
echo
echo "=== any path containing desktop_icons anywhere in assets ==="
find sites/assets -path '*desktop_icons*' 2>/dev/null | head -5
echo "  total: $(find sites/assets -path '*desktop_icons*' -name '*.svg' 2>/dev/null | wc -l)"
echo
echo "=== what src= paths do workspace/module icons actually use? ==="
grep -rhoE 'src="[^"]*icons/[^"]*"' $F/public/js $E/public/js 2>/dev/null | sort -u | head -10
echo "  -- img tags referencing /assets/*/icons in built js --"
grep -rhoE '/assets/[a-z_]+/icons/[a-zA-Z0-9_/.-]+' sites/assets/frappe/dist/js/*.js sites/assets/erpnext/dist/js/*.js 2>/dev/null | sort -u | head -12
