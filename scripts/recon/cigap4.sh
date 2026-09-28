#!/bin/bash
cd /home/frappe/frappe-bench || exit 1
F=apps/frappe/frappe; E=apps/erpnext/erpnext
B=$(ls -t sites/assets/frappe/dist/css/desk.bundle.*.css | grep -v map | head -1)

echo "=== T1. IS FRAPPE'S OWN TEAL RAMP CONSUMED? (collision risk with CI-001 teal) ==="
for n in 50 100 200 300 400 500 600 700 800 900; do
  c=$(grep -o "var(--teal-$n)" $B | wc -l)
  printf "  var(--teal-%-3s referenced %s times\n" "$n)" "$c"
done
echo "  --- which upstream tokens point at frappe teal ---"
grep -oE -- '--[a-z0-9-]+: *var\(--teal-[0-9]+\)' $B | sort -u | sed 's/^/    /' | head
echo "  --- other accent ramps actually consumed ---"
for fam in blue green red yellow orange purple pink cyan; do
  printf "    %-8s %s refs\n" "$fam" "$(grep -o "var(--$fam-[0-9]*)" $B | wc -l)"
done

echo
echo "=== T2. 'ERPNext' STRINGS: TRANSLATABLE vs BAKED ==="
tr_count=$(grep -rIhoE '_\(\s*["'"'"'][^"'"'"']*ERPNext[^"'"'"']*["'"'"']' $E --include=*.py --include=*.js 2>/dev/null | wc -l)
all_str=$(grep -rIhoE '["'"'"'][^"'"'"']*ERPNext[^"'"'"']*["'"'"']' $E --include=*.py --include=*.js 2>/dev/null | wc -l)
echo "  string literals containing 'ERPNext'     : $all_str"
echo "  of those wrapped in _() (translatable)   : $tr_count"
echo "  --- distinct translatable strings (top) ---"
grep -rIhoE '_\(\s*["'"'"'][^"'"'"']*ERPNext[^"'"'"']*["'"'"']' $E --include=*.py --include=*.js 2>/dev/null \
  | sed -E 's/^_\(\s*.//; s/.$//' | sort | uniq -c | sort -rn | head -12 | sed 's/^/    /'
echo "  --- non-_() UI-reaching strings (json labels / doctype names) ---"
grep -rIhoE '"(label|title|description)": *"[^"]*ERPNext[^"]*"' $E 2>/dev/null | sort -u | head -8 | sed 's/^/    /'

echo
echo "=== T3. WORKSPACE / MODULE ICON INVENTORY ==="
echo "  erpnext desktop_icons: $(ls $E/public/icons/*.svg 2>/dev/null | wc -l)"
ls $F/public/icons/desktop_icons/*.svg 2>/dev/null | wc -l | sed 's/^/  frappe desktop_icons: /'
echo "  workspaces shipped by erpnext: $(find $E -path '*workspace*' -name '*.json' 2>/dev/null | wc -l)"
echo "  --- icon field values used by erpnext workspaces (top) ---"
find $E -path '*workspace*' -name '*.json' -exec grep -ho '"icon": *"[^"]*"' {} \; 2>/dev/null | sort | uniq -c | sort -rn | head -8 | sed 's/^/    /'

echo
echo "=== T4. FAVICON / APP IDENTITY RESOLUTION ==="
grep -rn 'favicon' $F/www/desk.html $F/templates/includes/*.html 2>/dev/null | head -5 | sed 's/^/  /'
echo "  website_settings favicon field exists: $(grep -c favicon $F/website/doctype/website_settings/website_settings.json 2>/dev/null)"
echo "  splash screen html:"
sed -n '1,20p' $F/templates/includes/splash_screen.html 2>/dev/null | grep -oE '<(img|svg|div)[^>]*' | head -5 | sed 's/^/    /'
