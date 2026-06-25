# Discovery Origin Taxonomy

Status: G8.1A taxonomy contract
Authority: Phase 65 G8.1A Discovery Drift Correction
Date: 2026-05-10

## Origin Values

The approved discovery-origin values are:

```text
USER_SEEDED
THEME_ADJACENT
SUPPLY_CHAIN_ADJACENT
PEER_CLUSTER
CUSTOMER_SUPPLIER_LINK
ETF_HOLDING_LINK
SEC_INDUSTRY_LINK
NEWS_RESEARCH_CAPTURE
LOCAL_FACTOR_SCOUT
SYSTEM_SCOUTED
```

## Meanings

`USER_SEEDED` means the user supplied the name directly.

`THEME_ADJACENT` means the name is adjacent to an approved theme, but the system has not proven it.

`SUPPLY_CHAIN_ADJACENT` means the name is adjacent to an approved supply-chain path, but the system has not proven it.

`PEER_CLUSTER`, `CUSTOMER_SUPPLIER_LINK`, `ETF_HOLDING_LINK`, and `SEC_INDUSTRY_LINK` are reserved for later governed discovery paths.

`NEWS_RESEARCH_CAPTURE` records research or narrative capture only. It is not canonical evidence.

`LOCAL_FACTOR_SCOUT` is defined for G8.1B, but it is not used in G8.1A.

`SYSTEM_SCOUTED` means a governed system pipeline emitted the name with a manifest-backed scout path. No current G8.1A seed name is system-scouted.

## Boolean Contract

Origin booleans must agree with the origin labels:

```text
USER_SEEDED -> is_user_seeded = true
SYSTEM_SCOUTED -> is_system_scouted = true
```

For G8.1A, user-seeded and system-scouted are mutually exclusive.

## Evidence Contract

`origin_evidence` must be present and non-empty, but it is provenance evidence only. It does not validate the thesis, make a candidate actionable, or promote a candidate into a card.
