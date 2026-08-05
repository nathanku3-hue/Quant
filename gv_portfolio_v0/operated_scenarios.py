"""Declarative scenarios for the single scalable operated-portfolio engine."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash

DEFAULT_SCENARIO_ID = "GV_OPERATED_PORTFOLIO_10_TRANSITION_1R"
PORTFOLIO_25_SCENARIO_ID = "GV_OPERATED_PORTFOLIO_25_1"
ENGINE_SCALE_50_SCENARIO_ID = "GV_ENGINE_SCALE_CHARACTERIZATION_50"
ENGINE_SCALE_100_SCENARIO_ID = "GV_ENGINE_SCALE_CHARACTERIZATION_100"
PROSPECTIVE_25_SCENARIO_ID = "GV_PROSPECTIVE_PAPER_BASELINE_1"
REAL_MU_PROSPECTIVE_SCENARIO_ID = "GV_REAL_EVIDENCE_MU_PORTFOLIO_1"
OPERATED_PAPER_CAPITAL_SCENARIO_ID = "GV_OPERATED_PAPER_CAPITAL_1"


def _instrument(
    permanent_key: str,
    symbol: str,
    name: str,
    cluster: str,
    *,
    evidence_content: str,
    evidence_slug: str,
    outcome: str,
    score: int,
    thesis: str,
    target_quantity: str,
    reference_price: str,
) -> dict[str, Any]:
    return {
        "permanent_key": permanent_key,
        "symbol": symbol,
        "name": name,
        "economic_cluster": cluster,
        "evidence_content": evidence_content,
        "evidence_slug": evidence_slug,
        "outcome": outcome,
        "net_score_bps": score,
        "principal_claim": thesis,
        "target_quantity": target_quantity,
        "reference_price": reference_price,
        "hard_falsifiers": [f"{symbol.lower()}_hard_falsifier"],
        "watch_conditions": [f"{symbol.lower()}_watch_condition"],
    }


SCENARIO_10: dict[str, Any] = {
    "scenario_id": DEFAULT_SCENARIO_ID,
    "title": "GV Operated Portfolio 10",
    "id_domain": "GV-OPERATED-PORTFOLIO-10",
    "schema_version": "gv_operated_portfolio_v3",
    "claim_boundary": (
        "Deterministic operated paper portfolio only; no alpha or live-capital claim."
    ),
    "fixture_namespace": "operated-10",
    "minimum_funded_positions": 3,
    "minimum_total_cash_bps": 1000,
    "cash_openings": [
        {"bucket": "AVAILABLE", "amount": "4500"},
        {"bucket": "RESEARCH_RESERVE", "amount": "500"},
    ],
    "portfolio_aim": {
        "objective": "Operate one diversified paper portfolio with explicit residual liquidity.",
        "allowed_actions": ["BUY", "SELL", "REDUCE", "HOLD", "CASH"],
        "effective_at": "2026-07-22T09:00:00.000000Z",
    },
    "timeline": {
        "cash_opened_at": "2026-07-22T08:55:00.000000Z",
        "initial_decision_at": "2026-07-22T09:05:00.000000Z",
        "aim_confirmed_at": "2026-07-22T09:05:30.000000Z",
        "initial_transition_at": "2026-07-22T09:06:00.000000Z",
        "initial_order_start_minute": 7,
        "initial_certified_at": "2026-07-22T09:12:00.000000Z",
        "no_change_certified_at": "2026-08-05T12:01:00.000000Z",
        "transition_decision_at": "2026-08-20T12:01:00.000000Z",
        "transition_planned_at": "2026-08-20T12:02:00.000000Z",
        "transition_order_start_minute": 3,
        "transition_certified_at": "2026-08-20T12:05:00.000000Z",
        "correction_at": "2026-08-20T12:06:00.000000Z",
        "correction_recorded_at": "2026-08-20T12:07:00.000000Z",
    },
    "status_explanations": {
        "DRAFT_REVIEW": "Ten distinct instruments and one portfolio aim await operator confirmation.",
        "FUNDED_CERTIFIED": "The operator confirmed one portfolio; four positions were funded and residual cash remained classified.",
        "OBSERVED_NO_CHANGE_CERTIFIED": "A later observation was admitted but did not cross a transition threshold, so holdings and cash were preserved.",
        "TRANSITION_CERTIFIED": "A later observation weakened Harbor and strengthened Meridian; Harbor was reduced and Meridian was funded.",
        "CORRECTED_CERTIFIED": "A non-economic annotation was corrected append-only; portfolio economics and prior certifications remained stable.",
    },
    "initial_decision_reason": "INITIAL_CAPITAL_COMPETITION",
    "initial_changed_why_reason": (
        "The four highest-scoring eligible instruments received capital; residual cash remained explicit."
    ),
    "no_change": {
        "instrument_symbol": "NSTAR",
        "content": "Northstar renewal movement remained inside the declared watch band; no score crossed a funding threshold.",
        "locator": "fixture://operated-10/nstar/no-change-v1",
        "observed_at": "2026-08-05T12:00:00.000000Z",
        "reason": "The observation stayed inside the watch band; no hard falsifier or funding threshold fired.",
    },
    "transition": {
        "content": "Harbor backlog quality weakened below its funding band while Meridian qualification converted into a firm order.",
        "locator": "fixture://operated-10/harbor-meridian/transition-v1",
        "observed_at": "2026-08-20T12:00:00.000000Z",
        "decision_reason": "AUTHORIZED_HARBOR_TO_MERIDIAN_TRANSITION",
        "transition_kind": "REDUCE_AND_FUND",
        "reason": "Harbor fell below its prior funding band while Meridian moved above the incremental-capital threshold.",
        "primary_reduced_symbol": "HARBOR",
        "primary_funded_symbol": "MERID",
        "review_updates": {
            "HARBOR": {
                "net_score_bps": 260,
                "target_quantity": "6",
                "principal_claim": "Backlog quality weakened; retain only a reduced monitoring position.",
            },
            "MERID": {
                "net_score_bps": 590,
                "target_quantity": "5",
                "principal_claim": "A firm qualification order now supports bounded funding.",
            },
        },
    },
    "correction": {
        "reason": "Clarify that Meridian evidence is a firm qualification order, not a shipment.",
        "source_identity": "OPERATED10:CORRECTION:MERIDIAN-ANNOTATION",
    },
    "instruments": [
        _instrument("ISSUER:NORTHSTAR:COMMON", "NSTAR", "Northstar Systems", "DIGITAL_INFRASTRUCTURE", evidence_content="Recurring platform renewals remain above the principal-thesis floor.", evidence_slug="renewals", outcome="ADMIT", score=620, thesis="Renewal durability supports a funded principal position.", target_quantity="20", reference_price="25"),
        _instrument("ISSUER:HARBOR:COMMON", "HARBOR", "Harbor Automation", "DIGITAL_INFRASTRUCTURE", evidence_content="Automation backlog supports near-term cash conversion but concentration risk remains.", evidence_slug="backlog", outcome="ADMIT", score=560, thesis="Backlog quality supports a bounded funded position.", target_quantity="10", reference_price="40"),
        _instrument("ISSUER:ORBIT:COMMON", "ORBIT", "Orbit Networks", "DIGITAL_INFRASTRUCTURE", evidence_content="Network bookings improved, but customer concentration evidence is incomplete.", evidence_slug="bookings", outcome="ABSTAIN", score=300, thesis="Concentration evidence is insufficient for commitment.", target_quantity="0", reference_price="35"),
        _instrument("ISSUER:QUANTA:COMMON", "QUANTA", "Quanta Compute", "DIGITAL_INFRASTRUCTURE", evidence_content="Compute demand is strong while power availability constrains the bull case.", evidence_slug="power", outcome="ABSTAIN", score=250, thesis="Power constraints keep the thesis observable but unfunded.", target_quantity="0", reference_price="60"),
        _instrument("ISSUER:MESH:COMMON", "MESH", "Mesh Security", "DIGITAL_INFRASTRUCTURE", evidence_content="Security growth does not offset a mandate-breaking leverage ratio.", evidence_slug="leverage", outcome="REJECT", score=180, thesis="Leverage violates the mandate screen.", target_quantity="0", reference_price="20"),
        _instrument("ISSUER:ATLAS:COMMON", "ATLAS", "Atlas Logistics", "REAL_ECONOMY", evidence_content="Freight utilization and contract repricing support resilient base economics.", evidence_slug="utilization", outcome="ADMIT", score=540, thesis="Contract repricing supports a funded real-economy position.", target_quantity="15", reference_price="30"),
        _instrument("ISSUER:VITAL:COMMON", "VITAL", "Vital Diagnostics", "REAL_ECONOMY", evidence_content="Diagnostic consumables produce stable recurring demand and low balance-sheet risk.", evidence_slug="consumables", outcome="ADMIT", score=520, thesis="Recurring consumables support a funded defensive position.", target_quantity="12", reference_price="50"),
        _instrument("ISSUER:MERIDIAN:COMMON", "MERID", "Meridian Components", "REAL_ECONOMY", evidence_content="Component qualification is progressing, but the initial order evidence is not yet decisive.", evidence_slug="qualification", outcome="ADMIT", score=470, thesis="Qualification progress makes Meridian eligible but initially unfunded.", target_quantity="0", reference_price="30"),
        _instrument("ISSUER:FOUNDRY:COMMON", "FNDRY", "Foundry Materials", "REAL_ECONOMY", evidence_content="Materials spreads normalized and remain below the capital-entry threshold.", evidence_slug="spreads", outcome="ABSTAIN", score=350, thesis="Normalized spreads remain below entry threshold.", target_quantity="0", reference_price="45"),
        _instrument("ISSUER:AGRI:COMMON", "AGRI", "Agri Inputs", "REAL_ECONOMY", evidence_content="Input-volume recovery is offset by adverse working-capital intensity.", evidence_slug="working-capital", outcome="REJECT", score=220, thesis="Working-capital intensity blocks admission.", target_quantity="0", reference_price="25"),
    ],
}


SCENARIO_25: dict[str, Any] = {
    "scenario_id": PORTFOLIO_25_SCENARIO_ID,
    "title": "GV Operated Portfolio 25",
    "id_domain": "GV-OPERATED-PORTFOLIO-25",
    "schema_version": "gv_operated_portfolio_v3",
    "claim_boundary": (
        "Deterministic operated 25-security paper portfolio only; no alpha or live-capital claim."
    ),
    "fixture_namespace": "operated-25",
    "minimum_funded_positions": 3,
    "minimum_total_cash_bps": 1000,
    "cash_openings": [
        {"bucket": "AVAILABLE", "amount": "10000"},
        {"bucket": "RESEARCH_RESERVE", "amount": "1000"},
    ],
    "portfolio_aim": {
        "objective": "Operate one 25-security paper portfolio with bounded review and explicit residual liquidity.",
        "allowed_actions": ["BUY", "SELL", "REDUCE", "HOLD", "CASH"],
        "effective_at": "2026-09-01T09:00:00.000000Z",
    },
    "timeline": {
        "cash_opened_at": "2026-09-01T08:55:00.000000Z",
        "initial_decision_at": "2026-09-01T09:05:00.000000Z",
        "aim_confirmed_at": "2026-09-01T09:05:30.000000Z",
        "initial_transition_at": "2026-09-01T09:06:00.000000Z",
        "initial_order_start_minute": 7,
        "initial_certified_at": "2026-09-01T09:20:00.000000Z",
        "no_change_certified_at": "2026-09-05T12:01:00.000000Z",
        "transition_decision_at": "2026-09-20T12:01:00.000000Z",
        "transition_planned_at": "2026-09-20T12:02:00.000000Z",
        "transition_order_start_minute": 3,
        "transition_certified_at": "2026-09-20T12:06:00.000000Z",
        "correction_at": "2026-09-20T12:07:00.000000Z",
        "correction_recorded_at": "2026-09-20T12:08:00.000000Z",
    },
    "status_explanations": {
        "DRAFT_REVIEW": "Twenty-five distinct instruments and one portfolio aim await operator confirmation.",
        "FUNDED_CERTIFIED": "The operator confirmed one 25-security portfolio; multiple positions were funded and residual cash remained classified.",
        "OBSERVED_NO_CHANGE_CERTIFIED": "A later observation was admitted without crossing a transition threshold, preserving portfolio economics.",
        "TRANSITION_CERTIFIED": "A later observation changed capital competition; one funded position was reduced and one previously unfunded position received capital.",
        "CORRECTED_CERTIFIED": "A non-economic annotation was corrected append-only; portfolio economics and prior certifications remained stable.",
    },
    "initial_decision_reason": "INITIAL_25_SECURITY_CAPITAL_COMPETITION",
    "initial_changed_why_reason": (
        "The selected eligible instruments received capital through one competition across all 25 identities; residual cash remained explicit."
    ),
    "no_change": {
        "instrument_symbol": "NSTAR",
        "content": "Northstar renewal evidence remained inside the declared watch band; no target quantity changed.",
        "locator": "fixture://operated-25/nstar/no-change-v1",
        "observed_at": "2026-09-05T12:00:00.000000Z",
        "reason": "The admitted observation stayed inside the watch band; no hard falsifier or funding threshold fired.",
    },
    "transition": {
        "content": "Harbor backlog quality weakened below its funding band while Meridian converted qualification into a firm order.",
        "locator": "fixture://operated-25/harbor-meridian/transition-v1",
        "observed_at": "2026-09-20T12:00:00.000000Z",
        "decision_reason": "AUTHORIZED_25_SECURITY_HARBOR_TO_MERIDIAN_TRANSITION",
        "transition_kind": "REDUCE_AND_FUND",
        "reason": "Harbor fell below its prior funding band while Meridian moved above the incremental-capital threshold in the 25-security competition.",
        "primary_reduced_symbol": "HARBOR",
        "primary_funded_symbol": "MERID",
        "review_updates": {
            "HARBOR": {
                "net_score_bps": 260,
                "target_quantity": "6",
                "principal_claim": "Backlog quality weakened; retain only a reduced monitoring position.",
            },
            "MERID": {
                "net_score_bps": 590,
                "target_quantity": "5",
                "principal_claim": "A firm qualification order now supports bounded funding.",
            },
        },
    },
    "correction": {
        "reason": "Clarify that Meridian evidence is a firm qualification order, not a shipment.",
        "source_identity": "OPERATED25:CORRECTION:MERIDIAN-ANNOTATION",
    },
    "instruments": [
        _instrument("ISSUER:NORTHSTAR:COMMON", "NSTAR", "Northstar Systems", "DIGITAL_INFRASTRUCTURE", evidence_content="Recurring platform renewals remain above the principal-thesis floor.", evidence_slug="renewals", outcome="ADMIT", score=620, thesis="Renewal durability supports a funded principal position.", target_quantity="20", reference_price="25"),
        _instrument("ISSUER:HARBOR:COMMON", "HARBOR", "Harbor Automation", "DIGITAL_INFRASTRUCTURE", evidence_content="Automation backlog supports near-term cash conversion but concentration risk remains.", evidence_slug="backlog", outcome="ADMIT", score=560, thesis="Backlog quality supports a bounded funded position.", target_quantity="10", reference_price="40"),
        _instrument("ISSUER:ORBIT:COMMON", "ORBIT", "Orbit Networks", "DIGITAL_INFRASTRUCTURE", evidence_content="Network bookings improved while customer concentration remained unresolved.", evidence_slug="bookings", outcome="ABSTAIN", score=300, thesis="Concentration evidence is insufficient for commitment.", target_quantity="0", reference_price="35"),
        _instrument("ISSUER:QUANTA:COMMON", "QUANTA", "Quanta Compute", "DIGITAL_INFRASTRUCTURE", evidence_content="Compute demand is strong while power availability constrains deployment.", evidence_slug="power", outcome="ABSTAIN", score=250, thesis="Power constraints keep the thesis observable but unfunded.", target_quantity="0", reference_price="60"),
        _instrument("ISSUER:MESH:COMMON", "MESH", "Mesh Security", "DIGITAL_INFRASTRUCTURE", evidence_content="Security growth does not offset a mandate-breaking leverage ratio.", evidence_slug="leverage", outcome="REJECT", score=180, thesis="Leverage violates the mandate screen.", target_quantity="0", reference_price="20"),
        _instrument("ISSUER:ATLAS:COMMON", "ATLAS", "Atlas Logistics", "INDUSTRIAL_SYSTEMS", evidence_content="Freight utilization and contract repricing support resilient base economics.", evidence_slug="utilization", outcome="ADMIT", score=540, thesis="Contract repricing supports a funded industrial position.", target_quantity="15", reference_price="30"),
        _instrument("ISSUER:MERIDIAN:COMMON", "MERID", "Meridian Components", "INDUSTRIAL_SYSTEMS", evidence_content="Component qualification is progressing, but the initial order evidence is not decisive.", evidence_slug="qualification", outcome="ADMIT", score=470, thesis="Qualification progress makes Meridian eligible but initially unfunded.", target_quantity="0", reference_price="30"),
        _instrument("ISSUER:FOUNDRY:COMMON", "FNDRY", "Foundry Materials", "INDUSTRIAL_SYSTEMS", evidence_content="Materials spreads normalized and remain below the capital-entry threshold.", evidence_slug="spreads", outcome="ABSTAIN", score=350, thesis="Normalized spreads remain below entry threshold.", target_quantity="0", reference_price="45"),
        _instrument("ISSUER:VECTOR:COMMON", "VECTOR", "Vector Controls", "INDUSTRIAL_SYSTEMS", evidence_content="Control-system replacement demand is supported by a multi-year service backlog.", evidence_slug="service-backlog", outcome="ADMIT", score=515, thesis="Service backlog supports bounded initial funding.", target_quantity="8", reference_price="45"),
        _instrument("ISSUER:FORGE:COMMON", "FORGE", "Forge Robotics", "INDUSTRIAL_SYSTEMS", evidence_content="Robotics bookings improved but free-cash conversion remains below threshold.", evidence_slug="cash-conversion", outcome="ABSTAIN", score=330, thesis="Cash conversion requires another observation before funding.", target_quantity="0", reference_price="38"),
        _instrument("ISSUER:VITAL:COMMON", "VITAL", "Vital Diagnostics", "HEALTHCARE", evidence_content="Diagnostic consumables produce stable recurring demand and low balance-sheet risk.", evidence_slug="consumables", outcome="ADMIT", score=520, thesis="Recurring consumables support a funded defensive position.", target_quantity="12", reference_price="50"),
        _instrument("ISSUER:GENOM:COMMON", "GENOM", "Genom Analytics", "HEALTHCARE", evidence_content="Sequencing demand is expanding while reimbursement evidence remains incomplete.", evidence_slug="reimbursement", outcome="ABSTAIN", score=365, thesis="Reimbursement uncertainty blocks initial funding.", target_quantity="0", reference_price="55"),
        _instrument("ISSUER:CLINIC:COMMON", "CLINIC", "Clinic Systems", "HEALTHCARE", evidence_content="Hospital workflow renewals remain stable but implementation costs are elevated.", evidence_slug="renewals", outcome="ABSTAIN", score=340, thesis="Implementation costs keep the position on watch.", target_quantity="0", reference_price="42"),
        _instrument("ISSUER:BIOSYN:COMMON", "BIOSYN", "BioSyn Tools", "HEALTHCARE", evidence_content="Research-tool orders recovered but customer concentration remains high.", evidence_slug="orders", outcome="ABSTAIN", score=320, thesis="Order recovery is insufficient without concentration improvement.", target_quantity="0", reference_price="48"),
        _instrument("ISSUER:MEDICA:COMMON", "MEDICA", "Medica Services", "HEALTHCARE", evidence_content="Procedure volumes are stable while leverage exceeds the mandate ceiling.", evidence_slug="leverage", outcome="REJECT", score=190, thesis="Leverage violates the mandate screen.", target_quantity="0", reference_price="36"),
        _instrument("ISSUER:LUMEN:COMMON", "LUMEN", "Lumen Retail", "CONSUMER_NETWORKS", evidence_content="Membership retention and unit economics remain above the funding floor.", evidence_slug="retention", outcome="ADMIT", score=505, thesis="Membership durability supports bounded initial funding.", target_quantity="10", reference_price="28"),
        _instrument("ISSUER:MARKET:COMMON", "MARKET", "Market Hub", "CONSUMER_NETWORKS", evidence_content="Marketplace take rate improved while seller churn remains elevated.", evidence_slug="seller-churn", outcome="ABSTAIN", score=310, thesis="Seller churn prevents initial funding.", target_quantity="0", reference_price="32"),
        _instrument("ISSUER:TRAVEL:COMMON", "TRAVEL", "Travel Grid", "CONSUMER_NETWORKS", evidence_content="Booking growth remains positive but refund volatility exceeds the watch band.", evidence_slug="refunds", outcome="ABSTAIN", score=295, thesis="Refund volatility keeps the security unfunded.", target_quantity="0", reference_price="27"),
        _instrument("ISSUER:HOME:COMMON", "HOME", "Home Direct", "CONSUMER_NETWORKS", evidence_content="Repeat purchase evidence weakened and inventory days increased.", evidence_slug="inventory", outcome="REJECT", score=205, thesis="Inventory intensity blocks admission.", target_quantity="0", reference_price="22"),
        _instrument("ISSUER:FOODCO:COMMON", "FOODCO", "FoodCo Brands", "CONSUMER_NETWORKS", evidence_content="Brand pricing remains resilient but volume evidence is neutral.", evidence_slug="volume", outcome="ABSTAIN", score=355, thesis="Neutral volume evidence does not justify funding.", target_quantity="0", reference_price="31"),
        _instrument("ISSUER:SOLAR:COMMON", "SOLAR", "Solar Array", "ENERGY_RESOURCES", evidence_content="Contracted solar backlog and balance-sheet liquidity support bounded funding.", evidence_slug="contracted-backlog", outcome="ADMIT", score=500, thesis="Contracted backlog supports an initial funded position.", target_quantity="10", reference_price="32"),
        _instrument("ISSUER:GRID:COMMON", "GRID", "Grid Storage", "ENERGY_RESOURCES", evidence_content="Storage deployments and service attach rates remain above threshold.", evidence_slug="deployments", outcome="ADMIT", score=510, thesis="Deployment evidence supports bounded initial funding.", target_quantity="12", reference_price="35"),
        _instrument("ISSUER:DRILL:COMMON", "DRILL", "Drill Services", "ENERGY_RESOURCES", evidence_content="Service pricing improved while cyclicality remains outside the mandate preference.", evidence_slug="pricing", outcome="ABSTAIN", score=285, thesis="Cyclicality keeps the security unfunded.", target_quantity="0", reference_price="29"),
        _instrument("ISSUER:AGRI:COMMON", "AGRI", "Agri Inputs", "ENERGY_RESOURCES", evidence_content="Input-volume recovery is offset by adverse working-capital intensity.", evidence_slug="working-capital", outcome="REJECT", score=220, thesis="Working-capital intensity blocks admission.", target_quantity="0", reference_price="25"),
        _instrument("ISSUER:WATER:COMMON", "WATER", "Water Systems", "ENERGY_RESOURCES", evidence_content="Municipal order coverage is stable but margin evidence remains below threshold.", evidence_slug="margins", outcome="ABSTAIN", score=345, thesis="Margin evidence requires another observation before funding.", target_quantity="0", reference_price="34"),
    ],
}


def _scale_characterization_scenario(size: int) -> dict[str, Any]:
    """Build synthetic load data without changing the operated engine contract."""
    if size not in {50, 100}:
        raise ValueError(f"UNSUPPORTED_SCALE_CHARACTERIZATION:{size}")
    scenario = deepcopy(SCENARIO_25)
    scenario_id = (
        ENGINE_SCALE_50_SCENARIO_ID
        if size == 50
        else ENGINE_SCALE_100_SCENARIO_ID
    )
    multiplier = size // 25
    scenario.update(
        {
            "scenario_id": scenario_id,
            "title": f"GV Engine Scale Characterization {size}",
            "id_domain": f"GV-ENGINE-SCALE-{size}",
            "claim_boundary": (
                f"Synthetic {size}-security engine stress evidence only; not Universe "
                "acceptance, historical membership proof, alpha evidence, or live-capital authority."
            ),
            "fixture_namespace": f"engine-scale-{size}",
            "cash_openings": [
                {"bucket": "AVAILABLE", "amount": str(10000 * multiplier)},
                {"bucket": "RESEARCH_RESERVE", "amount": str(1000 * multiplier)},
            ],
            "initial_decision_reason": (
                f"INITIAL_{size}_SECURITY_ENGINE_CHARACTERIZATION"
            ),
            "initial_changed_why_reason": (
                f"One deterministic competition covered all {size} synthetic identities; "
                "residual cash remained explicit."
            ),
        }
    )
    scenario["portfolio_aim"]["objective"] = (
        f"Characterize the existing operated engine with one synthetic {size}-security "
        "paper portfolio and bounded operator workload."
    )
    scenario["status_explanations"] = {
        "DRAFT_REVIEW": f"{size} synthetic identities await one portfolio confirmation.",
        "FUNDED_CERTIFIED": (
            f"One {size}-security stress portfolio was funded through the shared engine."
        ),
        "OBSERVED_NO_CHANGE_CERTIFIED": (
            "A later observation preserved portfolio economics."
        ),
        "TRANSITION_CERTIFIED": (
            "A later observation produced one reduce and one fund leg."
        ),
        "CORRECTED_CERTIFIED": (
            "A non-economic correction preserved economics and certification history."
        ),
    }
    scenario["no_change"]["locator"] = (
        f"fixture://engine-scale-{size}/nstar/no-change-v1"
    )
    scenario["transition"]["locator"] = (
        f"fixture://engine-scale-{size}/harbor-meridian/transition-v1"
    )
    scenario["correction"]["source_identity"] = (
        f"ENGINE-SCALE-{size}:CORRECTION:MERIDIAN-ANNOTATION"
    )

    instruments: list[dict[str, Any]] = []
    for index in range(size):
        template = deepcopy(SCENARIO_25["instruments"][index % 25])
        cohort = (index // 25) + 1
        if cohort > 1:
            template["symbol"] = f"{template['symbol']}{cohort}"
            template["name"] = f"{template['name']} Cohort {cohort}"
            template["permanent_key"] = template["permanent_key"].replace(
                ":COMMON", f":SCALE_COHORT_{cohort}:COMMON"
            )
            template["evidence_content"] = (
                f"{template['evidence_content']} Synthetic stress cohort {cohort}."
            )
            template["evidence_slug"] = (
                f"{template['evidence_slug']}-cohort-{cohort}"
            )
            template["principal_claim"] = (
                f"{template['principal_claim']} Synthetic stress cohort {cohort}."
            )
            template["hard_falsifiers"] = [
                f"{value}_cohort_{cohort}"
                for value in template["hard_falsifiers"]
            ]
            template["watch_conditions"] = [
                f"{value}_cohort_{cohort}"
                for value in template["watch_conditions"]
            ]
        instruments.append(template)
    scenario["instruments"] = instruments
    return scenario


SCENARIO_50 = _scale_characterization_scenario(50)
SCENARIO_100 = _scale_characterization_scenario(100)


def _prospective_25_scenario() -> dict[str, Any]:
    """Derive the runtime-observation profile from the accepted 25-security baseline."""

    scenario = deepcopy(SCENARIO_25)
    scenario.update(
        {
            "scenario_id": PROSPECTIVE_25_SCENARIO_ID,
            "title": "GV Prospective Paper Baseline 25",
            "id_domain": "GV-PROSPECTIVE-PAPER-BASELINE-25",
            "claim_boundary": (
                "Human-confirmed prospective paper observations on the accepted "
                "25-security opportunity set; no provider, broker, alpha, or live-capital claim."
            ),
            "fixture_namespace": "prospective-paper-25",
            "source_scenario_id": PORTFOLIO_25_SCENARIO_ID,
            "runtime_observation_mode": True,
            "initial_decision_reason": "BOOTSTRAP_ACCEPTED_25_SECURITY_BASELINE",
            "initial_changed_why_reason": (
                "The prospective profile bootstraps the accepted 25-security certified "
                "initial portfolio before any operator-supplied observation."
            ),
        }
    )
    scenario["timeline"] = {
        "cash_opened_at": "2026-08-01T08:55:00.000000Z",
        "initial_decision_at": "2026-08-01T09:05:00.000000Z",
        "aim_confirmed_at": "2026-08-01T09:05:30.000000Z",
        "initial_transition_at": "2026-08-01T09:06:00.000000Z",
        "initial_order_start_minute": 7,
        "initial_certified_at": "2026-08-01T09:20:00.000000Z",
    }
    scenario["portfolio_aim"]["effective_at"] = "2026-08-01T09:00:00.000000Z"
    scenario["portfolio_aim"]["objective"] = (
        "Operate the accepted 25-security paper portfolio through human-supplied "
        "prospective observations and explicit confirmation."
    )
    scenario["status_explanations"] = {
        "DRAFT_REVIEW": "The accepted 25-security baseline awaits bootstrap confirmation.",
        "FUNDED_CERTIFIED": (
            "The accepted 25-security initial portfolio is certified and ready for "
            "operator-supplied prospective observations."
        ),
    }
    # Later observations are runtime authority. Scenario-authored episodes are absent.
    scenario.pop("no_change", None)
    scenario.pop("transition", None)
    scenario.pop("correction", None)
    return scenario


SCENARIO_PROSPECTIVE_25 = _prospective_25_scenario()


def _real_mu_prospective_scenario() -> dict[str, Any]:
    """One real MU identity driven by the banked MU/NVDA reconciliation."""

    reconciliation_hash = (
        "89cc062783ae367c1bf259cfb7b355e0812ca162995b7ce05743a39e99592017"
    )
    return {
        "scenario_id": REAL_MU_PROSPECTIVE_SCENARIO_ID,
        "title": "GV Real Evidence — MU Paper Decision",
        "id_domain": "GV-REAL-EVIDENCE-MU-PORTFOLIO-1",
        "schema_version": "gv_operated_portfolio_v3",
        "claim_boundary": (
            "One real MU identity and classified cash driven by already-banked MU/NVDA "
            "evidence. Paper ABSTAIN/NO_POSITION authority only; no score, alpha, "
            "investability, provider, broker, or live-capital claim."
        ),
        "fixture_namespace": "real-evidence-mu",
        "identity_namespace": "SEC_CIK_LISTING_V1",
        "minimum_funded_positions": 0,
        "minimum_economic_clusters": 1,
        "minimum_total_cash_bps": 10000,
        "cash_openings": [
            {"bucket": "AVAILABLE", "amount": "10000"},
            {"bucket": "RESEARCH_RESERVE", "amount": "1000"},
        ],
        "portfolio_aim": {
            "objective": (
                "Operate one real MU paper decision with explicit classified cash and "
                "no position unless source evidence advances."
            ),
            "allowed_actions": ["HOLD", "CASH"],
            "effective_at": "2026-08-02T12:00:00.000000Z",
        },
        "timeline": {
            "cash_opened_at": "2026-08-02T11:55:00.000000Z",
            "initial_decision_at": "2026-08-02T12:05:00.000000Z",
            "aim_confirmed_at": "2026-08-02T12:05:30.000000Z",
            "initial_transition_at": "2026-08-02T12:06:00.000000Z",
            "initial_order_start_minute": 7,
            "initial_certified_at": "2026-08-02T12:08:00.000000Z",
        },
        "status_explanations": {
            "DRAFT_REVIEW": (
                "The real MU evidence decision and classified cash await operator confirmation."
            ),
            "FUNDED_CERTIFIED": (
                "The operator certified a cash-only MU ABSTAIN/NO_POSITION decision; "
                "no security position or execution authority exists."
            ),
        },
        "initial_decision_reason": "MU_NVDA_RECONCILIATION_HOLD_FOR_EVIDENCE",
        "initial_changed_why_reason": (
            "The banked reconciliation did not establish Micron-specific physical "
            "supply persistence, so MU remained ABSTAIN and all capital stayed classified cash."
        ),
        "source_scenario_id": "GV_MU_NVDA_RECONCILED_EVIDENCE_1",
        "source_authority": {
            "schema_version": "gv_v2_mu_nvda_reconciliation_v1",
            "case_id": "GV_V2_MU_NVDA_G_SUPPLY_RECONCILIATION_1",
            "reconciliation_hash": reconciliation_hash,
            "verification_mode": "REBUILD_FROM_BANKED_SOURCES",
            "result_path": (
                "data/gv_v2_reconciliation/mu_nvda_supply_1/"
                "reconciliation_result.json"
            ),
        },
        "runtime_observation_mode": True,
        "instruments": [
            {
                "identity_namespace": "SEC_CIK_LISTING_V1",
                "permanent_key": "SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
                "security_class": "COMMON_STOCK",
                "symbol": "MU",
                "name": "Micron Technology, Inc.",
                "economic_cluster": "SEMICONDUCTOR_MEMORY",
                "evidence_content": (
                    "The banked MU filing and independent NVDA facts partially corroborate "
                    "a broad memory-price and supply-constrained environment, but do not "
                    "establish Micron-specific physical supply persistence."
                ),
                "evidence_slug": "mu-nvda-reconciliation",
                "evidence_locator": (
                    "repo://data/gv_v2_reconciliation/mu_nvda_supply_1/"
                    f"reconciliation_result.json#reconciliation_hash={reconciliation_hash}"
                ),
                "outcome": "ABSTAIN",
                "net_score_bps": 0,
                "target_quantity": "0",
                "reference_price": "1",
                "principal_claim": (
                    "Micron-specific physical supply persistence remains unestablished; "
                    "retain NO_POSITION pending the missing discriminator."
                ),
                "hard_falsifiers": [
                    "banked source hash or source-family linkage fails verification"
                ],
                "watch_conditions": [
                    "independent point-in-time Micron shipment, allocation, inventory, "
                    "utilization, capacity-ramp, or channel evidence persists across periods"
                ],
            }
        ],
    }


SCENARIO_REAL_MU_PROSPECTIVE = _real_mu_prospective_scenario()


def _operated_paper_capital_scenario() -> dict[str, Any]:
    """Forward-operated MU paper authority without rewriting the banked specimen."""

    scenario = deepcopy(SCENARIO_REAL_MU_PROSPECTIVE)
    scenario.update(
        {
            "scenario_id": OPERATED_PAPER_CAPITAL_SCENARIO_ID,
            "title": "GV Operated Paper Capital — MU",
            "id_domain": "GV-OPERATED-PAPER-CAPITAL-1",
            "claim_boundary": (
                "One owner-supplied, market-identified MU paper-capital decision using "
                "the certified cash baseline. Operator assertions are content-addressed "
                "but are not provider-verified, alpha evidence, investment advice, broker "
                "authority, or live-capital authority."
            ),
            "fixture_namespace": "operated-paper-capital-mu",
            "source_scenario_id": REAL_MU_PROSPECTIVE_SCENARIO_ID,
            "forward_operated_market_packet": True,
        }
    )
    scenario["portfolio_aim"] = {
        **scenario["portfolio_aim"],
        "objective": (
            "Operate one bounded owner-authored MU paper decision from certified cash "
            "through preview, explicit disposition, persistence, certification, and replay."
        ),
        "allowed_actions": ["BUY", "HOLD", "CASH"],
    }
    scenario["status_explanations"] = {
        "DRAFT_REVIEW": (
            "The forward-operated MU paper workspace awaits bootstrap confirmation."
        ),
        "FUNDED_CERTIFIED": (
            "The certified MU workspace is ready for one owner-supplied evidence and "
            "market packet; no paper position exists until explicit confirmation."
        ),
    }
    scenario["initial_decision_reason"] = "BOOTSTRAP_BANKED_MU_CASH_BASELINE"
    scenario["initial_changed_why_reason"] = (
        "The forward-operated workspace starts from the certified banked MU cash-only "
        "baseline without modifying its historical evidence contract."
    )
    return scenario


SCENARIO_OPERATED_PAPER_CAPITAL = _operated_paper_capital_scenario()


_SCENARIOS = {
    DEFAULT_SCENARIO_ID: SCENARIO_10,
    PORTFOLIO_25_SCENARIO_ID: SCENARIO_25,
    ENGINE_SCALE_50_SCENARIO_ID: SCENARIO_50,
    ENGINE_SCALE_100_SCENARIO_ID: SCENARIO_100,
    PROSPECTIVE_25_SCENARIO_ID: SCENARIO_PROSPECTIVE_25,
    REAL_MU_PROSPECTIVE_SCENARIO_ID: SCENARIO_REAL_MU_PROSPECTIVE,
    OPERATED_PAPER_CAPITAL_SCENARIO_ID: SCENARIO_OPERATED_PAPER_CAPITAL,
}


def get_scenario(scenario_id: str = DEFAULT_SCENARIO_ID) -> dict[str, Any]:
    try:
        return deepcopy(_SCENARIOS[scenario_id])
    except KeyError as exc:
        raise ValueError(f"UNKNOWN_OPERATED_SCENARIO:{scenario_id}") from exc


def scenario_hash(scenario: Mapping[str, Any]) -> str:
    return domain_hash("GV-OPERATED-SCENARIO:V1", dict(scenario))


def available_scenario_ids() -> tuple[str, ...]:
    return tuple(_SCENARIOS)
