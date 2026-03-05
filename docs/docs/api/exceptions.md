---
title: Exceptions API Reference
description: Public API exceptions provided by the SDK
---

# Exceptions API Reference

The rag_control SDK provides a comprehensive set of exceptions for handling various error scenarios. All exceptions can be imported from `rag_control.exceptions`.

## Base Exception

### `RagControlError`

Base exception for all rag_control SDK errors. Inherit from or catch this exception to handle any rag_control error in a general way.

---

## Adapter Exceptions

Adapter exceptions are raised when there are failures in integrating with external services.

### `AdapterError`

Base exception for all adapter integration failures.

### `LLMAdapterError`

Raised when the LLM adapter fails (e.g., service unavailable, invalid credentials, response parsing issues).

### `QueryEmbeddingAdapterError`

Raised when the query embedding adapter fails (e.g., service unavailable, invalid query, dimension mismatches).

### `VectorStoreAdapterError`

Raised when the vector store adapter fails (e.g., connection issues, invalid parameters, storage failures).

---

## Governance Exceptions

Governance exceptions are raised when governance policies are violated or missing.

### `GovernanceOrgNotFoundError`

Raised when no governance configuration exists for the requested organization.

**Attributes:**
- `user_context`: The `UserContext` that triggered the error

### `GovernancePolicyDeniedError`

Raised when a governance deny rule matches and blocks policy resolution.

**Attributes:**
- `user_context`: The `UserContext` that triggered the error
- `rule_name`: The name of the deny rule that matched

### `GovernanceUserContextOrgIDRequiredError`

Raised when `user_context.org_id` is required but not provided.

### `GovernanceRegistryOrgNotFoundError`

Raised when an org_id cannot be found in the governance registry.

**Attributes:**
- `org_id`: The organization ID that was not found

---

## Enforcement Exceptions

Enforcement exceptions are raised when generated responses violate policy checks.

### `EnforcementPolicyViolationError`

Raised when a generated response violates enforcement policy checks.

**Attributes:**
- `policy_name`: The name of the enforcement policy that failed
- `violations`: A list of violation messages describing what failed

---

## Embedding Model Exceptions

Embedding model exceptions are raised for issues with embedding model configuration and validation.

### `EmbeddingModelTypeError`

Raised when an embedding model identifier is not a string.

### `EmbeddingModelValidationError`

Raised when an embedding model identifier is empty or invalid.

### `EmbeddingModelMismatchError`

Raised when query and vector store embedding models do not match.

---

## Control Plane Config Exceptions

### `ControlPlaneConfigValidationError`

Raised when control plane configuration is invalid or incomplete.

---

## Exception Hierarchy

```
Exception
└── RagControlError
    ├── AdapterError
    │   ├── LLMAdapterError
    │   ├── QueryEmbeddingAdapterError
    │   └── VectorStoreAdapterError
    ├── GovernanceOrgNotFoundError
    ├── GovernancePolicyDeniedError
    ├── GovernanceUserContextOrgIDRequiredError
    ├── GovernanceRegistryOrgNotFoundError
    ├── EnforcementPolicyViolationError
    ├── EmbeddingModelTypeError (also inherits from TypeError)
    ├── EmbeddingModelValidationError (also inherits from ValueError)
    ├── EmbeddingModelMismatchError (also inherits from ValueError)
    └── ControlPlaneConfigValidationError (also inherits from ValueError)
```

---

## Importing Exceptions

All public exceptions can be imported from `rag_control.exceptions`:

```python
from rag_control.exceptions import (
    RagControlError,
    AdapterError,
    LLMAdapterError,
    QueryEmbeddingAdapterError,
    VectorStoreAdapterError,
    GovernanceOrgNotFoundError,
    GovernancePolicyDeniedError,
    GovernanceUserContextOrgIDRequiredError,
    GovernanceRegistryOrgNotFoundError,
    EnforcementPolicyViolationError,
    EmbeddingModelTypeError,
    EmbeddingModelValidationError,
    EmbeddingModelMismatchError,
    ControlPlaneConfigValidationError,
)
```

Adapter exceptions can also be imported from the adapter submodule:

```python
from rag_control.adapters import (
    AdapterError,
    LLMAdapterError,
    QueryEmbeddingAdapterError,
    VectorStoreAdapterError,
)
```
