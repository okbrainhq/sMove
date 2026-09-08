# R2 evidence scope

- `../parts.csv` / `../parts.json` select **49 fitted / 26 unique MPNs**; split CSVs separate main35/carrier14. Other captures record rejected/earlier candidates, not the final BOM.
- `../stock.json`: direct JLC exact-component `overseasStockCount`, JSON paths, UTC capture times, raw-body hashes and explicit five-set+spare planning counts. Presale and LCSC counts are not added; nothing reserved/ordered/uploaded.
- `C*.json` + `raw/C*.body.gz`: archived direct HTTP responses, parsed with the existing offline RSC parser. Duplicate price-tier records are not conflicting stock; price tiers live in stock.json. One initial C51118 rate-limit response was replaced by the successful bounded retry.
- `reused-primary.json` identifies archived primary BQ/ICM/ESP sources and compressed hashes. Focused BQ excerpts expose the pin7/8 conflict with the old generator. R2 must not copy that old map.
- `ap2112`, `pca9306`, `jst-ph` metadata/raw files are successful primary datasheet captures. Full text was not injected wholesale. Capacitor DC-bias/physical footprint validation remains for implementers.
- ICM current-datasheet request was blocked. `icm-eol` HTTP200 was **not a PDF**, so no EOL date/root cause is asserted. Failed switch/capacitor PDF attempts are retained as failures, not verification.
- Local PH4 and battery leads are explicitly unverified/manual-source acceptance items; see INTERFACE-MECHANICAL.md. No web-snippet quantity is promoted to live JLC stock.
- Offline reproduction: `python3 docs/revision-r2/build_handoff.py`. Direct recapture, only if later requested: `python3 docs/revision-r2/capture.py C...`; it writes only this R2 directory. No CAD exports or manufacturing release.
