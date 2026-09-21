#!/usr/bin/env python3
"""
WCAG 2.2 contrast for the bERP token layer.

Used to DERIVE the dark semantic map rather than to check it afterwards
(BERP-DS-001A §B5.4: measured, never estimated). Run standalone to regenerate
the figures quoted in foundations/_semantic.scss:

    python scripts/contrast.py

The first block is an instrument check: it recomputes the five ratios CI-001 §6
publishes. If those do not match to two decimals, distrust everything below
them — the arithmetic is wrong, not the palette (REVIEW-METHOD P2).
"""


def _linear(channel: int) -> float:
	c = channel / 255.0
	return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
	h = hex_colour.lstrip("#")
	if len(h) == 3:
		h = "".join(ch * 2 for ch in h)
	r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
	return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def ratio(a: str, b: str) -> float:
	la, lb = luminance(a), luminance(b)
	hi, lo = max(la, lb), min(la, lb)
	return (hi + 0.05) / (lo + 0.05)


# CI-001 §6 published figures — the instrument control.
CI_001_PUBLISHED = {
	"#76CABB": 1.92,
	"#17997F": 3.56,
	"#117461": 5.68,
	"#595A5C": 6.90,
	"#414142": 10.20,
}

AA_NORMAL = 4.5
AA_LARGE = 3.0


def verdict(r: float) -> str:
	if r >= AA_NORMAL:
		return "PASS"
	if r >= AA_LARGE:
		return "large-only"
	return "FAIL"


def main() -> int:
	print("\n  Instrument check — computed vs CI-001 §6 published (vs white)")
	worst = 0.0
	for colour, published in CI_001_PUBLISHED.items():
		computed = ratio(colour, "#FFFFFF")
		delta = abs(computed - published)
		worst = max(worst, delta)
		print(f"    {colour}  computed {computed:6.2f}:1   published {published:6.2f}:1   Δ {delta:.3f}")
	if worst > 0.01:
		print(f"\n  INSTRUMENT FAILED: worst delta {worst:.3f} — do not trust derived values.")
		return 1
	print(f"    instrument OK (worst delta {worst:.3f})")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
