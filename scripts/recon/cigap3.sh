#!/bin/bash
cd /home/frappe/frappe-bench || exit 1
F=apps/frappe/frappe; E=apps/erpnext/erpnext

echo "=== S1. BAKED-IN FILLS IN SHIPPED SVG (unreachable by CSS tokens) ==="
for d in $F/public/images $E/public/images $E/public/icons $F/public/icons; do
  [ -d "$d" ] || continue
  n=$(find $d -name '*.svg' 2>/dev/null | wc -l)
  hard=$(grep -rhoE '(fill|stroke)="#[0-9a-fA-F]{3,6}"' $d 2>/dev/null | wc -l)
  cur=$(grep -rhoE '(fill|stroke)="currentColor"' $d 2>/dev/null | wc -l)
  printf "  %-42s svg:%-4s hard-coded:%-5s currentColor:%s\n" "$d" "$n" "$hard" "$cur"
done
echo "  --- distinct hard-coded colours in erpnext desktop icons ---"
grep -rhoE '(fill|stroke)="#[0-9a-fA-F]{6}"' $E/public/icons 2>/dev/null | sed 's/.*"#/#/;s/"//' | sort | uniq -c | sort -rn | head -8
echo "  --- frappe icon sprite ---"
ls $F/public/icons/ 2>/dev/null | head
for s in $F/public/icons/*/*.svg; do :; done
echo "  timeless sprite symbols: $(grep -o '<symbol' $F/public/icons/timeless/symbol-defs.svg 2>/dev/null | wc -l)"
echo "  espresso sprite symbols: $(grep -o '<symbol' $F/public/icons/espresso/symbol-defs.svg 2>/dev/null | wc -l)"
for sp in $F/public/icons/*/symbol-defs.svg; do
  printf "  %-50s hard:%s currentColor:%s\n" "$sp" \
    "$(grep -oE '(fill|stroke)="#[0-9a-fA-F]{3,6}"' $sp | wc -l)" \
    "$(grep -oE '(fill|stroke)="currentColor"' $sp | wc -l)"
done

echo
echo "=== S2. desk.html TEMPLATE EXTENSION SURFACE ==="
D=$F/www/desk.html
echo "  file: $D  ($(wc -l < $D) lines)"
echo "  jinja {% block %} declarations: $(grep -c '{%-\? *block' $D)"
grep -oE '\{%-? *(extends|block|include) [^%]*%\}' $D | sed 's/^/    /'
echo "  hardcoded <meta> in desk.html:"
grep -oE '<meta[^>]*>' $D | head -8 | sed 's/^/    /'

echo
echo "=== S3. WHERE THE LITERALS LIVE (scss sources) ==="
cd $F/public/scss 2>/dev/null && {
  grep -rlE '#[0-9a-fA-F]{6}' . 2>/dev/null | head -0
  for f in $(grep -rlE '#[0-9a-fA-F]{6}' . 2>/dev/null); do
    printf "  %-52s %s\n" "$f" "$(grep -oE '#[0-9a-fA-F]{6}' $f | wc -l)"
  done | sort -k2 -rn | head -14
}

echo
echo "=== S4. IDENTITY STRINGS BAKED INTO PYTHON/JS (not translatable) ==="
cd /home/frappe/frappe-bench
printf "  erpnext py/js 'ERPNext' occurrences : %s\n" "$(grep -rI --include=*.py --include=*.js -o 'ERPNext' $E 2>/dev/null | wc -l)"
printf "  frappe  py/js 'Frappe' occurrences  : %s\n" "$(grep -rI --include=*.py --include=*.js -o 'Frappe' $F 2>/dev/null | wc -l)"
printf "  erpnext html 'ERPNext' occurrences  : %s\n" "$(grep -rI --include=*.html -o 'ERPNext' $E 2>/dev/null | wc -l)"
