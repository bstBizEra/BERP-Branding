# CI gap probes — BERP-CI-GAP-001

Instruments that produced `BERP-CI-GAP-001 — ERPNext ↔ bERP Brand & CI Gap
Analysis`. Run inside the backend container:

    docker cp scripts/recon/<probe> <container>:/tmp/ && docker exec <container> bash /tmp/<probe>

| Probe | Measures |
|---|---|
| `cigap_tokens.py` | Upstream effective design values, both themes. **Self-checks first** against five independently verified bench values and prints its own failure count before any reading. |
| `cigap3.sh` | Structural ceiling — baked-in SVG fills, `desk.html` Jinja surface, literal distribution |
| `cigap4.sh` | Ramp consumption (the teal-collision test), `_()` coverage of identity strings, favicon/splash resolution |
| `cigap5.sh` | Reconciles this document's hex count against DS-001A §A3's different convention |
| `cigap7–10.sh` | Module-icon path, sprite `currentColor` census, and the icon-emission site |

**`docs/.recon/cigap.sh` is superseded and must not be re-run.** Its value match
used `[^;]*`, which runs past a block-final declaration into the next rule; it
reported three fabricated values. See BERP-CI-GAP-001 §1.

Per REVIEW-METHOD P2, a probe's negative or empty result is not trustworthy
until the probe has been validated against a known-good case. `cigap_tokens.py`
enforces this on itself; the shell probes do not, so read their empty results
with suspicion — `cigap7.sh`'s `find sites/assets -path '*desktop_icons*'`
returns 0 purely because `find` does not follow the assets symlink.
