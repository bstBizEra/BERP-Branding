#!/bin/bash
cd /home/frappe/frappe-bench
F=apps/frappe/frappe; E=apps/erpnext/erpnext
echo "=== A. does anything REFERENCE desktop_icons? (source, not assets) ==="
echo "  in frappe py/js/html : $(grep -rIl 'desktop_icons' $F --include=*.py --include=*.js --include=*.html 2>/dev/null | wc -l) files"
grep -rIl 'desktop_icons' $F $E --include=*.py --include=*.js --include=*.html --include=*.json 2>/dev/null | head -8 | sed 's/^/    /'
echo "  in BUILT desk js     : $(grep -l 'desktop_icons' sites/assets/frappe/dist/js/*.js 2>/dev/null | wc -l) bundles"
echo "  raw occurrences in built js: $(cat sites/assets/frappe/dist/js/*.js 2>/dev/null | grep -o 'desktop_icons' | wc -l)"
echo
echo "=== B. how DOES a workspace/module icon render? ==="
echo "  -- frappe sidebar item template (sidebar/workspace js) --"
grep -rhoE '<(img|svg|use)[^>]{0,120}' $F/public/js/frappe/views/workspace/*.js 2>/dev/null | head -12 | sed 's/^/    /'
echo "  -- frappe.utils.icon helper --"
grep -rhA6 'frappe.utils.icon *= *function\|icon(icon_name' $F/public/js/frappe/utils/common.js 2>/dev/null | head -14 | sed 's/^/    /'
echo
echo "=== C. the icon sprite: how many symbols, and are they currentColor? ==="
for s in $F/public/icons/*/*.svg; do
  sym=$(grep -o '<symbol' "$s" 2>/dev/null | wc -l)
  [ "$sym" -gt 0 ] || continue
  printf "    %-56s symbols:%-4s hard-fill:%-4s currentColor:%s\n" "$(echo $s|sed 's|.*/icons/||')" "$sym" \
    "$(grep -oE '(fill|stroke)="#[0-9a-fA-F]{3,6}"' "$s"|wc -l)" \
    "$(grep -oE '(fill|stroke)="currentColor"' "$s"|wc -l)"
done
echo
echo "=== D. app_include_icons hooks (the sprite channel) ==="
grep -rn 'app_include_icons' $F/hooks.py $E/hooks.py 2>/dev/null | sed 's/^/    /'
echo
echo "=== E. what the ERPNext desktop_icons dir actually contains ==="
ls $E/public/icons/desktop_icons/ 2>/dev/null | head -6 | sed 's/^/    /'
echo "    count: $(ls $E/public/icons/desktop_icons/*.svg 2>/dev/null | wc -l)"
