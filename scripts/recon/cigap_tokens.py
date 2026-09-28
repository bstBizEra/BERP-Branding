#!/usr/bin/env python3
"""Extract Frappe/ERPNext's effective design values from built Desk CSS.

Instrument notes (REVIEW-METHOD P2):
  - a custom-property value terminates at ';' OR '}'. The previous shell probe
    used [^;]* which ran past a block-final declaration into the next rule.
  - declarations are attributed to their enclosing selector by brace-depth scan.
  - SELF-CHECK runs first against values already verified on this bench.
"""
import re, sys, os, json, glob
from collections import defaultdict, Counter

BENCH = "/home/frappe/frappe-bench"

def find_bundles():
    out = []
    for pat in ("sites/assets/frappe/dist/css/desk.bundle.*.css",
                "sites/assets/erpnext/dist/css/erpnext.bundle.*.css"):
        for p in glob.glob(os.path.join(BENCH, pat)):
            if p.endswith(".map"): continue
            out.append(p)
    return sorted(out)

DECL = re.compile(r"--([A-Za-z0-9_-]+)\s*:\s*([^;}]*?)\s*(?=[;}])")
SEL  = re.compile(r"([^{}@;]+)\{$")

def parse(css):
    """return {selector: {prop: value}} preserving source order (last wins)."""
    blocks = defaultdict(dict)
    stack = []            # selector stack
    i, n = 0, len(css)
    buf = []
    while i < n:
        c = css[i]
        if c == '{':
            sel = ''.join(buf).strip()
            buf = []
            stack.append(sel)
            i += 1
            continue
        if c == '}':
            buf = []
            if stack: stack.pop()
            i += 1
            continue
        if c == ';':
            decl = ''.join(buf).strip()
            m = DECL.match(decl + ';')
            if m and stack:
                blocks[stack[-1]][m.group(1)] = m.group(2)
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    return blocks

def collect(paths):
    merged = defaultdict(dict)
    raw = ""
    for p in paths:
        css = open(p, encoding="utf-8", errors="replace").read()
        raw += css
        for sel, props in parse(css).items():
            merged[sel.strip()].update(props)
    return merged, raw

def scope(merged, keys):
    out = {}
    for sel, props in merged.items():
        s = sel.replace(" ", "")
        if s in keys or any(s.endswith(","+k) or s.startswith(k+",") or ","+k+"," in s for k in keys):
            for k2, v in props.items():
                out.setdefault(k2, v)
                out[k2] = v
    return out

VAR = re.compile(r"var\(\s*--([A-Za-z0-9_-]+)\s*(?:,([^()]*))?\)")
def resolve(val, table, depth=0):
    if depth > 12 or not val: return val
    def sub(m):
        name, fb = m.group(1), (m.group(2) or "").strip()
        if name in table: return resolve(table[name], table, depth+1)
        return fb if fb else m.group(0)
    new = VAR.sub(sub, val)
    return new if new == val else resolve(new, table, depth+1)

def main():
    paths = find_bundles()
    merged, raw = collect(paths)
    light = scope(merged, {":root", "[data-theme=light]", '[data-theme="light"]'})
    dark  = scope(merged, {"[data-theme=dark]", '[data-theme="dark"]'})
    ltab, dtab = dict(light), dict(light); dtab.update(dark)

    # ---------- SELF-CHECK ----------
    checks = [("border-radius-sm","8px",ltab),("navbar-height","48px",ltab),
              ("list-row-height","30px",ltab),("text-base","14px",ltab),
              ("padding-md","15px",ltab)]
    print("=== SELF-CHECK (values already verified on this bench) ===")
    bad = 0
    for k, want, t in checks:
        got = resolve(t.get(k,"<missing>"), t)
        ok = got == want
        bad += (not ok)
        print(f"  {'PASS' if ok else 'FAIL'}  --{k:<18} want {want:<8} got {got}")
    print(f"  bundles: {[os.path.basename(p) for p in paths]}")
    print(f"  :root-scope props: {len(light)}   dark-scope props: {len(dark)}")
    if bad:
        print(f"  !! {bad} self-check failures — readings below are NOT trustworthy")
    print()

    def show(title, names, table, width=22):
        print(f"=== {title} ===")
        for nm in names:
            rawv = table.get(nm)
            if rawv is None:
                print(f"  --{nm:<{width}} (not declared)")
            else:
                rv = resolve(rawv, table)
                extra = f"   <- {rawv}" if rv != rawv else ""
                print(f"  --{nm:<{width}} {rv}{extra}")
        print()

    print("########## LIGHT THEME (:root) ##########\n")
    show("A. CORE COLOUR", ["primary","primary-color","text-color","text-light",
        "text-muted","heading-color","bg-color","fg-color","subtle-fg","control-bg",
        "border-color","border-primary","disabled-text-color","text-on-dark-bg",
        "btn-primary","sidebar-active-color","brand-color","navbar-bg"], ltab, 24)

    ramps = defaultdict(dict)
    for k, v in ltab.items():
        m = re.match(r"^(gray|blue|green|red|yellow|orange|purple|pink|cyan|teal|dark|neutral)-(\d+)$", k)
        if m: ramps[m.group(1)][int(m.group(2))] = resolve(v, ltab)
    print("=== A2. PRIMITIVE RAMPS ===")
    for fam in sorted(ramps):
        steps = " ".join(f"{s}:{ramps[fam][s]}" for s in sorted(ramps[fam]))
        print(f"  {fam:<8} {steps}")
    print()

    show("B. SEMANTIC STATE", ["alert-bg-success","alert-bg-danger","alert-bg-warning",
        "alert-bg-info","alert-text-success","alert-text-danger","alert-text-warning",
        "alert-text-info","success","error","warning","info"], ltab, 22)

    print("=== B2. HARD-CODED HEX LITERALS IN BUILT CSS ===")
    hexes = Counter(h.lower() for h in re.findall(r"#([0-9a-fA-F]{6})\b", raw))
    print(f"  distinct 6-digit literals: {len(hexes)}   total occurrences: {sum(hexes.values())}")
    for h, c in hexes.most_common(20):
        print(f"    #{h}  x{c}")
    print()

    show("C. TYPOGRAPHY", ["font-stack","text-xs","text-sm","text-base","text-md",
        "text-lg","text-xl","text-2xl","text-3xl","weight-regular","weight-medium",
        "weight-semibold","weight-bold"], ltab, 18)
    print("=== C2. font-family DECLARATIONS ===")
    fams = Counter(f.strip()[:100] for f in re.findall(r"font-family\s*:\s*([^;}]+)", raw))
    for f, c in fams.most_common(8): print(f"    x{c:<4} {f}")
    print()

    show("D. SPACING", [f"{p}-{s}" for p in ("padding","margin")
         for s in ("xs","sm","md","lg","xl","2xl")], ltab, 16)
    show("E. RADIUS", ["border-radius","border-radius-sm","border-radius-md",
        "border-radius-lg","border-radius-xl","border-radius-full"], ltab, 20)
    show("F. DIMENSION / DENSITY", ["btn-height","btn-height-sm","input-height",
        "input-height-sm","list-row-height","navbar-height","page-head-height",
        "sidebar-width","checkbox-size","icon-xs","icon-sm","icon-md","icon-lg"], ltab, 20)
    show("G. ELEVATION", ["shadow-xs","shadow-sm","shadow-base","shadow-md",
        "shadow-lg","shadow-xl","modal-shadow","card-shadow"], ltab, 16)

    print("########## DARK THEME DELTA ##########\n")
    print("=== tokens redeclared under [data-theme=dark] ===")
    for k in sorted(dark):
        print(f"  --{k:<26} {resolve(dark[k], dtab)}")
    print()

if __name__ == "__main__":
    main()
