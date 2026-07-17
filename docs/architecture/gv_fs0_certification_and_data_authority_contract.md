# GV-FS0 Certification, Canonicalization, and Data-Authority Protocol V1

Status: Conditional final approval; freeze artifact candidate
Date: 2026-07-17
Mode: `EXECUTION_PACKET`
Protocol ID: `GV_FS0_PROTOCOL_V1`
Authority: `docs/architecture/top_level_roadmap.md`, `docs/architecture/godview_endgame_vision.md`, `docs/architecture/godview_portfolio_first_operating_model.md`, `docs/architecture/godview_portfolio_p0_owner_freeze.md`, and the GV-FS0 final approval audit dated 2026-07-17

## 0. Authority and Freeze State

The GV-FS0 P0-P4 design is approved. This document is the single normative consolidation of the approved protocol clauses. Earlier planning patches and audit drafts are historical evidence only and have no independent runtime authority.

The protocol freeze becomes effective only after all of the following are complete:

1. the machine-readable V1 schemas, registries, event ranks, generated-event slots, transition-ownership definitions, and canonical vectors are generated from this contract;
2. the protocol and golden tests pass;
3. exact hashes for every frozen V1 artifact are recorded;
4. CI rejects unreviewed same-version changes; and
5. the protocol-freeze commit receives a clean audit result.

Until those conditions pass, the following remain blocked:

- economic event reduction;
- production `PortfolioBook` mutation logic;
- snapshot generation over the FS0 fixtures;
- certification of the FS0 fixtures;
- certified decision components;
- permanent certified-bundle publication;
- Streamlit product integration; and
- any GV-FS1 or real-data work.

The only implementation scope authorized before the freeze becomes effective is protocol-level proof:

- canonical encoders and raw-token parsing;
- exact schemas and registries;
- canonical vectors;
- event-rank, generated-slot, and transition-ownership definitions;
- verifier supervision primitives; and
- protocol tests.

Phase 0 repository and V2 line-ending hygiene remains a separate commit boundary and must not be mixed with this protocol boundary.

## 1. Purpose and Product Boundary

GV-FS0 proves one minimal end-to-end authority chain for both action and abstention:

```text
DecisionEnvelope
-> one-decision PortfolioBook
-> Fs0PortfolioSnapshot series
-> two independent verifier attempts
-> Fs0Certification
-> certification-reference event
-> certified decision result
-> final two-component certified bundle
-> read-only Streamlit adapter
```

The two decisions are:

```text
MANUAL_OWNER_PAPER / OPEN
MANUAL_OWNER_PAPER / NO_POSITION
```

OPEN and NO_POSITION use separate decisions, separate one-decision books, separate event trails, separate snapshot series, and separate certifications. The final bundle aggregates the two certified decision results; it never merges them into one book or one certification.

Only `PortfolioBook` may own primary FS0 economic state. Only `Fs0Certification` may declare a decision result certified. The UI is a read-only consumer and owns no accounting or certification truth.

GV-FS0 does not authorize:

- provider or network access;
- real or licensed data;
- real candidate admission;
- benchmarks or IWB integration;
- optimizers or challenger policies;
- multiple securities;
- leverage, shorts, derivatives, or live capital;
- 252-session replay;
- broad corporate actions;
- WRDS-dependent PEAD reopening;
- alpha, tradability, or investment claims; or
- new product navigation.

## 2. Normative Artifact Set

The V1 freeze must produce exact machine-readable definitions for:

```text
gv_fs0_source_fixture_v1
gv_fs0_decision_envelope_v1
gv_fs0_source_intent_v1
gv_fs0_portfolio_event_v1
gv_fs0_snapshot_v1
gv_fs0_verifier_input_v1
gv_fs0_verifier_result_v1
gv_fs0_verifier_attempt_v1
gv_fs0_certification_v1
gv_fs0_certified_decision_result_v1
gv_fs0_certified_bundle_v1
gv_fs0_blocked_evidence_v1
gv_fs0_certification_failure_registry_v1
gv_fs0_operational_error_registry_v1
gv_fs0_event_ranks_v1
gv_fs0_generated_event_slots_v1
gv_fs0_transition_ownership_v1
gv_fs0_canonical_vectors_v1
```

All JSON Schemas use JSON Schema Draft 2020-12:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema"
}
```

All object schemas set `additionalProperties` to `false`. Duplicate JSON object keys are prohibited before schema validation. Correctness must not depend on implementation-specific `format` validation; timestamps, dates, decimals, integers, hashes, IDs, and other constrained fields use explicit patterns plus repository-owned semantic validation.

Field counts are consequences of the schemas. A prose field count is never an independent governing contract.

## 3. Canonical JSON Document Protocol

### 3.1 Encoding and document framing

Every canonical JSON document uses:

```text
encoding                 UTF-8
byte-order mark          prohibited
line ending              LF
terminal newline         exactly one LF
JSON whitespace          none outside string values
object-key order         ascending Unicode scalar-value order after field validation
array order              preserved schema-defined semantic order
duplicate object keys    prohibited
unknown object fields    prohibited unless a schema explicitly allows them
```

A canonical document is constructed exactly as:

```python
canonical_json_document_bytes = (
    canonical_json_text.encode("utf-8")
    + b"\n"
)
```

`canonical_json_text` contains no newline or whitespace after its closing JSON token. The resulting document ends in exactly one LF.

### 3.2 Semantic string preparation

Before normalization or JSON string encoding, validate the raw code points.

For descriptive fields:

```text
validate raw code points
-> reject surrogates
-> reject prohibited Unicode noncharacters
-> normalize to NFC
-> validate the normalized result again
-> canonical-encode
```

For identity-bearing fields:

```text
validate raw code points
-> reject surrogates
-> reject prohibited Unicode noncharacters
-> compute NFC
-> require exact equality with the supplied value
-> validate the result again
-> canonical-encode
```

A normalization library must never receive an unvalidated surrogate or prohibited noncharacter.

Reject every surrogate code point:

```text
U+D800-U+DFFF
```

Reject Unicode noncharacters:

```text
U+FDD0-U+FDEF
and every code point whose low 16 bits are FFFE or FFFF
```

### 3.3 Exact JSON string escaping

Canonical string encoding applies identically to object keys and string values.

Always escape:

```text
U+0022 quotation mark       -> \"
U+005C reverse solidus      -> \\
```

Use exactly these short escapes:

```text
U+0008 -> \b
U+0009 -> \t
U+000A -> \n
U+000C -> \f
U+000D -> \r
```

Every other control character in U+0000-U+001F uses lowercase four-digit form:

```text
\u00xx
```

Examples:

```text
U+0000 -> \u0000
U+000B -> \u000b
U+001F -> \u001f
```

The solidus `/` is emitted literally and is never escaped. U+2028 and U+2029 are emitted directly as UTF-8. All other valid non-ASCII scalar values, including CJK and non-BMP emoji, are emitted directly as UTF-8. Non-BMP characters are never encoded as UTF-16 surrogate-pair escapes.

Canonical output must not rely on a language JSON encoder's defaults for string escaping, ASCII escaping, solidus handling, U+2028/U+2029, surrogate handling, non-BMP handling, or hexadecimal letter case.

### 3.4 Canonical integers

Canonical integers are JSON numbers, not strings.

The only accepted raw source-token grammar is:

```regex
^(0|[1-9][0-9]*)$
```

Prohibited forms include:

```text
-0
-1
+1
00
01
1.0
1e0
1E0
```

Raw integer-token spelling must be validated before conversion to a host-language number. A parser that has already converted `1.0`, `1e0`, or `01` to mathematical value 1 is insufficient.

All V1 canonical integer fields are unsigned. The global maximum is:

```text
9007199254740991
```

Schemas impose smaller field-specific maxima where practical. Canonical output is the minimal unsigned ASCII decimal representation with no sign, leading zero, decimal point, exponent, whitespace, or string quoting.

The rule applies to fields including:

```text
ordinal
source_sequence
generated_event_slot
event_type_rank
intra_rank_sequence
semantic_sequence
check_rank
outcome_rank
```

### 3.5 Canonical decimals

Decimal economic values are JSON strings containing plain base-10 notation.

Prohibited:

- JSON numeric floats;
- exponent notation;
- leading `+`;
- NaN or infinity;
- negative zero in any representation.

Field domains:

```text
cash, fees, prices, receivables, market value, NAV, contribution
    quantum = 0.000001 currency units

dividend amount per share
    quantum = 0.000001 currency units per share

shares
    canonical non-negative integer under the integer protocol
```

Excess trailing decimal zeros are accepted and canonicalized:

```text
"1.230000"  -> "1.23"
"1.2300000" -> "1.23"
"0.000000"  -> "0"
```

A nonzero digit beyond the field quantum is invalid rather than rounded:

```text
"1.2300001" -> invalid
"0.0000004" -> invalid
```

`ROUND_HALF_EVEN` may be used internally only to assert exact representability. Canonicalization must never silently alter a value that requires rounding. Canonical zero is `"0"`.

### 3.6 Canonical timestamps and dates

Canonical timestamps use exactly:

```text
YYYY-MM-DDTHH:MM:SS.ffffffZ
```

Rules:

- timezone awareness is mandatory;
- numeric offsets may be accepted only when losslessly normalizable to UTC;
- canonical output always uses `Z`;
- exactly six fractional digits are emitted;
- input precision greater than microseconds is rejected;
- leap seconds are rejected;
- naive timestamps are rejected.

Session dates use exactly `YYYY-MM-DD` and are validated separately.

Canonical certification time is derived from terminal valuation authority:

```text
certification_session = terminal_snapshot.session
certification_effective_timestamp = terminal_snapshot.valuation_timestamp
```

The certification-reference event uses the same deterministic session and timestamp. Causal placement after valuation comes from event rank 90, not a fabricated wall-clock time.

Canonical objects must not contain `checked_at`, `generated_at`, `completed_at`, runtime durations, process start/end times, current wall-clock time, or file modification time. Operational evidence may contain such observations outside canonical product identity.

## 4. Domain-Separated Hashing

### 4.1 Exact framing

Every canonical hash preimage is constructed exactly as:

```python
hash_preimage = (
    domain_prefix.encode("utf-8")
    + b"\n"
    + canonical_json_document_bytes
)
```

`domain_prefix` contains no LF. `canonical_json_document_bytes` already ends with exactly one LF. No additional byte is appended.

Every hash uses SHA-256 and lowercase 64-character hexadecimal output.

Golden tests must assert:

1. canonical JSON text;
2. canonical document bytes;
3. the complete domain-separated preimage bytes;
4. the preimage byte length; and
5. the resulting digest.

### 4.2 V1 domains

Required domains include:

```text
GV-FS0:FIXTURE:V1
GV-FS0:DECISION_ENVELOPE:V1
GV-FS0:BOOK_ID:V1
GV-FS0:PORTFOLIO_EVENT_ID:V1
GV-FS0:SNAPSHOT_ID:V1
GV-FS0:ECONOMIC_PAYLOAD:V1
GV-FS0:VERIFIER_INPUT:V1
GV-FS0:VERIFIER_RESULT:V1
GV-FS0:CERTIFICATION_FAILURE_REGISTRY:V1
GV-FS0:OPERATIONAL_ERROR_REGISTRY:V1
GV-FS0:CERTIFICATION_ID:V1
GV-FS0:CERTIFICATION_REFERENCE_EVENT_ID:V1
GV-FS0:CERTIFIED_DECISION_RESULT:V1
GV-FS0:PRESENTATION:V1
GV-FS0:CERTIFIED_BUNDLE:V1
```

A semantic hash change requires a new domain version.

## 5. Acyclic Identity Graph

The normative dependency graph is:

```text
fixture_hash
    -> decision_hash
    -> book_id
    -> economic event IDs
    -> canonical economic event order and semantic sequences
    -> snapshot IDs
    -> economic_payload_hash
    -> verifier_input_hash
    -> verifier attempt 1 result or stable infrastructure outcome
    -> verifier attempt 2 result or stable infrastructure outcome
    -> ordered verifier_attempts
    -> certification_id
    -> certification-reference event ID
    -> terminal event order and reference semantic sequence
    -> certified_decision_result_hash
    -> presentation_hash
    -> bundle_hash
    -> bundle_id
```

Every object hash excludes:

- its own ID or hash field;
- downstream references;
- runtime metadata;
- filesystem paths;
- environment values;
- host or user identity;
- operational timestamps.

### 5.1 Fixture hash

`fixture_hash` derives from the canonical source fixture payload under `GV-FS0:FIXTURE:V1`. It excludes generated events, snapshots, verifier outputs, certifications, components, and bundle content. The human-readable `fixture_id` remains in the preimage.

### 5.2 Decision hash

`decision_hash` derives from the complete canonical `DecisionEnvelope` under `GV-FS0:DECISION_ENVELOPE:V1`. It excludes only its own hash and downstream generated references. It includes `fixture_hash`.

### 5.3 Book ID

A book is identified before events exist. Its preimage is:

```text
protocol_id
fixture_id
fixture_hash
decision_id
decision_hash
```

Identity:

```text
BOOK_<64-character digest>
```

A book ID never derives from events, snapshots, certification, or bundle content.

### 5.4 Event IDs

An event ID uses `GV-FS0:PORTFOLIO_EVENT_ID:V1` and the provenance-sensitive preimage defined in Section 8. It excludes `event_id`, global `semantic_sequence`, runtime metadata, and downstream identities.

Identity:

```text
EVT_<64-character digest>
```

### 5.5 Snapshot IDs

A snapshot ID uses `GV-FS0:SNAPSHOT_ID:V1` and includes:

```text
book_id
decision_id
fixture_hash
session
valuation_timestamp
applied economic event IDs
shares
cash
receivables
market_value
NAV
session_contribution
cumulative_contribution
```

It excludes `snapshot_id`, certifications, certification-reference events, presentation, components, and bundle fields.

Identity:

```text
SNAP_<64-character digest>
```

### 5.6 Economic payload hash

The economic payload includes:

- protocol identity;
- fixture identity and hash;
- decision identity and hash;
- book ID;
- ordered economic event IDs;
- ordered snapshots; and
- terminal snapshot ID.

It excludes certification, certification-reference events, presentation, component identities, bundle identities, and UI state.

### 5.7 Certification ID

The certification-ID preimage is defined in Section 12. It excludes its own ID, the certification-reference event, display-only failure lists, operational diagnostics, component identities, and bundle fields.

Identity:

```text
CERT_<64-character digest>
```

### 5.8 Certification-reference event ID

The reference-event preimage includes:

```text
schema_version
book_id
decision_id
terminal_snapshot_id
certification_id
event_type = CERTIFICATION_REFERENCE
event_type_rank = 90
effective_timestamp
session
source_sequence
source_intent_id
generated_event_slot
intra_rank_sequence
```

The preimage excludes `event_id`, `semantic_sequence`, runtime metadata, operational evidence, component fields, and bundle fields.

Domain:

```text
GV-FS0:CERTIFICATION_REFERENCE_EVENT_ID:V1
```

The event ID is calculated before global `semantic_sequence` assignment.

### 5.9 Certified decision result identity

`certified_decision_result_hash` covers authoritative content only:

- fixture and decision bindings;
- book identity;
- canonical event trail;
- ordered snapshots;
- economic payload hash;
- ordered verifier attempts;
- unique retained verifier results;
- certification; and
- certification-reference event.

It excludes its own hash and ID, presentation, and bundle fields.

Identity:

```text
certified_decision_result_id = CDR_<certified_decision_result_hash>
```

### 5.10 Presentation identity

Presentation uses `GV-FS0:PRESENTATION:V1`. It may contain schema-controlled labels, canonical decimal strings, ordered rows, stable status labels, and stable explanatory references. It must not contain locale-derived formatting, wall-clock values, host values, or arbitrary Streamlit state.

Presentation does not affect decision, book, event, snapshot, economic-payload, certification, reference-event, or authoritative component identities.

### 5.11 Bundle identity

The final bundle contains exactly two roles in this order:

```text
1. OPEN
2. NO_POSITION
```

The bundle-hash preimage includes both complete certified decision results, both authoritative component hashes, both presentation projections and hashes, and the role structure. It excludes `bundle_hash` and `bundle_id`.

Definitions:

```text
bundle_hash = full SHA-256 digest
bundle_id = BUNDLE_<bundle_hash>
```

`bundle_id` is an alias derived from `bundle_hash`, not an independently hashed identity.

## 6. DecisionEnvelope and Source Fixture

### 6.1 DecisionEnvelope fields

The V1 decision envelope includes:

```text
schema_version
decision_id
decision_hash
fixture_hash
authority_tier
action
decision_timestamp
effective_timestamp
security_id
requested_quantity_or_sizing_input
rationale_ref
protocol_id
fixture_id
operator_id
supersedes_decision_id
```

Allowed cases:

```text
MANUAL_OWNER_PAPER / OPEN
MANUAL_OWNER_PAPER / NO_POSITION
```

The envelope is immutable after acceptance. A material correction creates a superseding envelope.

`rationale_ref` is an identity-bearing opaque token, not prose, a path, or a URL. It must already be NFC, contain no whitespace or path separators, and match:

```regex
^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$
```

### 6.2 Source fixture constraints

Each synthetic fixture contains:

- one security;
- 5-10 valid sessions;
- initial cash;
- canonical source price records;
- canonical source intent records;
- no provider or network data;
- no benchmark;
- no optimizer;
- no leverage;
- no unsupported corporate action.

OPEN includes one execution intent, one explicit fee intent, one dividend declaration, one dividend payment instruction, and session valuation instructions.

NO_POSITION contains no execution, fee, position movement, entitlement, or payment instruction. It contains explicit valuation instructions preserving all-cash economics.

### 6.3 Source identities

`source_sequence` is the zero-based ordinal in the canonical source-intent array. It is contiguous and contains no gaps or duplicates.

`source_intent_id` is a path-free stable ASCII token matching:

```regex
^[A-Z][A-Z0-9_]*:[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$
```

System-generated authority tokens are:

```text
DECISION:<64-character lowercase decision hash>
CERTIFICATION:<CERT_ plus 64-character lowercase certification digest>
```

A source fixture reference always means `source_intent_id`; it never means a filename, path, URL, or repository location.

## 7. Portfolio Event Types, Ranks, and Generated Slots

### 7.1 Event ranks

The immutable V1 event ranks are:

```text
10  DECISION_ACCEPTED
20  EXECUTION
30  FEE_OR_COST
40  CASH_MOVEMENT
50  POSITION_MOVEMENT
60  DIVIDEND_ENTITLEMENT
70  DIVIDEND_PAYMENT
80  SESSION_VALUATION
90  CERTIFICATION_REFERENCE
```

Unsupported event types or ranks block.

### 7.2 Generated-event slots

The immutable V1 slot table is:

```text
DECISION_ENVELOPE
    DECISION_ACCEPTED          slot 10

EXECUTION_INTENT
    EXECUTION                  slot 10
    CASH_MOVEMENT              slot 20
    POSITION_MOVEMENT          slot 30

EXPLICIT_FEE
    FEE_OR_COST                slot 10
    CASH_MOVEMENT              slot 20

DIVIDEND_DECLARATION
    DIVIDEND_ENTITLEMENT       slot 10

DIVIDEND_PAYMENT_INSTRUCTION
    DIVIDEND_PAYMENT           slot 10

VALUATION_INSTRUCTION
    SESSION_VALUATION          slot 10

CERTIFICATION
    CERTIFICATION_REFERENCE    slot 10
```

An execution intent does not embed a fee. Unused slots are not reused or renumbered. Adding, removing, or renumbering a slot requires a new protocol version.

## 8. Event Ordering, Identity, Duplicates, and Transition Ownership

### 8.1 Intra-rank derivation

Generated event candidates are grouped by:

```text
(
  effective_timestamp_utc,
  session,
  event_type_rank
)
```

Within a group, sort by:

```text
origin_order_key = (
  source_sequence,
  source_intent_id,
  generated_event_slot
)
```

Comparison uses ascending integer order, ascending ASCII bytes for `source_intent_id`, and ascending integer slot order. Duplicate origin-order keys within a group are invalid.

After sorting, assign:

```text
intra_rank_sequence = zero-based index within the group
```

It begins at zero and is contiguous.

### 8.2 Event identity preimage

The provenance-sensitive event identity preimage includes:

```text
schema_version
book_id
decision_id
source_sequence
source_intent_id
generated_event_slot
event_type
effective_timestamp
session
event_type_rank
intra_rank_sequence
complete type-specific semantic payload
```

It excludes:

```text
event_id
semantic_sequence
runtime metadata
downstream identities
```

### 8.3 Canonical global order

After event IDs exist and exact duplicates are collapsed, canonical global order is:

```text
(
  effective_timestamp_utc,
  session,
  event_type_rank,
  intra_rank_sequence,
  event_id
)
```

After sorting, assign:

```text
semantic_sequence = zero-based global ordinal
```

`semantic_sequence` attests the completed order and never participates in event-ID generation.

Contradictory timestamp/session combinations block rather than being silently reordered.

### 8.4 Identity preimage and economic-effect key

The identity preimage includes provenance such as `source_intent_id` and generates `event_id`.

A separate economic-effect key excludes provenance-only fields and contains the normalized operation, including where applicable:

```text
book_id
event_type
effective_timestamp
session
security_id
quantity
execution_price
fee
cash_delta
position_delta
dividend_amount_per_share
entitled_quantity
receivable_amount
payment_amount
referenced_entitlement_id
valuation_price
```

### 8.5 Duplicate rules

```text
same event_id + byte-identical identity preimage
    -> idempotent duplicate; collapse to one event

same event_id + different identity preimage
    -> CONFLICTING_EVENT_ID; block

different event_id + identical economic-effect key
    -> DUPLICATE_SEMANTIC_EVENT; block
```

Exact duplicates are collapsed before canonical ordering, `semantic_sequence`, snapshots, and economic-payload hashing. The retained trail contains one canonical event for one accepted idempotent operation.

### 8.6 Transition ownership

Every economic quantity change has one and only one owning event.

| Event type | Cash | Shares | Receivables | Other responsibility |
|---|---:|---:|---:|---|
| `DECISION_ACCEPTED` | no | no | no | audit only |
| `EXECUTION` | no | no | no | execution authority only |
| `FEE_OR_COST` | no | no | no | fee authority only |
| `CASH_MOVEMENT` | yes | no | no | applies declared cash delta once |
| `POSITION_MOVEMENT` | no | yes | no | applies declared share delta once |
| `DIVIDEND_ENTITLEMENT` | no | no | increase | creates receivable once |
| `DIVIDEND_PAYMENT` | increase | no | decrease | atomically settles one entitlement |
| `SESSION_VALUATION` | no | no | no | records valuation only |
| `CERTIFICATION_REFERENCE` | no | no | no | audit reference only |

Rules:

- `EXECUTION` does not mutate balances directly.
- The execution-generated `CASH_MOVEMENT` applies execution cash delta once.
- The execution-generated `POSITION_MOVEMENT` applies share delta once.
- `FEE_OR_COST` does not mutate balances directly.
- Its generated `CASH_MOVEMENT` applies the fee cash delta once.
- `DIVIDEND_ENTITLEMENT` increases receivables once.
- `DIVIDEND_PAYMENT` decreases the referenced receivable and increases cash by the same amount in one atomic reducer transition.
- A dividend payment emits no separate payment-related `CASH_MOVEMENT` in V1.
- `SESSION_VALUATION` observes post-transition balances and changes no cash, shares, or receivables.

Changing transition ownership is a protocol-version change.

### 8.7 Dividend ordering

For the bounded OPEN fixture:

1. execution and position movement establish eligible shares;
2. entitlement is calculated from shares effective immediately before entitlement;
3. entitlement precedes payment;
4. one payment references exactly one entitlement event;
5. payment occurs at most once;
6. payment atomically reduces receivables and increases cash by the same amount;
7. payment rank 70 precedes valuation rank 80 on the payment session; and
8. terminal certification blocks if an entitlement remains unpaid.

### 8.8 Event construction order

The normative construction order is:

```text
validate decision and source intents
-> validate source_sequence and source_intent_id
-> assign fixed generated_event_slot values
-> expand source intents into event candidates
-> group by timestamp, session, and event rank
-> sort each group by origin_order_key
-> assign intra_rank_sequence
-> construct identity preimages
-> calculate full event IDs
-> validate supplied event IDs where applicable
-> collapse exact idempotent duplicates
-> calculate economic-effect keys
-> reject duplicate semantic events
-> perform canonical global sort
-> assign global semantic_sequence
-> validate persisted semantic_sequence
-> apply reducer transitions
```

No event ID may be calculated before `intra_rank_sequence` exists.

## 9. PortfolioBook and Snapshot Economics

### 9.1 Book invariants

The one-decision book is append-only and enforces:

```text
cash >= 0
shares >= 0
implicit_leverage = false
unsupported_event_count = 0
out_of_order_event_count = 0
paid_dividend_count_per_entitlement = 1
NAV = cash + market_value + receivables
```

Missing, stale, duplicate, non-positive, mismatched, or unordered required prices block. No missing value becomes a zero return or zero price.

### 9.2 Economic formulas

```text
execution_cash_delta
    = -(shares * execution_price)

fee_cash_delta
    = -explicit_fee

dividend_receivable
    = entitled_shares * amount_per_share

market_value
    = shares * session_close

NAV
    = cash + market_value + receivables

session_contribution
    = current_NAV - previous_NAV

cumulative_contribution
    = current_NAV - initial_cash
```

For the first valuation session:

```text
previous_NAV = initial_cash
```

There is no synthetic zero-NAV predecessor.

### 9.3 Snapshot boundary

A snapshot is immutable and read-only. It contains schema-defined economic state and lineage, including:

```text
snapshot_id
session
valuation_timestamp
book_id
decision_id
fixture_hash
authority_tier
action
rationale_ref
security_id
shares
cash
receivables
market_value
nav
session_contribution
cumulative_contribution
applied_event_ids
```

A snapshot cannot mutate the book or certify itself. Certification references are not part of economic snapshots.

## 10. Verifier Input Projection

The verifier consumes a deterministic projection of original fixture and decision inputs. It does not consume primary events, ledgers, snapshots, certifications, components, or bundle data.

### 10.1 Protocol projection

```text
protocol_id              retain
fixture_id               retain
fixture_hash             retain
currency                 retain validated uppercase code
initial_cash             canonical decimal string
source prices            canonical projected source prices
source economic intents  canonical projected source intents
```

### 10.2 Decision projection

| DecisionEnvelope field | Verifier field | Treatment |
|---|---|---|
| `decision_id` | `decision.decision_id` | retained |
| `decision_hash` | `decision.decision_hash` | retained as opaque lineage binding |
| `authority_tier` | `decision.authority` | renamed, value unchanged |
| `action` | `decision.action` | retained |
| `decision_timestamp` | `decision.decision_timestamp` | canonical UTC |
| `effective_timestamp` | `decision.effective_timestamp` | canonical UTC |
| `security_id` | `decision.security_id` | retained |
| `requested_quantity_or_sizing_input` | `decision.requested_sizing` | exact schema projection |
| `rationale_ref` | `decision.rationale_reference` | renamed, value unchanged |
| `protocol_id` | omitted from decision object | retained in protocol object |
| `fixture_id` | omitted from decision object | retained in protocol object |
| `operator_id` | omitted | primary governance validation only |
| `supersedes_decision_id` | omitted | primary lineage validation only |

The verifier validates and preserves `decision_hash` but does not claim to recompute it because intentionally omitted governance fields are not available.

### 10.3 Price projection

Each source price contains exactly:

```text
security_id
session
price_timestamp
close_price
source_sequence
```

No primary valuation or return value is included.

### 10.4 Economic-intent projection

Allowed source intent types are:

```text
EXECUTION_INTENT
EXPLICIT_FEE
DIVIDEND_DECLARATION
DIVIDEND_PAYMENT_INSTRUCTION
VALUATION_INSTRUCTION
```

Projected intents include only original source facts such as source intent ID, type, timestamp, session, security, quantity, price, fee, dividend terms, referenced entitlement, and source sequence.

They omit generated event IDs, book ID, generated sequences, primary balance movements, primary NAV, primary contribution, snapshots, certifications, components, and bundle identities.

The complete verifier input is canonicalized under `GV-FS0:VERIFIER_INPUT:V1`. Its controller-computed hash participates in certification identity.

## 11. Verifier Process, Supervision, Attempts, and Results

### 11.1 Production invocation

The verifier is invoked as:

```text
<absolute sys.executable> -I -X utf8 <absolute verifier script> --input <absolute declared input file>
```

The verifier:

- receives one declared verifier-input file;
- imports only Python standard-library modules;
- imports no primary schema, canonicalization, accounting, reducer, certification, publication, or UI module;
- has no expected repository reads;
- writes no repository artifact; and
- emits exactly one canonical JSON document to stdout on schema-valid completion.

GV-FS0 does not claim operating-system filesystem confinement. The closure claim is limited to evidence that tests found no dependence on declared classes of ambient repository and process state.

### 11.2 Platform-specific environment

The controller constructs a minimal platform-specific environment. It does not rely on `PYTHONHASHSEED`, `PYTHONIOENCODING`, or `PYTHONUTF8` under isolated mode.

POSIX allowlist:

```text
HOME
TMPDIR
TZ
LC_ALL
LANG
```

with isolated temporary HOME/TMPDIR and `TZ=UTC`, `LC_ALL=C`, `LANG=C`.

Windows allowlist:

```text
SystemRoot
WINDIR
COMSPEC
PATHEXT
TEMP
TMP
TZ
```

Required operating-system values are copied explicitly. TEMP and TMP point to the isolated temporary directory. PATH may be included only if the selected Python distribution demonstrably requires it, and then must be explicitly minimal.

The executable and script paths are absolute. Correctness cannot depend on inherited Python, virtual-environment, package-manager, coverage, repository, locale, or user configuration.

### 11.3 Exact supervision constants

All deadlines use a monotonic clock.

```text
execution deadline             = 30.000 seconds
shutdown observation interval  = 2.000 seconds

stdout validity limit          = 1,048,576 bytes
stderr validity limit          = 65,536 bytes

stdout observation cap         = 1,048,577 bytes
stderr observation cap         = 65,537 bytes
```

The execution deadline begins immediately after successful process creation. Launch failure is classified without starting the execution deadline.

The controller may continue reading and discarding bytes after an observation cap, but no additional bytes are retained in canonical or diagnostic buffers.

### 11.4 Byte-oriented capture

The controller captures stdout and stderr concurrently as bytes. Byte limits are enforced before decoding. Accepted bytes are decoded using strict UTF-8.

Successful stderr is zero bytes. Successful stdout is exactly one canonical JSON document ending in one LF. BOMs, leading bytes, trailing bytes, extra blank lines, multiple JSON values, invalid UTF-8, or noncanonical output block a result.

Each stream records:

```text
captured prefix bytes
total bytes observed up to the observation cap
overflow observed
EOF observed
```

### 11.5 Hard-boundary predicates

`VERIFIER_TIMEOUT` is observed only when the process remains running at the 30-second execution deadline before any earlier controller termination request.

If output-limit excess caused termination before the deadline, later crossing the execution deadline during shutdown does not add `VERIFIER_TIMEOUT`.

`VERIFIER_OUTPUT_LIMIT_EXCEEDED` is observed when either stream produces its validity limit plus one byte. Which stream overflowed is operational evidence only.

`VERIFIER_PROCESS_FAILED` is observed for nonzero exit, signal, or platform process failure only when the outcome is not solely the expected result of controller termination for timeout or output-limit excess.

`VERIFIER_SUPERVISION_INCOMPLETE` is observed when, 2.000 seconds after the first controller termination request:

- the process has not reached a terminal state;
- either stream reader has not reached EOF; or
- the controller cannot classify required process and stream state.

### 11.6 Simultaneous boundaries

The first hard boundary is selected by monotonic observation time. If timeout and output-limit observations have the same recorded observation time, precedence is:

```text
1. VERIFIER_TIMEOUT
2. VERIFIER_OUTPUT_LIMIT_EXCEEDED
```

Once the first controller termination request is issued, later expiration of a different hard boundary does not replace or add that initiating hard-boundary predicate. Independently observable non-boundary predicates may still be recorded during shutdown.

### 11.7 Stable controller code selection

After bounded shutdown observation, choose the lowest-ranked code present in the complete observed predicate set:

```text
10  VERIFIER_SUPERVISION_INCOMPLETE
20  VERIFIER_TIMEOUT
30  VERIFIER_OUTPUT_LIMIT_EXCEEDED
40  VERIFIER_PROCESS_FAILED
50  VERIFIER_STDERR_NONEMPTY
60  VERIFIER_OUTPUT_INVALID_UTF8
70  VERIFIER_OUTPUT_NOT_CANONICAL
80  VERIFIER_OUTPUT_SCHEMA_INVALID
90  VERIFIER_RESULT_BINDING_INVALID
```

Reader completion order, thread scheduling, pipe scheduling, and platform event delivery cannot affect the selected code.

Decode and parse stages occur only in this order:

```text
enforce byte limits
-> strict UTF-8 decode
-> canonical-document validation
-> JSON parse
-> schema validation
-> binding validation
```

### 11.8 Evidence-based independence

Required evidence includes:

- static AST import inspection;
- standard-library allowlist validation;
- rejection of dynamic import and repository path insertion;
- repository-absent execution with only script and declared input;
- empty-working-directory execution;
- decoy fixture/config/cache files;
- varied temporary home directories and environment values;
- varied dictionary insertion order; and
- separate non-production hash-seed stress tests where useful.

The protocol does not claim that arbitrary undeclared filesystem reads are prevented.

### 11.9 Verifier result schema

Common required fields:

```text
schema_version
protocol_binding
fixture_binding
decision_binding
verifier_input_hash
verifier_status
reconstructed_economic_payload
reconstructed_economic_payload_hash
failure_codes
```

Allowed statuses:

```text
RECONSTRUCTED
REJECTED
```

For `RECONSTRUCTED`:

```text
reconstructed_economic_payload       required non-null object
reconstructed_economic_payload_hash  required non-null 64-character hash
failure_codes                         required empty array
```

For `REJECTED`:

```text
reconstructed_economic_payload       required null
reconstructed_economic_payload_hash  required null
failure_codes                         required non-empty canonical array
```

Verifier rejection codes come from the certification-failure registry and must permit emitter `VERIFIER`.

The verifier-result hash uses `GV-FS0:VERIFIER_RESULT:V1` and includes only deterministic result content. It excludes its own hash, process IDs, temporary paths, host information, timestamps, duration, stdout/stderr diagnostics, interpreter identity, and environment data.

The controller validates the schema, recomputes any reconstructed economic-payload hash, canonicalizes the result, and computes `verifier_result_hash`. A verifier-supplied result hash is never trusted and is schema-invalid under V1.

### 11.10 Exactly two verifier attempts

Every certification contains exactly two ordered entries:

```text
verifier_attempts[0].ordinal = 1
verifier_attempts[1].ordinal = 2
```

Allowed attempt outcomes:

```text
RESULT
INFRASTRUCTURE_FAILURE
```

A RESULT attempt requires:

```text
verifier_result_hash = non-null controller-computed hash
controller_failure_code = null
```

An INFRASTRUCTURE_FAILURE attempt requires:

```text
verifier_result_hash = null
controller_failure_code = stable certification-registry controller code
```

Operational diagnostics and timings remain non-canonical. The complete ordered attempt array participates directly in `certification_id`.

### 11.11 Unique retained verifier results

The certified decision result contains:

```text
verifier_attempts
retained_verifier_results
```

`verifier_attempts` is the authoritative two-entry ordered array.

`retained_verifier_results` is a hash-addressed collection of unique records:

```json
{
  "verifier_result_hash": "<64-character lowercase sha256>",
  "verifier_result": {}
}
```

Rules:

1. entries are sorted by ascending `verifier_result_hash`;
2. a hash appears at most once;
3. each result validates against the verifier-result schema;
4. the controller recomputes each result hash;
5. every RESULT attempt hash resolves to exactly one retained entry;
6. every retained entry is referenced by at least one attempt;
7. two byte-identical executions reference the same retained entry;
8. two differing schema-valid executions produce two retained entries;
9. infrastructure-failure attempts reference no retained result; and
10. attempt order is represented only by `verifier_attempts`, never by collection order.

The complete retained collection participates in `certified_decision_result_hash`.

### 11.12 Attempt comparison semantics

Two identical RECONSTRUCTED results that match primary values, canonical bytes, and hash produce:

```text
independent_reconstruction_passed = TRUE
canonical_hash_reproduced = TRUE
```

Two identical reconstructed results that differ from primary values produce `independent_reconstruction_passed = FALSE`. A conclusive primary/reconstructed byte or hash difference produces `canonical_hash_reproduced = FALSE`.

Two schema-valid reconstructed results that differ from each other produce:

```text
independent_reconstruction_passed = FALSE
canonical_hash_reproduced = FALSE
```

One reconstructed result plus one infrastructure failure produces UNKNOWN for both checks when the valid result matches primary state. A conclusive mismatch in the valid result produces FALSE for the affected check, and FALSE takes precedence over UNKNOWN.

Two infrastructure failures produce UNKNOWN for both checks.

Two byte-identical REJECTED results produce:

```text
independent_reconstruction_passed = FALSE
canonical_hash_reproduced = UNKNOWN
```

unless deterministic rejection evidence conclusively proves a hash mismatch, in which case the hash check is FALSE.

A RECONSTRUCTED/REJECTED disagreement, differing REJECTED results, differing deterministic bindings, or differing ordered verifier failure codes produces `independent_reconstruction_passed = FALSE`. The hash check is FALSE only when non-null payload evidence conclusively differs; otherwise it is UNKNOWN.

## 12. Certification Semantics and Failure Registries

### 12.1 Mandatory checks

The certification contains these ten tri-state checks:

```text
decision_authority_valid
timestamp_causality_valid
price_freshness_valid
cash_conserved
holdings_valid
nav_reconciled
receivables_reconciled
unsupported_events_absent
independent_reconstruction_passed
canonical_hash_reproduced
```

Allowed values:

```text
TRUE
FALSE
UNKNOWN
```

Evaluation rule:

1. conclusive evidence of violation produces FALSE;
2. otherwise inability to complete the check produces UNKNOWN;
3. otherwise completed evidence produces TRUE.

FALSE takes precedence over UNKNOWN when conclusive violation evidence exists.

Certification status is CERTIFIED only when all ten checks are TRUE. Any FALSE or UNKNOWN produces BLOCKED.

### 12.2 Deterministic check mapping

| Check | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| `decision_authority_valid` | envelope and authority rules pass | authority, action, operator, sizing, or lineage violates a rule | authority validation could not execute |
| `timestamp_causality_valid` | all timestamp and ordering constraints pass | timestamp, session, tie, or causal order violates protocol | causality evaluation could not execute |
| `price_freshness_valid` | every required valid price satisfies fixture rules | missing, duplicate, stale, non-positive, mismatched, or unordered price | price validation could not execute |
| `cash_conserved` | recomputed cash reconciles at every step | negative, unexplained, duplicated, or mismatched cash effect | cash reconciliation could not execute |
| `holdings_valid` | share transitions satisfy all rules | negative, fractional, unexplained, duplicated, leveraged, or action-inconsistent holdings | holdings validation could not execute |
| `nav_reconciled` | every NAV equals cash plus market value plus receivables | any primary or reconstructed NAV differs | NAV reconciliation could not execute |
| `receivables_reconciled` | entitlements and payments reconcile exactly | missing, duplicate, incorrect, or unpaid terminal receivable | receivable reconciliation could not execute |
| `unsupported_events_absent` | every source and generated event is supported | any unsupported event, rank, slot, or transition is present | event classification could not execute |
| `independent_reconstruction_passed` | both verifier attempts complete consistently and match primary economics | deterministic verifier rejection, mismatch, or run-to-run difference | required verifier execution did not complete |
| `canonical_hash_reproduced` | independent canonical bytes and hashes match | recomputed canonical bytes or hashes differ | required payload or result was unavailable or could not be canonicalized |

### 12.3 Certification-failure registry

The certification-failure registry contains only codes eligible for:

- verifier REJECTED results;
- controller verifier-attempt infrastructure outcomes; and
- certification failure bindings.

Each entry contains:

```text
code
category
terminal_or_recoverable
applicable_schema_versions
applicable_checks
applicable_outcomes
applicable_emitters
stable_user_message
operator_recovery_reference
```

Allowed emitters:

```text
PRIMARY
VERIFIER
CONTROLLER
```

`applicable_outcomes` may contain FALSE and/or UNKNOWN, never TRUE.

The registry is hashed under:

```text
GV-FS0:CERTIFICATION_FAILURE_REGISTRY:V1
```

Only its version and hash participate in certification identity.

### 12.4 Operational-error registry

The separate operational registry contains publication, recovery, presentation, and runtime-facing codes, including:

```text
PUBLICATION_LOCKED
PUBLICATION_TARGET_CHANGED
PUBLICATION_POST_REPLACE_VERIFICATION_FAILED
PUBLICATION_RECOVERY_RECORD_FAILED
```

Entries contain:

```text
code
category
terminal_or_recoverable
applicable_schema_versions
stable_user_message
operator_recovery_reference
```

The registry is hashed under:

```text
GV-FS0:OPERATIONAL_ERROR_REGISTRY:V1
```

It does not participate in certification, economic, or certified-component identity.

### 12.5 Failure bindings

The authoritative certification field is ordered `failure_bindings`. Each binding contains exactly:

```text
check
outcome
code
```

Canonical order is:

```text
(check_rank, outcome_rank, code)
```

with:

```text
FALSE   outcome_rank = 10
UNKNOWN outcome_rank = 20
```

For each binding:

- the code exists in the certification registry;
- the schema version is applicable;
- the check is applicable;
- the outcome is applicable;
- the registry emitter matches the source; and
- the certification check value equals the binding outcome.

A TRUE check permits no binding. FALSE and UNKNOWN each require at least one compatible binding. Duplicate bindings are prohibited.

A derived flat `failure_codes` list may be displayed but has no independent authority and does not participate separately in certification identity.

### 12.6 Certification-ID preimage

The certification-ID preimage includes:

```text
certification_schema_version
protocol_id
protocol_version
fixture_id
fixture_hash
decision_id
decision_hash
book_id
terminal_snapshot_id
primary_economic_payload_hash
verifier_input_hash
ordered verifier_attempts
all ten tri-state check values
certification_status
certification_failure_registry_version
certification_failure_registry_hash
ordered failure_bindings
```

Changing attempt order, outcome, result hash, controller code, check value, status, binding check/outcome/code, registry version, or registry hash changes certification identity.

The operational registry is excluded.

## 13. Certification-Reference Event

The reference event is created only after `certification_id` exists.

Construction order:

```text
terminal snapshot exists
-> certification exists
-> certification_id is calculated
-> certification source authority is constructed
-> generated_event_slot 10 is assigned
-> intra_rank_sequence is derived within the rank-90 group
-> reference-event identity preimage is constructed
-> event_id is calculated
-> event enters canonical global order
-> semantic_sequence is assigned and validated
```

Its deterministic session and timestamp equal the terminal valuation session and timestamp. It mutates no economic quantity and is excluded from snapshots and `economic_payload_hash`.

A reference-effect key contains:

```text
book_id
decision_id
terminal_snapshot_id
certification_id
effective_timestamp
session
```

Duplicate reference semantics block unless they are the same exact idempotent event.

## 14. Certified Decision Results, Blocked Evidence, and Final Bundle

### 14.1 Certified decision result

A certified result represents exactly one decision and one book. It contains:

- authoritative decision and fixture bindings;
- book identity;
- canonical event trail;
- ordered snapshots;
- economic payload hash;
- exactly two ordered verifier attempts;
- unique hash-addressed retained verifier results;
- certification;
- certification-reference event; and
- a separate presentation projection.

It is valid only when certification status is CERTIFIED.

### 14.2 OPEN-first gate

OPEN may be rendered during its functional gate from an in-memory component or temporary test artifact outside the permanent product path. It must not publish a partial final bundle.

### 14.3 Blocked evidence

A blocked certification and verifier evidence may exist only as:

- in-memory diagnostic state; or
- explicitly non-publishable operational evidence using `gv_fs0_blocked_evidence_v1` outside the permanent certified-bundle path.

Serialized blocked evidence must contain:

```text
publishable = false
certification_status = BLOCKED
```

It is excluded from certified-component and bundle hashes, cannot validate as `gv_fs0_certified_decision_result_v1`, and can never occupy:

```text
data/gv_fs0/gv_fs0_certified_bundle.json
```

### 14.4 Final bundle

The permanent bundle requires both:

```text
open_result
no_position_result
```

Both must:

- use distinct decision IDs;
- use distinct book IDs;
- contain independent certifications;
- share the protocol version and currency;
- bind their own fixture hashes; and
- have status CERTIFIED.

A partial final bundle is schema-invalid.

## 15. Atomic and Concurrency-Safe Publication

Target:

```text
data/gv_fs0/gv_fs0_certified_bundle.json
```

Lock:

```text
data/gv_fs0/.gv_fs0_certified_bundle.lock
```

### 15.1 Observed state and lock

Before candidate construction, record the exact existing target-byte SHA-256 or `ABSENT`. This operational value is not canonical product content.

Acquire the lock using exclusive file creation. Acquisition is non-waiting. An existing lock returns `PUBLICATION_LOCKED`. Locks are never automatically broken or removed based on age.

### 15.2 Compare under lock

After lock acquisition, reread the target.

```text
candidate bytes equal current valid target
    -> idempotent success; no replace

current target hash differs from observed prebuild target hash
    -> PUBLICATION_TARGET_CHANGED; do not overwrite

current target still matches observed state
    -> replacement may continue
```

Differing candidates never use last-writer-wins.

### 15.3 Replacement algorithm

Under the held lock:

1. validate both certified components;
2. validate the complete final bundle;
3. produce canonical candidate bytes;
4. create a unique temporary file in the target directory using exclusive create;
5. write all bytes;
6. flush the language buffer;
7. file-`fsync`;
8. close the temporary file;
9. atomically replace the target on the same filesystem;
10. directory-`fsync` where supported;
11. reread and verify exact target bytes and SHA-256;
12. remove surviving temporary files; and
13. remove the lock only under the normal-release conditions below.

The previous valid target remains unchanged for failures before successful atomic replacement. After successful replacement, the protocol does not claim the previous file can be restored.

### 15.4 Post-replace failure

If post-replace verification fails:

- return `PUBLICATION_POST_REPLACE_VERIFICATION_FAILED`;
- do not claim prior-target preservation;
- do not automatically roll back;
- retain available expected and observed hashes, length, and failed stage as operational evidence;
- convert the lock into a durable recovery-required record; and
- block further automatic publication.

### 15.5 Durable recovery record

The recovery record contains:

```text
record_version = GV-FS0-PUBLICATION-RECOVERY-V1
state = RECOVERY_REQUIRED
target_token = GV_FS0_CERTIFIED_BUNDLE
observed_prebuild_target_hash
candidate_hash
observed_post_replace_target_hash
failure_code
failure_stage
```

While publication remains locked:

1. write sorted-key UTF-8 JSON with exactly one terminal LF to a temporary lock-directory file;
2. flush;
3. file-`fsync`;
4. close;
5. atomically replace the lock file;
6. directory-`fsync` where supported; and
7. retain the recovery record until explicit operator recovery.

If durable recovery-record replacement fails, retain the existing lock, return `PUBLICATION_RECOVERY_RECORD_FAILED`, and require operator inspection.

Only explicit recovery may remove a recovery-required lock. PID age alone is insufficient because of PID reuse.

### 15.6 Normal lock release

Automatic lock removal is allowed only when:

- no replace occurred and the target remains verified unchanged;
- replacement completed and post-replace verification succeeded; or
- candidate bytes were identical to the already valid target.

## 16. Streamlit Presentation Boundary

The adapter consumes only validated presentation, snapshot, and certification artifacts. It may render:

- authority;
- action;
- rationale reference;
- shares;
- cash;
- receivables;
- NAV;
- contribution;
- canonical hashes;
- certification status; and
- stable failure messages.

It must not:

- import `PortfolioBook` or reducer functions;
- mutate the book;
- calculate NAV or contribution;
- construct dividend entitlements;
- decide freshness;
- execute the verifier;
- aggregate certification;
- infer certification from partial fields; or
- upgrade BLOCKED or unavailable state to CERTIFIED.

Existing replay content remains explicitly non-certifying.

## 17. Data Authority

### 17.1 DataAccessAuthorization

A detached authorization is required before any real provider read, including a local licensed source. It binds exact provider, datasets, licence owner, permitted use, coverage, restrictions, accountable authorizer, repository/artifact identity, authorized actions, issue/expiry, and revocation state.

It contains no credentials or secret material. Payload fields cannot self-authorize. Authorization to probe does not imply authorization to acquire or retain; authorization to acquire does not imply candidate admission.

### 17.2 DataAdmissionCertificate

A detached admission certificate may be created only after acquired bytes pass exact hashes, schema and semantic checks, completeness, contradiction, availability lineage, validity lineage, correction lineage, purpose, and rejected-use checks.

Permission evidence alone cannot produce admission.

### 17.3 Gate matrix

```text
synthetic_fixture:
  DataAccessAuthorization = not required
  DataAdmissionCertificate = not required

real_provider_read:
  DataAccessAuthorization = required
  DataAdmissionCertificate = not possible before read

real_candidate_admission:
  DataAccessAuthorization = required
  DataAdmissionCertificate = required
  owner_freeze_full_admission_gate = required
```

The owner-freeze admission thresholds remain unchanged.

## 18. V1 Immutability and Freeze Evidence

After final protocol approval, these V1 surfaces are byte- and semantics-immutable under their V1 identifiers:

- canonical JSON rules;
- string, Unicode, integer, decimal, date, and timestamp rules;
- hash framing and domain prefixes;
- JSON Schemas;
- event ranks;
- generated-event slots;
- transition ownership;
- ordering and duplicate algorithms;
- identity preimages;
- verifier projection and result rules;
- verifier supervision constants and predicate semantics;
- two-attempt and retained-result rules;
- certification tri-state mappings;
- both registries;
- publication conflict and recovery rules; and
- canonical golden vectors.

Any semantic change requires:

1. a new schema or protocol version;
2. a new machine-readable identifier;
3. a new hash-domain version where hash semantics change;
4. new golden vectors;
5. explicit migration or compatibility treatment;
6. a decision-log entry; and
7. re-audit before implementation or publication.

Editorial corrections may retain V1 only when they change no normative meaning, machine-readable artifact, accepted or rejected value, canonical byte, hash, identity, certification outcome, or publication behavior.

Freeze evidence must record exact repository hashes for:

- this normative contract;
- every V1 schema;
- the certification-failure registry;
- the operational-error registry;
- event ranks;
- generated-event slots;
- transition ownership;
- canonical vectors.

CI must fail on unreviewed same-version changes.

## 19. Required Protocol and Golden Tests

The protocol proof suite must cover at minimum:

### Canonical bytes

- exact hash framing with one terminal LF and no double LF;
- exact string escaping, slash, U+2028/U+2029, CJK, NFC text, emoji, and non-BMP text;
- raw surrogate and noncharacter rejection before normalization;
- normalized-result validation;
- exact integer tokens, range limits, and rejection of signs, leading zeros, decimals, and exponents;
- decimal trailing-zero canonicalization and excess-precision rejection;
- exact timestamps and UTC normalization;
- complete golden preimages and hashes;
- equality among primary, verifier, and CI reference encoders.

### Identity and ordering

- acyclic self-field exclusions;
- deterministic source sequence and generated slots;
- deterministic `intra_rank_sequence`;
- event ID only after intra-rank assignment;
- `semantic_sequence` only after global sort;
- exact duplicate collapse before ordering;
- conflicting event-ID rejection;
- provenance-distinct duplicate economic-effect rejection;
- certification-reference ID includes certification ID and excludes semantic sequence.

### Transition ownership

- execution changes no balance directly;
- execution cash and position movements apply once;
- fee changes no balance directly;
- fee cash movement applies once;
- entitlement increases receivables once;
- payment decreases receivables and increases cash exactly once;
- payment emits no separate cash movement;
- payment precedes valuation;
- no effect is unowned or multiply owned.

### Verifier projection and results

- exact full-envelope projection bytes and hash;
- retained, renamed, omitted, and transformed fields;
- repository-absent and ambient-state independence evidence;
- exact `-I -X utf8` invocation;
- byte limits before decoding;
- exact supervision constants;
- deterministic simultaneous-boundary behavior;
- reader scheduling cannot change controller code;
- exactly two attempts and ordinals 1 then 2;
- identical attempts reference one retained result;
- differing valid attempts reference two retained results;
- duplicate retained hash, missing reference, unreferenced result, and forged hash rejection;
- RECONSTRUCTED and REJECTED conditional nullability;
- controller recomputation of payload and result hashes.

### Certification and registries

- deterministic TRUE/FALSE/UNKNOWN mapping;
- FALSE precedence over UNKNOWN;
- complete ordered attempts affect certification identity;
- complete failure bindings affect certification identity;
- certification registry hash affects certification identity;
- operational registry changes do not affect certification identity;
- incompatible check/outcome/code/emitter combinations block;
- TRUE with a binding blocks;
- FALSE or UNKNOWN without a binding blocks.

### Publication and product boundary

- all pre-replace failures preserve prior target;
- post-replace failure makes no preservation claim;
- recovery lock is durable and not auto-deleted;
- identical concurrent candidates are idempotent;
- differing concurrent candidates cannot overwrite each other;
- blocked evidence cannot validate as a certified result or occupy the permanent path;
- a partial final bundle is invalid;
- UI owns no economic or certification logic.

## 20. Protocol Freeze and GV-FS0 Exit Gates

### 20.1 Protocol freeze gate

P0-P4 is frozen only when:

1. this document contains no superseded protocol language or malformed patch markers;
2. all machine-readable V1 artifacts are generated;
3. all canonical and adversarial protocol tests pass;
4. frozen artifact hashes are recorded;
5. CI protects same-version immutability; and
6. a clean audit approves the protocol-freeze commit.

Only then is reducer implementation authorized.

### 20.2 GV-FS0 product exit gate

GV-FS0 closes only when:

1. OPEN traverses the complete chain through visible certified output;
2. NO_POSITION traverses the same implementation path;
3. all book invariants pass;
4. dividend entitlement and payment are exact;
5. both verifier attempts and retained results satisfy this protocol;
6. all ten certification checks are TRUE for both decisions;
7. primary and verifier values, canonical bytes, and hashes match;
8. two local builds are identical;
9. Windows and Linux canonical bytes and hashes are identical;
10. the permanent bundle contains exactly the two certified components;
11. atomic and concurrent publication tests pass;
12. the default portfolio page renders without owning truth;
13. focused legacy regressions remain green and non-certifying;
14. the complete repository test suite passes; and
15. terminal review and SAW pass with no unresolved in-scope Critical or High finding.

## 21. Current Next Action

Generate the machine-readable V1 schemas, both registries, event-rank table, generated-event-slot table, transition-ownership table, and canonical vectors from this consolidated contract. Implement and pass only the protocol/golden test boundary, record exact freeze hashes, and submit the protocol-freeze commit for clean audit.

Do not begin economic reduction, fixture certification, bundle publication, or Streamlit integration before that audit passes.
