---
title: Control Plane Config Contract
description: Formal specification of configuration structure
---

# Control Plane Config Contract

This document specifies the formal contract for rag_control configuration.

## Overview

The Config Contract defines:

- Configuration file structure
- Required and optional fields
- Validation rules
- Schema and types
- Configuration versioning

## Detailed Specification

For the complete formal specification, see:

📄 [`rag_control/spec/control_plane_config_contract.md`](https://github.com/RetrievalLabs/rag_control/blob/main/rag_control/spec/control_plane_config_contract.md)

## Quick Reference

### Top-Level Sections

```yaml
policies:
  # Policy definitions
  - name: policy_name
    generation: {...}
    enforcement: {...}
    logging: {...}

filters:
  # Filter definitions
  - name: filter_name
    condition: {...}

orgs:
  # Organization configurations
  - org_id: org_id
    default_policy: policy_name
    document_policy: {...}
    policy_rules: [...]
```

### Validation

- All policy names referenced must exist
- All filter names referenced must exist
- All policy names in rules must exist
- Condition fields must be valid paths
- Operators must be supported

## See Also

- [Configuration Guide](/getting-started/configuration)
- [Execution Contract](/specs/execution-contract)
- [GitHub Repository](https://github.com/RetrievalLabs/rag_control)
