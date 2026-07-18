# GV-FS0 F1C-SHIP Terminal Evidence

Mode: `CLOSURE_REPORT`
Date: 2026-07-19
Transport C: `48ad053dc21d7dda3c8280dcbd3c332584cc184a`
Authoritative candidate C2: `91b9bf1459439443298886ad6acc4a6181154431`
Base: `c37db092f092f00ad615109815bfacb13124c4da`
Hosted CI: `29651784244` PASS (Ubuntu, Windows, byte parity)
Status: `F1C_SHIP_CLOSED_ON_PRODUCT_BRANCH; SCORE_39_RETAINED`

## Two-SHA pattern executed

1. Materialize exact permanent bundle at `data/gv_fs0/gv_fs0_certified_bundle.json`
2. Local focused 202/202 + zero-new-failure floor
3. Candidate C = runtime/bundle/tests/workflow/cutover only
4. Push C as transport (not shipment claim)
5. Hosted Windows fail on CRLF then C2 `.gitattributes` LF pin then push C2 then workflow_dispatch
6. Hosted Ubuntu+Windows+parity PASS on C2
7. Distinct A/B/C on C and re-pin C2 PASS
8. Closeout T (this docs commit): SAW/truth + obsolete F1C/F1D split language removed as active gate

## Identity

| Field | Value |
|---|---|
| Bundle hash | `527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c` |
| Bundle ID | `BUNDLE_527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c` |
| Byte length | 55774 |
| File SHA-256 | `a9dda224da21ab4abfe1f27afdb2875bb34f240d469caf20a90b7e635adb96e5` |
| Roles | OPEN then NO_POSITION, both CERTIFIED |

## Boundary

No provider, real data, PEAD, broker/live capital, protocol redesign, main merge, or GV-FS1.
Official shipped-product score remains **39/100**.
