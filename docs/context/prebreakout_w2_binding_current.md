# PREBREAKOUT W2 Binding — Current Immutable Authority

Date: 2026-08-10
Disposition: `CLOSED / IMMUTABLE HISTORICAL TRIAL-1 SCIENTIFIC AUTHORITY / TRIAL-1 CLOSED FAIL / PERMANENT 1_OF_8`
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

## Search custody — Trial #1 closed at permanent 1/8

```text
search_family_id              = PREBREAKOUT_SEARCH_v1
trial_ledger_scope            = PREBREAKOUT_V1_TRIAL_LEDGER
hard material budget          = 8
real TRIAL_OPEN count         = 1
real TRIAL_CLOSE count        = 1
real material trials consumed = 1/8
Trial #1 result               = FAILED
refund / reset                = FORBIDDEN
```

Trial #1 opened only after its exact source/data and implementation identities were frozen, and it closed exactly once after the frozen development evaluation. Open chain hash=`67999418489331536960f042de0dd96da12f1572fa6c6ab01e600914d1ef71a9`; close chain hash=`a3d9322eb05442f9fcdcd12f80a6a22d51b00d9edbc0635cc00841461871f9ee`. No second open occurred.

The old-family ledger remains immutable historical custody. It does not authorize Trial #2 or a successor rescue. `ECONPHYSICS_PREBREAKOUT_v1` is a separate scientific/search identity, with zero successor empirical-trial authority today.

## MU / SNDK law

```text
MU statistical weight   = 0
SNDK statistical weight = 0
special ticker branching = FORBIDDEN
promotion denominator weight = 0
```

The earlier W3 evidence receipt containing `BREAKOUT_CONTRACT_UNBOUND` is retained as historical custody describing the state when that receipt was created. It is **not current W2 state** and must not be cited as evidence that W2 remains unbound.

Real W3 authority later resolved the source/identity seam used by Trial #1. MU/SNDK remain zero-weight integration traces; their realized Trial-1 traces do not create promotion weight, special-case logic, or successor-mechanism authority.

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

W5 consumed the same W2 version/hash plus `20d` primary horizon, `B-20...B-1` lead law and hard budget `8`; Trial #1 is now closed `FAILED`. This W2 binding remains immutable historical authority and must not be edited to rescue the result.

## Authority boundary — current after Trial #1 close

```text
W3 real authority               = COMPLETE
real material search trial      = TRIAL_1_OPENED_AND_CLOSED_FAILED
Atlas development outcome open  = PERFORMED_AFTER_PREDICTION_FREEZE
W4 Atlas                        = COMPLETE_SEALED_FRESH_PROCESS_VERIFIED
W5 development                  = COMPLETE_ECONOMIC_FAIL
untouched W6 lockbox open       = FALSE
W6 labels open                  = FALSE
old-family Trial #2             = NOT AUTHORIZED
successor empirical trial today = NOT AUTHORIZED
prospective clock start         = NOT AUTHORIZED TODAY
financial_alpha_evidence        = 0
capital_authority               = NONE
```
