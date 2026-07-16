"""Verify the GV-FS0 Protocol V1 freeze in bootstrap or enforced mode."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_fs0_canonical import (  # noqa: E402
    CanonicalizationError,
    canonical_document_bytes,
    parse_canonical_document_bytes,
    sha256_bytes,
    terminal_newline_count,
)
from scripts.generate_gv_fs0_protocol_v1 import (  # noqa: E402
    ARTIFACT_ROOT,
    CONTRACT,
    PROTOCOL_ID,
    contract_literal_check,
    rendered_artifacts,
)
VALIDATION_ROOT = ROOT / "validation"
if str(VALIDATION_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATION_ROOT))

from gv_fs0_ci_reference_encoder import verify_vectors  # noqa: E402

MANIFEST = ARTIFACT_ROOT / "gv_fs0_freeze_manifest_v1.json"
MANIFEST_VERSION = "gv_fs0_freeze_manifest_v1"
GITATTRIBUTES = ROOT / ".gitattributes"

ARTIFACT_IDS = {
    "schemas/gv_fs0_source_fixture_v1.schema.json": "gv_fs0_source_fixture_v1",
    "schemas/gv_fs0_decision_envelope_v1.schema.json": "gv_fs0_decision_envelope_v1",
    "schemas/gv_fs0_source_intent_v1.schema.json": "gv_fs0_source_intent_v1",
    "schemas/gv_fs0_portfolio_event_v1.schema.json": "gv_fs0_portfolio_event_v1",
    "schemas/gv_fs0_snapshot_v1.schema.json": "gv_fs0_snapshot_v1",
    "schemas/gv_fs0_verifier_input_v1.schema.json": "gv_fs0_verifier_input_v1",
    "schemas/gv_fs0_verifier_result_v1.schema.json": "gv_fs0_verifier_result_v1",
    "schemas/gv_fs0_verifier_attempt_v1.schema.json": "gv_fs0_verifier_attempt_v1",
    "schemas/gv_fs0_certification_v1.schema.json": "gv_fs0_certification_v1",
    "schemas/gv_fs0_certified_decision_result_v1.schema.json": "gv_fs0_certified_decision_result_v1",
    "schemas/gv_fs0_certified_bundle_v1.schema.json": "gv_fs0_certified_bundle_v1",
    "schemas/gv_fs0_blocked_evidence_v1.schema.json": "gv_fs0_blocked_evidence_v1",
    "registries/gv_fs0_certification_failure_registry_v1.json": "gv_fs0_certification_failure_registry_v1",
    "registries/gv_fs0_operational_error_registry_v1.json": "gv_fs0_operational_error_registry_v1",
    "tables/gv_fs0_event_ranks_v1.json": "gv_fs0_event_ranks_v1",
    "tables/gv_fs0_generated_event_slots_v1.json": "gv_fs0_generated_event_slots_v1",
    "tables/gv_fs0_transition_ownership_v1.json": "gv_fs0_transition_ownership_v1",
    "vectors/gv_fs0_canonical_vectors_v1.json": "gv_fs0_canonical_vectors_v1",
}

FROZEN_PATHS = [
    "docs/architecture/gv_fs0_certification_and_data_authority_contract.md",
    *[f"contracts/gv_fs0/v1/{path}" for path in ARTIFACT_IDS],
]


def _git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_object_format() -> str:
    override = os.environ.get("GV_FS0_GIT_OBJECT_FORMAT")
    if override is not None:
        if override not in {"sha1", "sha256"}:
            raise RuntimeError(f"unsupported Git object format override: {override}")
        return override
    result = _git(["rev-parse", "--show-object-format"])
    value = result.stdout.decode("ascii").strip()
    if value not in {"sha1", "sha256"}:
        raise RuntimeError(f"unsupported Git object format: {value}")
    return value


def git_blob_oid(data: bytes, object_format: str) -> str:
    preimage = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    digest = hashlib.sha1 if object_format == "sha1" else hashlib.sha256
    return digest(preimage).hexdigest()


def _artifact_id(path: str) -> str:
    if path == FROZEN_PATHS[0]:
        return "gv_fs0_certification_and_data_authority_contract"
    relative = path.removeprefix("contracts/gv_fs0/v1/")
    return ARTIFACT_IDS[relative]


def manifest_object() -> dict[str, Any]:
    object_format = git_object_format()
    entries = []
    for relative_path in FROZEN_PATHS:
        data = (ROOT / relative_path).read_bytes()
        entries.append(
            {
                "artifact_id": _artifact_id(relative_path),
                "byte_length": len(data),
                "git_blob_oid": git_blob_oid(data, object_format),
                "path": relative_path,
                "sha256": sha256_bytes(data),
                "terminal_newline_count": terminal_newline_count(data),
            }
        )
    return {
        "entries": entries,
        "frozen_surface_count": len(entries),
        "git_object_format": object_format,
        "manifest_version": MANIFEST_VERSION,
        "protocol_id": PROTOCOL_ID,
    }


def rendered_manifest() -> bytes:
    return canonical_document_bytes(manifest_object())


def _load_manifest(raw: bytes | None = None) -> dict[str, Any]:
    data = MANIFEST.read_bytes() if raw is None else raw
    value = parse_canonical_document_bytes(data)
    if not isinstance(value, dict):
        raise CanonicalizationError("MANIFEST_ROOT_NOT_OBJECT")
    return value


def _expected_artifact_files() -> set[Path]:
    return {ARTIFACT_ROOT / path for path in ARTIFACT_IDS}


def _actual_artifact_files() -> set[Path]:
    return {path for path in ARTIFACT_ROOT.rglob("*") if path.is_file() and path != MANIFEST}


def _check_lf_attributes() -> list[str]:
    try:
        text = GITATTRIBUTES.read_text(encoding="utf-8")
    except OSError as exc:
        return [f".gitattributes unreadable: {exc}"]
    required = {
        "docs/architecture/gv_fs0_certification_and_data_authority_contract.md text eol=lf",
        "contracts/gv_fs0/v1/**/*.json text eol=lf",
    }
    return [f"missing .gitattributes rule: {line}" for line in sorted(required) if line not in text]


def check_current_tree() -> list[str]:
    failures: list[str] = []
    generated = rendered_artifacts()
    for relative, expected in generated.items():
        path = ARTIFACT_ROOT / relative
        try:
            observed = path.read_bytes()
        except OSError:
            failures.append(f"missing artifact: {relative}")
            continue
        if observed != expected:
            failures.append(f"generated artifact mismatch: {relative}")

    expected_files = _expected_artifact_files()
    actual_files = _actual_artifact_files()
    for path in sorted(expected_files - actual_files):
        failures.append(f"missing artifact file: {path.relative_to(ROOT).as_posix()}")
    for path in sorted(actual_files - expected_files):
        failures.append(f"extra artifact file: {path.relative_to(ROOT).as_posix()}")

    failures.extend(contract_literal_check())
    failures.extend(_check_lf_attributes())
    failures.extend(verify_vectors(ARTIFACT_ROOT / "vectors/gv_fs0_canonical_vectors_v1.json"))

    for relative_path in FROZEN_PATHS:
        data = (ROOT / relative_path).read_bytes()
        if b"\r\n" in data or b"\r" in data:
            failures.append(f"non-LF line ending: {relative_path}")
        if terminal_newline_count(data) != 1:
            failures.append(f"terminal_newline_count != 1: {relative_path}")

    try:
        observed_manifest = MANIFEST.read_bytes()
        _load_manifest(observed_manifest)
    except (OSError, CanonicalizationError) as exc:
        failures.append(f"manifest invalid: {exc}")
    else:
        expected_manifest = rendered_manifest()
        if observed_manifest != expected_manifest:
            failures.append("manifest content mismatch")

    return failures


def _git_show(base_ref: str, path: str) -> bytes | None:
    result = _git(["show", f"{base_ref}:{path}"], check=False)
    return result.stdout if result.returncode == 0 else None


def check_enforced_base(base_ref: str) -> list[str]:
    failures: list[str] = []
    for path in [*FROZEN_PATHS, MANIFEST.relative_to(ROOT).as_posix()]:
        base_bytes = _git_show(base_ref, path)
        if base_bytes is None:
            failures.append(f"frozen base missing: {path}")
            continue
        current = (ROOT / path).read_bytes()
        if current != base_bytes:
            failures.append(f"same-version frozen surface changed: {path}")
    return failures


def _manifest_for_bytes(overrides: dict[str, bytes]) -> bytes:
    object_format = git_object_format()
    entries = []
    for path in FROZEN_PATHS:
        data = overrides.get(path, (ROOT / path).read_bytes())
        entries.append(
            {
                "artifact_id": _artifact_id(path),
                "byte_length": len(data),
                "git_blob_oid": git_blob_oid(data, object_format),
                "path": path,
                "sha256": sha256_bytes(data),
                "terminal_newline_count": terminal_newline_count(data),
            }
        )
    return canonical_document_bytes(
        {
            "entries": entries,
            "frozen_surface_count": len(entries),
            "git_object_format": object_format,
            "manifest_version": MANIFEST_VERSION,
            "protocol_id": PROTOCOL_ID,
        }
    )


def mutation_probe_failures() -> list[str]:
    """Return probe names that were not rejected by the bootstrap authority chain."""
    failures: list[str] = []
    generated = rendered_artifacts()
    cases: list[tuple[str, str, bytes]] = []

    schema_path = "contracts/gv_fs0/v1/schemas/gv_fs0_source_fixture_v1.schema.json"
    registry_path = "contracts/gv_fs0/v1/registries/gv_fs0_operational_error_registry_v1.json"
    contract_path = FROZEN_PATHS[0]
    vector_path = "contracts/gv_fs0/v1/vectors/gv_fs0_canonical_vectors_v1.json"

    schema = (ROOT / schema_path).read_bytes()
    cases.append(("one_byte_schema", schema_path, schema.replace(b"false", b"true", 1)))
    registry = (ROOT / registry_path).read_bytes()
    cases.append(("registry_semantic", registry_path, registry.replace(b"RECOVERABLE", b"TERMINAL", 1)))
    contract = (ROOT / contract_path).read_bytes()
    cases.append(("contract_change", contract_path, contract.replace(b"max_session_lag = 0", b"max_session_lag = 1", 1)))
    vector = (ROOT / vector_path).read_bytes()
    cases.append(("vector_change", vector_path, vector.replace(b"lowercase_hex", b"uppercase_hex", 1)))
    cases.append(("crlf_conversion", schema_path, schema.replace(b"\n", b"\r\n")))

    for name, path, mutated in cases:
        relative_artifact = path.removeprefix("contracts/gv_fs0/v1/")
        rejected = False
        if relative_artifact in generated and generated[relative_artifact] != mutated:
            rejected = True
        if path == contract_path and b"max_session_lag = 0" not in mutated:
            rejected = True
        if terminal_newline_count(mutated) != 1 or b"\r" in mutated:
            rejected = True
        if not rejected:
            failures.append(name)

    dishonest_path = schema_path
    dishonest_bytes = schema.replace(b"false", b"true", 1)
    dishonest_manifest = _manifest_for_bytes({dishonest_path: dishonest_bytes})
    manifest_value = _load_manifest(dishonest_manifest)
    manifest_accepts = any(
        entry["path"] == dishonest_path and entry["sha256"] == sha256_bytes(dishonest_bytes)
        for entry in manifest_value["entries"]
    )
    generator_rejects = generated[dishonest_path.removeprefix("contracts/gv_fs0/v1/")] != dishonest_bytes
    if not (manifest_accepts and generator_rejects):
        failures.append("dishonest_artifact_and_manifest")
    return failures


def parity_object() -> dict[str, Any]:
    return {
        "frozen_surface_sha256": sha256_bytes(
            b"".join((ROOT / path).read_bytes() for path in FROZEN_PATHS)
        ),
        "manifest_sha256": sha256_bytes(MANIFEST.read_bytes()),
        "protocol_id": PROTOCOL_ID,
        "vector_sha256": sha256_bytes(
            (ARTIFACT_ROOT / "vectors/gv_fs0_canonical_vectors_v1.json").read_bytes()
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["bootstrap", "enforced"], default="bootstrap")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--render-manifest", action="store_true")
    parser.add_argument("--print-parity-json", action="store_true")
    parser.add_argument("--skip-mutation-probes", action="store_true")
    args = parser.parse_args(argv)

    if args.render_manifest:
        sys.stdout.buffer.write(rendered_manifest())
        return 0

    failures = check_current_tree()
    if not args.skip_mutation_probes:
        failures.extend(f"mutation probe not rejected: {name}" for name in mutation_probe_failures())
    if args.mode == "enforced":
        failures.extend(check_enforced_base(args.base_ref))

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    if args.print_parity_json:
        sys.stdout.buffer.write(canonical_document_bytes(parity_object()))
    else:
        print(f"GV-FS0 protocol freeze {args.mode}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
