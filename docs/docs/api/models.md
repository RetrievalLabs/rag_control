---
title: Models API Reference
description: Core data models used throughout the SDK
---

# Models API Reference

Core data models used in the RAGControl SDK.

## UserContext

User context passed to engine methods. Provides user and organization information for governance and policy evaluation.

```python
from rag_control.models import UserContext

context = UserContext(
    user_id="user-123",
    org_id="acme-corp",
)
```

**Fields:**
- `user_id: str` - User identifier (required)
- `org_id: str` - Organization identifier (required)
- `attributes: dict[str, Any]` - Additional metadata (optional)

**Note:** Extra fields are allowed and passed through to policy rules and governance evaluations.

### Example with Custom Fields

```python
context = UserContext(
    user_id="user-123",
    org_id="acme-corp",
    attributes={
        "tier": "premium",
        "department": "finance",
        "role": "analyst",
    },
)
```

These custom fields can be referenced in policy rules and governance conditions.

## See Also

- [Engine API](/api/engine)
- [Policy, Governance & Filters API](/api/policy-gov-config)
- [Exceptions API](/api/exceptions)
