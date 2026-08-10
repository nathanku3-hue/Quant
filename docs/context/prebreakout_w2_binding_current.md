# PREBREAKOUT W2 Binding — Current Immutable Authority

Date: 2026-08-10
Disposition: `CLOSED / IMMUTABLE SCIENTIFIC AUTHORITY / ZERO REAL MATERIAL TRIALS`
Family: `PREBREAKOUT_DISCOVERY_v1`
W2 authority version: `PREBREAKOUT_W2_CONTRACT_v1`

## Canonical scientific seal

```text
methodology_contract_sha256 = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
breakout_contract_sha256    = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
```

The two contract fields intentionally carry the **same** W2 seal in v1. Breakout B/B-1 is a frozen section of the single W2 scientific contract, not a separately mutable scientific authority.

Secondary implementation-byte custody, not a second scientific version:

```text
research/prebreakout_discovery_v1/preregistration.py sha256 = 3df15dce6e0c14ccf5e8ab65ecf66cadd212f28bc134f5c50ec7790ea9583214
research/prebreakout_discovery_v1/breakout.py        sha256 = 58951dc81a9f643b577e6ef201f3d2bc9751333e634d0932d94d1f9c8d43efe7
```

W4's deterministic envelope over the exact W2 snapshot is:

```text
prebreakout_atlas_methodology_binding_v1 binding_sha256
= 080aba6676202e68d14aff405049a2422d231dd7b8335f3be32f376b049205ad
```

That W4 binding hash is a downstream custody envelope; it does not replace or version W2.

## Frozen B / B-1 law

For one exact W3-authorized `CIQSEC + Trading Item` listing series, using observed sessions only:

```text
prior_high_20(t) = max(close[t-20], ..., close[t-1])

raw_breakout(t) = close[t] > prior_high_20(t)
```

Equality is not a breakout. The accepted algorithmic breakout session `B` is a raw breakout that also satisfies the frozen episode de-duplication law:

```text
if B_prev exists:
    accept new B only when session_index(B) - session_index(B_prev) > 20
```

Therefore at least 20 full observed sessions lie between accepted breakout episodes.

`B-1` is the immediately preceding observed trading session for the same exact listing. W2 never substitutes a calendar day, another listing, ticker identity, current survivor, or alternate listing.

For smoke/engineering proof:

```text
if W3 says PIT_ELIGIBLE_B_MINUS_1:
    a legitimate PREBREAKOUT flag must exist no later than B-1
    and inside the frozen TTFLD window B-20 ... B-1
else:
    W3 must provide one deterministic PIT exclusion reason
```

`DETERMINISTIC_UNAVAILABLE` is fail-closed and does not satisfy the current W2 smoke obligation. Actual per-security B/B-1 dates still require the legitimate W3/source series; absence of those source bytes is **not** an unbound W2 methodology state.

## Frozen labels / horizons / lead law

```text
risk_set_spec_id         = PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1
primary_label_spec_id    = PREBREAKOUT_RIGHT_TAIL_20D_TOP5_V1
secondary_label_spec_id  = PREBREAKOUT_RIGHT_TAIL_10D_TOP5_V1
primary_horizon          = 20 observed sessions
secondary_horizon        = 10 observed sessions
winner_fraction          = 0.05 date-local top tail
TTFLD window             = B-20 ... B-1
minimum legitimate lead = 1 observed session
miss effective TTFLD     = 0
```

## Search custody — closed at zero

```text
search_family_id    = PREBREAKOUT_SEARCH_v1
trial_ledger_scope  = PREBREAKOUT_V1_TRIAL_LEDGER
hard material budget = 8
real TRIAL_OPEN count = 0
real material trials consumed = 0/8
```

Repository inspection on 2026-08-10 found no non-test PREBREAKOUT Trial-Ledger file and no non-test `TRIAL_OPEN` evidence. Fixture/unit-test `TRIAL_OPEN` calls do not consume the real scientific budget.

**Do not issue real `TRIAL_OPEN #1`** until both prerequisites are frozen first:

1. the exact data/source manifest for Trial-1, including W3 PIT/source authority bindings; and
2. the exact Trial-1 implementation manifest, including implementation identity and code-byte custody.

Only after both manifests are immutable may the W2 ledger open Trial-1, and that open must bind the corresponding source/code identities before any result-bearing discovery label inspection.

## MU / SNDK law

```text
MU statistical weight   = 0
SNDK statistical weight = 0
special ticker branching = FORBIDDEN
promotion denominator weight = 0
```

The earlier W3 evidence receipt containing `BREAKOUT_CONTRACT_UNBOUND` is retained as historical custody describing the state when that receipt was created. It is **not current W2 state** and must not be cited as evidence that W2 remains unbound.

Current next dependency for MU/SNDK is W3/source refresh against this exact W2 seal and exact source-derived B/B-1 dates; no provider acquisition or outcome opening is authorized by this W2 closure.

## W3 / W4 / W5 handoff

W3 must consume:

```text
W2 authority version = PREBREAKOUT_W2_CONTRACT_v1
breakout_contract_sha256 = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
B/B-1 law = strict prior-20 high + 20-session episode cooldown + immediate prior observed B-1
```

W4 must consume:

```text
methodology_contract_sha256 = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
breakout_contract_sha256    = 94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71
binding_sha256              = 080aba6676202e68d14aff405049a2422d231dd7b8335f3be32f376b049205ad
```

W5 must consume the same W2 version/hash plus `20d` primary horizon, `B-20...B-1` lead law, and hard budget `8`. W5 may not run a real charged candidate until the Trial-1 source/data manifest and implementation manifest are frozen and W2 has then issued exactly one corresponding `TRIAL_OPEN`.

## Authority boundary

This closure changes no outcome state and creates no empirical evidence:

```text
provider acquisition            = NOT PERFORMED
real material search trial      = NOT OPENED
Atlas outcome open              = NOT PERFORMED
untouched lockbox open          = NOT PERFORMED
prospective clock start         = NOT AUTHORIZED
financial_alpha_evidence        = 0
capital_authority               = NONE
```
