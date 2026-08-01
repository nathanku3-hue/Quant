# P1 Custody and Handoff Decision

Date: 2026-08-01
Decision: `SELECT_PROVISIONAL_OWNER_CONTROLLED_PROPRIETARY_MODEL`
Status: `OPERATIONAL_BOUNDARY_SELECTED; LEGAL_CLEARANCE_OPEN; LIVE_CLOSED`
Jurisdiction assumed for this record: Australia, with Western Australia as the operator location unless later corrected

## Decision boundary

This is an operational custody and handoff decision for future design work. It does not provide legal advice, determine that an Australian financial services licence is or is not required, approve a broker, or authorize real-capital activity.

The current Corporations Act states that a person is generally taken not to deal in a financial product when dealing on their own behalf, subject to qualifications. It separately requires a person carrying on a financial services business to hold an Australian financial services licence unless an exemption or representative arrangement applies. ASIC advises that advice, dealing, market making, and custodial services can be financial services and directs operators to assess their exact activities and seek professional advice where uncertain.

Primary references checked on 2026-08-01:

- Corporations Act 2001, section 766C, current compilation available from the Federal Register of Legislation: https://www.legislation.gov.au/C2004A00818/latest/text
- Corporations Act 2001, section 911A, current compilation available from the Federal Register of Legislation: https://www.legislation.gov.au/C2004A00818/latest/text
- ASIC, AFS licensees: https://www.asic.gov.au/for-finance-professionals/afs-licensees/
- ASIC Regulatory Guide 36, Licensing: Financial product advice and dealing: https://www.asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-36-licensing-financial-product-advice-and-dealing/

## Credible options

### Option A — Owner-controlled proprietary account; human order submission

One legal and beneficial owner uses one account held with a regulated broker/custodian. Terminal Zero produces paper decisions, certified records, proposed order instructions, and reconciliation evidence. The human owner/approver reviews and enters or submits every real order. Terminal Zero holds no client assets, broker credentials, signing keys, or autonomous order authority.

- Custody clarity: highest among current options.
- Reversibility: high; software can be stopped without impairing broker custody.
- Legal complexity: lowest relative option, but still requires qualified review of the exact entity, business, communications, and broker arrangement.
- Product impact: preserves current paper-first architecture and separates decision evidence from execution authority.

### Option B — Owner-controlled proprietary account; supervised API submission

The same beneficial owner and broker custody apply, but a bounded software service holds restricted brokerage credentials and submits orders after human approval.

- Custody clarity: moderate.
- Reversibility: moderate; credential revocation and broker-side kill controls are required.
- Legal/operational complexity: higher because automated submission, credential custody, incident response, access logging, and broker API terms become authoritative.
- Product impact: requires a new execution and secrets boundary.

### Option C — Advisory, discretionary, pooled, or client-capital operation

The system provides advice to another person, arranges or submits orders for another person, manages another person's account, or combines capital from multiple beneficial owners.

- Custody clarity: low without a formal licensed structure.
- Reversibility: lower because client obligations and records attach.
- Legal/operational complexity: highest.
- Product impact: changes the legal exposure, user model, custody model, disclosures, controls, and liability boundary.

## Discriminator

Select the option that keeps beneficial ownership, account ownership, cash and security custody, order approval, order submission, and economic liability with one owner while allowing Terminal Zero to remain a paper decision and certified-record system.

Option A best satisfies that discriminator and is selected provisionally.

## Selected model

```text
legal owner = beneficial account owner
broker/custodian = holds cash, securities, account ledger, and executed-order authority
operator = owner or named internal operator acting only for that owner
approver = beneficial owner
Terminal Zero = paper decision, proposed order, certification, replay, and audit records
real order = entered/submitted by the human approver through the broker
certified reconciliation = broker confirmation imported or manually recorded after execution
```

## Who

- Legal custodian: the selected regulated broker/custodian under its account agreement.
- Account owner and beneficial owner: one identified person or entity; these identities must be recorded and must not silently diverge.
- Operator: the owner or a formally designated internal operator acting solely for that owner.
- Approver: the beneficial owner; no delegated autonomous approval.
- Auditor: the owner and any separately appointed professional adviser with read-only access to certified records.

## What

- Cash and securities: remain exclusively with the broker/custodian.
- Orders: Terminal Zero may create proposed paper instructions only; a human submits real orders.
- Credentials: no brokerage password, API token, signing key, or multi-factor secret is stored by Terminal Zero.
- Certified records: Terminal Zero may retain immutable decisions, evidence hashes, proposed orders, human approval records, broker confirmations, reconciliations, corrections, and incident records.
- Corrections: append-only in Terminal Zero; economic corrections at the broker require a new supervised transaction and reconciliation.

## When

- Authority begins only after qualified legal advice confirms the exact arrangement and the broker accepts the intended use.
- Human approval is required for every real order immediately before submission.
- Revocation is immediate when the owner withdraws authority, credentials or account access change, a control fails, or an incident is declared.
- Reconciliation occurs after each execution and at least once per trading day with activity.
- Unresolved reconciliation differences trigger the emergency stop before another order.

## Where

- Operator location: Australia, currently assumed Western Australia.
- Broker/custodian venue and governing law: must be recorded before any pilot.
- Cash, securities, and authoritative broker records remain in the broker's systems.
- Terminal Zero records remain in the owner's controlled repository/storage and are not a substitute for broker statements.
- Any overseas broker, market, cloud record location, or cross-border operator introduces a new jurisdictional review.

## How

```text
certified paper decision
→ proposed order packet with limits and rationale
→ human owner review
→ human submission through broker
→ broker acknowledgement
→ execution or cancellation
→ broker confirmation
→ Terminal Zero reconciliation
→ append-only certification or incident stop
```

Approval limits:

- long-only listed liquid securities;
- no leverage, margin, derivatives, shorting, borrowing, lending, or pooled capital;
- one beneficial owner;
- explicit maximum position, order, daily turnover, and loss limits fixed before pilot design;
- no order proceeds while a prior execution is unreconciled.

Rollback and emergency stop:

- cancel unfilled orders through the broker;
- revoke operator access;
- disable any import or order-packet generation path;
- reconcile all open orders, cash, positions, and fees;
- reduce or close positions only through a separately approved supervised plan;
- preserve all decision, approval, broker, and incident records.

## Exposure classification

Selected intended exposure: proprietary activity for one beneficial owner only.

The classification changes immediately if the system or operator:

- provides recommendations or opinions intended to influence another person's financial-product decisions;
- arranges, enters, or manages orders for another person;
- holds or controls another person's cash, securities, credentials, or beneficial interest;
- accepts pooled or subscribed funds;
- operates a managed, advisory, discretionary, signal, subscription, or public recommendation service;
- makes a market or regularly quotes executable prices.

## Unresolved legal questions

Qualified Australian legal advice must resolve at least:

1. the exact legal person operating Terminal Zero and owning the brokerage account;
2. whether the actual activities, communications, repetition, remuneration, or business structure amount to carrying on a financial services business;
3. the application and limits of the own-account treatment in section 766C(3) to the exact facts;
4. whether any research distribution, signal publication, proposed-order sharing, or software access constitutes financial product advice, arranging, dealing, or another regulated service;
5. market-integrity, insider-trading, conflicts, record-retention, privacy, cybersecurity, tax, and reporting duties;
6. broker terms governing manual order support, data import, automated tooling, record access, and account delegation;
7. any cross-border consequences from broker, exchange, cloud, data, operator, or beneficial-owner location.

## Stop rules

Limited Live and all real-order implementation stop if any of the following is true:

- legal owner, beneficial owner, operator, approver, or custodian is undefined;
- qualified legal review is absent or does not cover the exact intended facts;
- another person's assets, account, credentials, or decisions enter scope;
- the operator publishes or supplies recommendations intended to influence others;
- the system stores broker credentials or can submit orders;
- broker/custodian venue, governing law, account terms, or record location is unknown;
- reconciliation, revocation, emergency stop, or audit access is unproven;
- leverage, shorting, derivatives, margin, borrowing, pooled capital, or unsupervised operation is proposed.

## Handoff result

This record removes ambiguity about the intended custody direction but does not remove the legal blocker. It does not raise the accepted score and does not open P2 or Limited Live.
