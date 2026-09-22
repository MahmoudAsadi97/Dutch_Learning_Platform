"""Validate the local Azure parameter file without network access, spending or printing values."""
from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

TEMPLATE = Path(__file__).resolve().parents[1] / "infra" / "main.bicep"
SECRETS = {"authClientSecret": 16, "assertionSigningKey": 32,
           "postgresAdminPassword": 24, "postgresAppPassword": 24}
EMAIL = re.compile(r"[^\s@,]+@[^\s@,]+\.[^\s@,]+")
DIGEST_IMAGE = re.compile(r"[a-z0-9]+\.azurecr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def read_parameters(path: Path) -> dict:
    try:
        if path.stat().st_size > 128 * 1024:
            raise ValueError("parameter file is too large")
        document = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    except (OSError, UnicodeError, ValueError) as exc:
        # JSON parser errors may contain secrets. Never print them, or the source file.
        raise ValueError("Cannot read a valid UTF-8 JSON parameter file (maximum 128 KiB; no duplicate fields).") from exc
    if not isinstance(document, dict) or not isinstance(document.get("parameters"), dict):
        raise TypeError("The file must contain an ARM parameters object.")
    return document["parameters"]


def valid_email(value) -> bool:
    return isinstance(value, str) and bool(EMAIL.fullmatch(value)) and not value.lower().endswith(
        ("@example.com", "@example.org", "@example.net", ".invalid")
    )


def valid_uuid(value) -> bool:
    try:
        return isinstance(value, str) and bool(UUID(value).int) and str(UUID(value)) == value.lower()
    except ValueError:
        return False


def validate(parameters: dict, *, bootstrap: bool = False, today: datetime | None = None) -> tuple[list[str], list[str]]:
    """Known field names only in messages. No values or secret identifiers are returned."""
    errors, warnings = [], []
    types = dict(re.findall(r"^param (\w+) (string|int|bool|array)\b", TEMPLATE.read_text(), re.MULTILINE))
    values = {}
    references = set()
    for key, entry in parameters.items():
        if key not in types:
            errors.append("Unknown parameter field; compare the file with infra/main.bicep.")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{key}: must use an ARM value or secret reference object.")
            continue
        if set(entry) == {"reference"} and key in SECRETS:
            ref = entry["reference"]
            vault = ref.get("keyVault", {}) if isinstance(ref, dict) else {}
            if (not isinstance(vault, dict) or not isinstance(vault.get("id"), str)
                    or not re.fullmatch(r"/subscriptions/[\w-]+/resourceGroups/[^/]+/providers/Microsoft.KeyVault/vaults/[^/]+",
                                        vault["id"], re.IGNORECASE)
                    or not isinstance(ref.get("secretName"), str) or not ref["secretName"].strip()):
                errors.append(f"{key}: malformed Key Vault reference.")
            else:
                references.add(key)
                warnings.append(f"{key}: referenced secret value and access need Azure validation.")
            continue
        if set(entry) != {"value"}:
            errors.append(f"{key}: requires exactly one value field (or a supported secret reference).")
            continue
        value = entry["value"]
        expected = {"string": str, "int": int, "bool": bool, "array": list}[types[key]]
        if type(value) is not expected:
            errors.append(f"{key}: wrong parameter type.")
            continue
        if "REPLACE_" in json.dumps(value).upper():
            errors.append(f"{key}: replace the template placeholder.")
        values[key] = value

    required = {*SECRETS, "authClientId", "allowedPrincipalObjectIds", "ownerAllowlist", "chatModelName",
                "chatModelVersion", "budgetStartDate", "budgetAlertEmails"}
    for key in sorted(required - values.keys() - references):
        errors.append(f"{key}: required for the owner-only deployment.")
    for key, minimum in SECRETS.items():
        if key in values and (len(values[key]) < minimum or values[key].strip() != values[key]):
            errors.append(f"{key}: requires at least {minimum} characters with no surrounding whitespace.")
    secrets = [values[key] for key in SECRETS if key in values]
    if len(set(secrets)) != len(secrets):
        errors.append("Use different values for the database passwords, assertion key and sign-in secret.")

    if not re.fullmatch(r"[a-z][a-z0-9]{2,11}", values.get("name", "dlp")):
        errors.append("name: use 3–12 lowercase letters/digits, starting with a letter.")
    for key in ("authClientId", "tenantId"):
        if key in values and not valid_uuid(values[key]):
            errors.append(f"{key}: requires a nonzero UUID.")
    if "allowedPrincipalObjectIds" in values:
        ids = values["allowedPrincipalObjectIds"]
        if not ids or not all(valid_uuid(item) for item in ids):
            errors.append("allowedPrincipalObjectIds: requires at least one user object UUID.")
    if "ownerAllowlist" in values and not all(valid_email(item.strip()) for item in values["ownerAllowlist"].split(",")):
        errors.append("ownerAllowlist: use the actual signed-in email claim(s), separated by commas.")
    if "budgetAlertEmails" in values:
        emails = values["budgetAlertEmails"]
        if not emails or not all(valid_email(item) for item in emails):
            errors.append("budgetAlertEmails: requires actual alert email addresses.")
    for key in ("chatModelName", "chatModelVersion"):
        if key in values and not values[key].strip():
            errors.append(f"{key}: choose an explicit region-supported value.")
    if bool(values.get("strongModelName", "").strip()) != bool(values.get("strongModelVersion", "").strip()):
        errors.append("strongModelName and strongModelVersion: supply both or leave both empty.")
    if values.get("chatDeploymentSku", "Standard") not in {"Standard", "DataZoneStandard", "GlobalStandard"}:
        errors.append("chatDeploymentSku: unsupported deployment SKU.")
    for key, kind in types.items():
        if kind == "int" and key in values and values[key] < 1:
            errors.append(f"{key}: must be positive.")
    now = today or datetime.now(UTC)
    if "budgetStartDate" in values:
        start = values["budgetStartDate"]
        try:
            parsed = datetime.strptime(start, "%Y-%m-01T00:00:00Z").replace(tzinfo=UTC)
            if parsed > now or (bootstrap and parsed.strftime("%Y-%m") != now.strftime("%Y-%m")):
                raise ValueError
        except ValueError:
            errors.append("budgetStartDate: use the first day of this month in YYYY-MM-01T00:00:00Z form for bootstrap.")

    if bootstrap and any(values.get(key, False) for key in ("deployApplications", "deployMigrationJob", "publicWeb")):
        errors.append("Bootstrap must leave applications, migration job and public web disabled until real images exist.")
    if values.get("publicWeb", False) and not values.get("deployApplications", False):
        errors.append("publicWeb requires deployApplications; publish only after sign-in verification.")
    if values.get("deployApplications", False):
        if values.get("paidUsageApproved") is not True:
            errors.append("paidUsageApproved: runtime requires an explicit approved allowance.")
        if not DIGEST_IMAGE.fullmatch(values.get("webImage", "")):
            errors.append("webImage: runtime requires an immutable Azure registry image digest.")
    if ((values.get("deployApplications", False) or values.get("deployMigrationJob", False))
            and not DIGEST_IMAGE.fullmatch(values.get("apiImage", ""))):
        errors.append("apiImage: runtime/migration requires an immutable Azure registry image digest.")
    warnings.append("This is an offline check. Azure availability, identity permissions, secret strength, "
                    "prices and quotas remain unverified.")
    warnings.append("Creating the foundation incurs infrastructure costs even when paid model usage is disabled. "
                    "Budgets send alerts, not hard stops.")
    return list(dict.fromkeys(errors)), warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=Path("infra/parameters.local.json"))
    parser.add_argument("--bootstrap", action="store_true",
                        help="Check a new foundation: current budget month and no runtime exposure.")
    args = parser.parse_args()
    try:
        errors, warnings = validate(read_parameters(args.parameters), bootstrap=args.bootstrap)
    except (ValueError, TypeError, OSError) as exc:
        print(str(exc) if isinstance(exc, ValueError | TypeError) else "Cannot read the local Bicep template.")
        return 1
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"NOTE: {message}")
    if errors:
        print("Configuration needs correction. No Azure calls were made.")
        return 1
    print("Local configuration checks passed. No resources were created and no secrets were printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
