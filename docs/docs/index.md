---
slug: /
title: rag_control Documentation
description: Runtime Governance, Security, and Execution Control for RAG Systems
---

:::info Version
You are viewing **v0.1.1** documentation. This is the current stable release.
:::

# Welcome to RAG Control 

**rag_control** is an enterprise-grade governance, security, execution control, and observability layer for Retrieval-Augmented Generation (RAG) systems.

## What is rag_control?

RAG systems combine powerful retrieval and generation capabilities but introduce governance, security, and compliance challenges. rag_control addresses these with:

- **Policy-Based Generation**: Define and enforce generation policies (temperature, output length, citation requirements, external knowledge restrictions)
- **Runtime Enforcement**: Validate responses against policies before returning them to users
- **Governance & Security**: Apply organization-level rules, role-based access control, and data classification filters
- **Comprehensive Audit Logging**: Track all requests, decisions, and denials for compliance
- **Distributed Tracing**: Understand execution flow and identify performance bottlenecks
- **Metrics & Observability**: 18+ metrics covering throughput, latency, quality, costs, and errors

## Key Features

### 🛡️ Policy Enforcement
- Define multiple policies with different strictness levels
- Control temperature, max output tokens, reasoning depth
- Enforce citation requirements and validation
- Prevent external knowledge generation
- Apply context-aware fallback strategies

### 🔐 Governance & Security
- Organization-level access control
- Retrieval filtering by data classification and metadata
- User context validation
- Policy resolution based on org rules and data sensitivity

### 📊 Observability
- **Audit Logging**: Full request/response lifecycle tracking
- **Distributed Tracing**: OpenTelemetry integration for flow analysis
- **Metrics**: Token usage, latency, error rates, policy decisions

### 🚀 Production Ready
- Exception-swallowing pattern ensures governance failures never break request flow
- Comprehensive error handling with custom exception types
- Type-safe with mypy strict mode compliance
- 100% code coverage with extensive test suite

## Quick Links

- [Installation & Quick Start](/getting-started/quick-start)
- [Core Concepts](/concepts/overview)
- [API Reference](/api/engine)
- [Observability](/observability/audit-logging)

## Support & Community

- 📚 [Read the Documentation](/getting-started/installation)
- 🐛 [Report Issues](https://github.com/RetrievalLabs/rag_control/issues)
- 💬 [GitHub Discussions](https://github.com/RetrievalLabs/rag_control/discussions)
- 🏢 [RetrievalLabs.ai](https://retrievallabs.ai)

## Support the Project

If you find rag_control useful, please consider **[⭐ starring the repository on GitHub](https://github.com/RetrievalLabs/rag_control)** to show your support! Your star helps us reach more developers and organizations building secure RAG systems.

---

**Built by [RetrievalLabs](https://retrievallabs.ai)** — Enterprise AI Governance and Security
