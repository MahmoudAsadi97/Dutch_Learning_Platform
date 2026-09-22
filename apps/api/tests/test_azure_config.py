from __future__ import annotations

import json
import sys
from datetime import UTC, datetime

import pytest

from tests.test_release_tools import module

NOW = datetime(2026, 9, 22, tzinfo=UTC)


def valid_parameters():
    # Deliberate test values, never live credentials or an actual model selection.
    values = {
        "name": "dlp", "authClientId": "ac3c7d26-424b-4486-a149-47bf75104298",
        "allowedPrincipalObjectIds": ["ac3c7d26-424b-4486-a149-47bf75104297"],
        "ownerAllowlist": "owner@taalstudio.test", "authClientSecret": "sign-in-test-" * 3,
        "assertionSigningKey": "signing-test-" * 4, "postgresAdminPassword": "admin-test-" * 3,
        "postgresAppPassword": "app-test-" * 3, "chatModelName": "test-model", "chatModelVersion": "test-version",
        "budgetStartDate": "2026-09-01T00:00:00Z", "budgetAlertEmails": ["budget@taalstudio.test"],
    }
    return {key: {"value": value} for key, value in values.items()}


def test_example_is_rejected_until_owner_fills_it():
    checker = module("check_azure_config")
    params = checker.read_parameters(checker.TEMPLATE.with_name("parameters.example.json"))
    errors, _ = checker.validate(params, bootstrap=True, today=NOW)
    assert any("placeholder" in error for error in errors)
    assert any("budgetStartDate" in error for error in errors)


def test_valid_foundation_is_offline_only():
    errors, warnings = module("check_azure_config").validate(valid_parameters(), bootstrap=True, today=NOW)
    assert errors == []
    assert any("unverified" in warning for warning in warnings)
    assert any("incurs infrastructure costs" in warning for warning in warnings)


@pytest.mark.parametrize("key,value", [
    ("name", "unsafe name"), ("authClientId", "not-a-uuid"), ("allowedPrincipalObjectIds", []),
    ("ownerAllowlist", "owner@example.com"), ("budgetAlertEmails", [123]),
    ("monthlyBudget", True), ("dailyTokens", -1), ("assertionSigningKey", "short"),
    ("paidUsageApproved", "true"), ("strongModelName", "without-version"),
    ("budgetStartDate", "2026-09-22T00:00:00Z"), ("chatDeploymentSku", "Batch"),
])
def test_invalid_fields_are_rejected_without_echoing_values(key, value):
    params = valid_parameters()
    params[key] = {"value": value}
    errors, _ = module("check_azure_config").validate(params, today=NOW)
    assert errors
    assert any(key in error for error in errors)
    assert "unsafe name" not in " ".join(errors)


def test_bootstrap_cannot_publish_and_runtime_requires_allowance_and_image_digests():
    checker = module("check_azure_config")
    params = valid_parameters()
    params.update({key: {"value": True} for key in ("deployApplications", "publicWeb")})
    errors, _ = checker.validate(params, bootstrap=True, today=NOW)
    assert any("Bootstrap" in error for error in errors)
    assert any("paidUsageApproved" in error for error in errors)
    assert any("apiImage" in error for error in errors)
    assert any("webImage" in error for error in errors)
    params.update({"paidUsageApproved": {"value": True},
                   "apiImage": {"value": "testregistry.azurecr.io/dlp-api@sha256:" + "a" * 64},
                   "webImage": {"value": "testregistry.azurecr.io/dlp-web@sha256:" + "b" * 64}})
    assert checker.validate(params, today=NOW)[0] == []


def test_duplicate_secret_json_is_refused_without_echo(tmp_path):
    checker = module("check_azure_config")
    path = tmp_path / "parameters.local.json"
    path.write_text('{"parameters": {"authClientSecret": {"value": "PRIVATE-SENTINEL", "value": "other"}}}')
    with pytest.raises(ValueError) as error:
        checker.read_parameters(path)
    assert "PRIVATE-SENTINEL" not in str(error.value)


def test_secret_reference_is_not_mistaken_for_verified_secret():
    checker = module("check_azure_config")
    params = valid_parameters()
    params["authClientSecret"] = {"reference": {
        "keyVault": {"id": "/subscriptions/test/resourceGroups/test/providers/Microsoft.KeyVault/vaults/test"},
        "secretName": "private-name",
    }}
    errors, warnings = checker.validate(params, today=NOW)
    assert errors == []
    assert any("secret value and access need Azure validation" in warning for warning in warnings)
    assert "private-name" not in " ".join(warnings)


def test_cli_does_not_echo_secrets_on_error(tmp_path, monkeypatch, capsys):
    checker = module("check_azure_config")
    path = tmp_path / "parameters.local.json"
    params = valid_parameters()
    params["postgresAdminPassword"] = {"value": "PRIVATE-SENTINEL"}
    path.write_text(json.dumps({"parameters": params}))
    monkeypatch.setattr(sys, "argv", ["check_azure_config.py", "--parameters", str(path)])
    assert checker.main() == 1
    assert "PRIVATE-SENTINEL" not in capsys.readouterr().out


def test_reused_secret_and_stale_bootstrap_month_are_rejected():
    checker = module("check_azure_config")
    params = valid_parameters()
    params["postgresAppPassword"] = params["postgresAdminPassword"]
    params["budgetStartDate"] = {"value": "2026-08-01T00:00:00Z"}
    errors, _ = checker.validate(params, bootstrap=True, today=NOW)
    assert any("different values" in error for error in errors)
    assert any("budgetStartDate" in error for error in errors)


@pytest.mark.parametrize("value", [None, [], "secret-value", {"keyVault": []}, {"keyVault": {"id": 42}}])
def test_malformed_secret_reference_does_not_crash(value):
    params = valid_parameters()
    params["authClientSecret"] = {"reference": value}
    errors, _ = module("check_azure_config").validate(params, today=NOW)
    assert any("authClientSecret" in error for error in errors)
