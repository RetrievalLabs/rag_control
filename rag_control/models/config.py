from __future__ import annotations

from pydantic import BaseModel, model_validator

from .filter import Filter
from .org import OrgConfig
from .policy import Policy


class ControlPlaneConfig(BaseModel):
    policies: list[Policy]
    filters: list[Filter]
    orgs: list[OrgConfig]

    @model_validator(mode="after")
    def validate_references(self) -> "ControlPlaneConfig":
        policy_names = [policy.name for policy in self.policies]
        filter_names = [flt.name for flt in self.filters]
        org_ids = [org.org_id for org in self.orgs]

        if len(policy_names) != len(set(policy_names)):
            raise ValueError("policies must have unique names")

        if len(filter_names) != len(set(filter_names)):
            raise ValueError("filters must have unique names")

        if len(org_ids) != len(set(org_ids)):
            raise ValueError("orgs must have unique org_id values")

        policy_name_set = set(policy_names)
        filter_name_set = set(filter_names)
        all_rule_names: list[str] = []

        for org in self.orgs:
            if org.default_policy not in policy_name_set:
                raise ValueError(
                    f"org '{org.org_id}' default_policy '{org.default_policy}' does not exist"
                )

            if org.filter_name is not None and org.filter_name not in filter_name_set:
                raise ValueError(
                    f"org '{org.org_id}' filter_name '{org.filter_name}' does not exist"
                )

            rule_names = [rule.name for rule in org.policy_rules]
            if len(rule_names) != len(set(rule_names)):
                raise ValueError(
                    f"org '{org.org_id}' policy_rules must have unique names"
                )
            all_rule_names.extend(rule_names)

            for rule in org.policy_rules:
                if (
                    rule.apply_policy is not None
                    and rule.apply_policy not in policy_name_set
                ):
                    raise ValueError(
                        f"org '{org.org_id}' rule '{rule.name}' apply_policy "
                        f"'{rule.apply_policy}' does not exist"
                    )

        if len(all_rule_names) != len(set(all_rule_names)):
            raise ValueError("policy_rules must have globally unique names")

        return self
