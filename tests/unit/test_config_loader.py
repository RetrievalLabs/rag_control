"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from pathlib import Path
from typing import TypedDict

import pytest

from rag_control.core.config_loader import load_control_plane_config
from rag_control.exceptions import ControlPlaneConfigValidationError
from rag_control.models.config import ControlPlaneConfig


class _LoaderCase(TypedDict, total=False):
    name: str
    path: Path
    expected_error: str | None
    simulate_read_error: bool


def test_load_control_plane_config_with_multiple_conditions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    valid_config_path = tmp_path / "valid.yaml"
    valid_config_path.write_text(
        """
policies:
  - name: default_policy
    generation: {}
    logging: {}
    enforcement: {}
filters:
  - name: default_filter
    condition:
      field: org_tier
      operator: equals
      value: enterprise
      source: user
orgs:
  - org_id: test_org
    default_policy: default_policy
    document_policy:
      filter_name: default_filter
    policy_rules:
      - name: allow_enterprise
        priority: 1
        effect: allow
        apply_policy: default_policy
        when:
          all:
            - field: org_tier
              operator: equals
              value: enterprise
              source: user
""".strip(),
        encoding="utf-8",
    )

    invalid_yaml_path = tmp_path / "invalid_yaml.yaml"
    invalid_yaml_path.write_text("policies: [", encoding="utf-8")

    non_mapping_root_path = tmp_path / "non_mapping_root.yaml"
    non_mapping_root_path.write_text("- item1\n- item2\n", encoding="utf-8")

    invalid_schema_path = tmp_path / "invalid_schema.yaml"
    invalid_schema_path.write_text("{}", encoding="utf-8")

    invalid_filter_in_value_path = tmp_path / "invalid_filter_in_value.yaml"
    invalid_filter_in_value_path.write_text(
        """
policies:
  - name: default_policy
    generation: {}
    logging: {}
    enforcement: {}
filters:
  - name: default_filter
    condition:
      field: org_tier
      operator: in
      value: enterprise
      source: user
orgs:
  - org_id: test_org
    default_policy: default_policy
    document_policy:
      filter_name: default_filter
    policy_rules: []
""".strip(),
        encoding="utf-8",
    )

    invalid_filter_empty_path = tmp_path / "invalid_filter_empty.yaml"
    invalid_filter_empty_path.write_text(
        """
policies:
  - name: default_policy
    generation: {}
    logging: {}
    enforcement: {}
filters:
  - name: default_filter
orgs:
  - org_id: test_org
    default_policy: default_policy
    document_policy:
      filter_name: default_filter
    policy_rules: []
""".strip(),
        encoding="utf-8",
    )

    invalid_filter_mixed_path = tmp_path / "invalid_filter_mixed.yaml"
    invalid_filter_mixed_path.write_text(
        """
policies:
  - name: default_policy
    generation: {}
    logging: {}
    enforcement: {}
filters:
  - name: default_filter
    condition:
      field: org_tier
      operator: equals
      value: enterprise
      source: user
    and:
      - name: nested_filter
        condition:
          field: department
          operator: equals
          value: finance
          source: user
orgs:
  - org_id: test_org
    default_policy: default_policy
    document_policy:
      filter_name: default_filter
    policy_rules: []
""".strip(),
        encoding="utf-8",
    )

    empty_file_path = tmp_path / "empty.yaml"
    empty_file_path.write_text("", encoding="utf-8")

    read_error_path = tmp_path / "read_error.yaml"
    read_error_path.write_text("policies: []", encoding="utf-8")

    directory_path = tmp_path / "config_dir"
    directory_path.mkdir()

    original_read_text = Path.read_text

    test_cases: list[_LoaderCase] = [
        {
            "name": "valid_config",
            "path": valid_config_path,
            "expected_error": None,
        },
        {
            "name": "missing_file",
            "path": tmp_path / "missing.yaml",
            "expected_error": "control plane config file does not exist",
        },
        {
            "name": "path_is_directory",
            "path": directory_path,
            "expected_error": "control plane config path is not a file",
        },
        {
            "name": "read_text_os_error",
            "path": read_error_path,
            "expected_error": "unable to read control plane config file",
            "simulate_read_error": True,
        },
        {
            "name": "invalid_yaml",
            "path": invalid_yaml_path,
            "expected_error": "invalid YAML in control plane config",
        },
        {
            "name": "non_mapping_root",
            "path": non_mapping_root_path,
            "expected_error": "control plane config root must be a mapping/object",
        },
        {
            "name": "invalid_schema",
            "path": invalid_schema_path,
            "expected_error": "invalid control plane config",
        },
        {
            "name": "invalid_filter_in_value",
            "path": invalid_filter_in_value_path,
            "expected_error": "value must be a list for 'in' operator",
        },
        {
            "name": "invalid_filter_empty",
            "path": invalid_filter_empty_path,
            "expected_error": "must include exactly one of: condition, and, or",
        },
        {
            "name": "invalid_filter_mixed",
            "path": invalid_filter_mixed_path,
            "expected_error": "must include exactly one of: condition, and, or",
        },
        {
            "name": "empty_file",
            "path": empty_file_path,
            "expected_error": "invalid control plane config",
        },
    ]

    for case in test_cases:
        with monkeypatch.context() as patch:
            if case.get("simulate_read_error"):
                target_path = case["path"]

                def _mock_read_text(self: Path, encoding: str = "utf-8") -> str:
                    if self == target_path:
                        raise OSError("simulated read failure")
                    return original_read_text(self, encoding=encoding)

                patch.setattr(Path, "read_text", _mock_read_text)

            if case["expected_error"] is None:
                config = load_control_plane_config(case["path"])
                assert isinstance(config, ControlPlaneConfig), case["name"]
                continue

            assert case["expected_error"] is not None
            with pytest.raises(ControlPlaneConfigValidationError, match=case["expected_error"]):
                load_control_plane_config(case["path"])
