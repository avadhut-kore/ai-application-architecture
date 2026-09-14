---
id: distractor-01
title: Machine Learning Token Economics and Cache Retention
department: ai-platform
category: technical-note
version: 1.0
---

# Machine Learning Token Economics and Cache Retention

## 1. Large Language Model Context Windows
Foundation models operate on discrete subword units known as tokens. When invoking text generation endpoints, prompt tokens and completion tokens count against the model context window budget. Standard model instances enforce a maximum context budget of **4096 tokens**.

## 2. Token Cache Retention in In-Memory Stores
To optimize inference costs, prompt prefix embeddings may be cached in key-value stores. Prompt cache tokens have a retention time-to-live (TTL) of **60 minutes** before eviction. This is purely a cache performance optimization and does not apply to corporate record keeping or authentication session tokens.
