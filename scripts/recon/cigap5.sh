#!/bin/bash
cd /home/frappe/frappe-bench || exit 1
D=$(ls -t sites/assets/frappe/dist/css/desk.bundle.*.css | grep -v map | head -1)
E=$(ls -t sites/assets/erpnext/dist/css/erpnext.bundle.*.css | grep -v map | head -1)
echo "=== RECONCILING the hex-literal count against DS-001A section A3 ==="
for f in "$D" "$E"; do
  echo "-- $(basename $f)  ($(wc -c < $f) bytes)"
  printf "   #hhh or #hhhhhh (3..6, DS-001A method) : %s\n" "$(grep -oE '#[0-9a-fA-F]{3,6}' "$f" | wc -l)"
  printf "   #hhhhhh only, word-bounded (my method) : %s\n" "$(grep -oE '#[0-9a-fA-F]{6}\b' "$f" | wc -l)"
  printf "   #hhh short form only                   : %s\n" "$(grep -oE '#[0-9a-fA-F]{3}([^0-9a-fA-F]|$)' "$f" | wc -l)"
  printf "   rgb()/rgba() literals                  : %s\n" "$(grep -oE 'rgba?\(' "$f" | wc -l)"
  printf "   var() references                       : %s\n" "$(grep -oE 'var\(' "$f" | wc -l)"
done
echo
echo "=== combined desk+erpnext ==="
printf "   3..6 form total : %s\n" "$(cat "$D" "$E" | grep -oE '#[0-9a-fA-F]{3,6}' | wc -l)"
printf "   6-digit total   : %s\n" "$(cat "$D" "$E" | grep -oE '#[0-9a-fA-F]{6}\b' | wc -l)"
echo
echo "NOTE: '#[0-9a-fA-F]{3,6}' is greedy-but-unanchored: it also matches the"
echo "      first 3 chars of a 6-digit value when followed by non-hex, and it"
echo "      matches inside url(#id) fragments. Checking that:"
printf "   occurrences of url(#  : %s\n" "$(cat "$D" "$E" | grep -oE 'url\(#' | wc -l)"
