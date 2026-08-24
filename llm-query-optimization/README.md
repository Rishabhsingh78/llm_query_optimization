# LLM Query Optimization

## Overview

This project optimizes a customer business-data query system that initially sent the entire tenant database to an LLM for every question.

### Goals

- 💰 Cheaper
- ⚡ Faster
- ✅ More accurate
- 🔒 Financially safe
- 🏢 Tenant-isolated
- 🔄 Resistant to stale cached financial data

The work was completed in two optimization levels followed by Level 3 correctness and production-design safeguards.

---

## Level 1 — Baseline

The original implementation sent a large amount of tenant data to the LLM and allowed the model to perform reasoning and arithmetic.

### Baseline Result

> **Question:** What is the outstanding amount for Sharma Traders?
>
> **Ground truth:** ₹2,790,342

The baseline system produced an **incorrect** financial answer.

### Baseline Performance

| Metric             | Baseline     |
|--------------------|--------------|
| Total latency      | 324.44 sec   |
| LLM latency        | 324.35 sec   |
| Prompt tokens      | 224,420      |
| Completion tokens  | 32,768       |
| Total tokens       | 257,188      |
| Accuracy           | ❌ Incorrect  |
| Cost               | $0           |

> **Note:** The benchmark used a free model, so the reported monetary cost was $0.

### Problems

- Very large LLM context
- High token consumption
- Very high latency
- LLM responsible for financial calculations
- Incorrect financial result

---

## Level 2 — Make It Cheap and Fast

### 1. Targeted Database Retrieval

Instead of sending the entire tenant database to the LLM, the system identifies the customer and retrieves only the required data.

**Before**
```
User Question
      ↓
Entire Tenant Database
      ↓
Large LLM Prompt
      ↓
LLM
```

**After**
```
User Question
      ↓
Intent Detection
      ↓
Customer Extraction
      ↓
Targeted Database Query
      ↓
Only Required Data
```

This avoids sending unnecessary orders, invoices, payments and messages to the LLM.

---

### 2. Deterministic Financial Calculations

Financial calculations are performed by the application/database layer instead of relying on the LLM.

```
Outstanding = Invoice Total - Payment Total
```

**Example — Sharma Traders:**

| Item             | Amount         |
|------------------|----------------|
| Invoice Total    | ₹16,751,325    |
| Payment Total    | ₹13,960,983    |
| **Outstanding**  | **₹2,790,342** |

> ⚠️ The LLM is **not** the source of truth for financial numbers.

---

### 3. Intent-Based Routing

The system detects common deterministic intents before deciding whether an LLM is required.

**Supported deterministic queries:**
- Outstanding amount
- Total invoice amount
- Total payment amount
- Order count
- Cancelled order count
- Pending order count
- Processing order count

These queries are answered directly from the database. Semantic questions are classified as *complex* and use the LLM path only when reasoning is actually required.

**Routing flow:**

```
                     Question
                        ↓
                  Intent Router
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
       Deterministic            Complex
             ↓                     ↓
         Database                  LLM
             ↓                     ↓
    Application Logic          Validation
             ↓                     ↓
             └──────────┬──────────┘
                        ↓
                     Answer
```

This avoids unnecessary LLM calls for simple database questions.

---

### 4. Redis Caching

Customer summaries are cached using Redis.

- **Cache key:** `customer_summary:{tenant_id}:{customer_name}`
- **TTL:** 5 minutes

The cache service supports:
- Cache lookup
- Cache write
- Explicit invalidation

This reduces repeated database work for frequently requested customer summaries.

---

### Level 2 Benchmark Results

The optimized benchmark contains 14 representative queries.

**Result: ✅ 14 / 14 successful**

#### Optimized Performance

| Metric               | Result          |
|----------------------|-----------------|
| Total client latency | ~70.6 ms        |
| Average latency      | ~5.04 ms/query  |
| Slowest query        | 33.6 ms         |
| LLM time             | 0               |

#### Baseline vs Optimized

| Metric            | Baseline     | Optimized       |
|-------------------|--------------|-----------------|
| Latency           | 324.44 sec   | ~70.6 ms total  |
| Prompt tokens     | 224,420      | 0               |
| Completion tokens | 32,768       | 0               |
| LLM calls         | Required     | 0               |
| Accuracy          | ❌ Incorrect  | ✅ Correct       |

The optimized benchmark reduced the measured benchmark latency by approximately **99.98%**.

> **Note:** Because the benchmark used a free model, both runs reported $0 monetary cost. Therefore, a production dollar-cost saving is not claimed from this benchmark.
>
> The measurable improvement is the **elimination of LLM calls and token consumption** for the deterministic benchmark queries.

---

## Level 3 — Correctness and Production Safeguards

### 1. Correctness Floor

Financial numbers must not depend on LLM arithmetic. The system calculates financial values using database/application logic.

```
Invoice Data
     ↓
Database Aggregation
     ↓
┌──────────────────┐
│ Invoice Total    │
│ Payment Total    │
└────────┬─────────┘
         ↓
 Application Logic
         ↓
    Outstanding
```

```python
outstanding = invoice_total - payment_total
```

The LLM can **explain** the result, but it is **not responsible** for generating the authoritative financial value.

A financial validation layer is also used for the LLM path to ensure financial values remain consistent with authoritative data.

**Correctness boundary:**

```
Database
   ↓
Authoritative Values
   ↓
Application Calculation
   ↓
Optional LLM Explanation
   ↓
Validation
   ↓
Response
```

> ⚠️ The LLM is **not** the source of financial truth.

---

### 2. Routing Under Uncertainty

The router classifies the question before deciding whether an LLM is required.

```
Question
   ↓
Intent Router
   ↓
┌───────────────────┬──────────────────┐
↓                   ↓
Deterministic       Complex
↓                   ↓
Database            LLM
↓                   ↓
Application         Validation
Logic               ↓
└──────────┬────────┘
           ↓
        Response
```

For financial questions, even if the LLM path is used, **authoritative financial values still come from the database/application layer**.

If required information is unavailable, the system **abstains** instead of inventing an answer.

---

### 3. Cache Invalidation

Caching financial data introduces a stale-data risk.

**Example:**

| State                | Value      |
|----------------------|------------|
| Cached outstanding   | ₹4,20,000  |
| New payment arrives  | ₹50,000    |
| Correct outstanding  | ₹3,70,000  |

Without invalidation, the system could continue returning the stale cached value.

> ⚠️ **TTL alone is not sufficient for financial correctness.**

**Correct invalidation flow:**

```
Invoice/Payment Mutation
          ↓
     DB Transaction
          ↓
      COMMIT SUCCESS
          ↓
Invalidate Customer Cache
          ↓
       Next Read
          ↓
      Fresh DB Data
          ↓
       Cache Result
```

The cache invalidation function is:

```python
invalidate_customer_summary_cache(
    tenant_id,
    customer_name,
)
```

> **Note:** The current application does not contain an invoice/payment mutation endpoint, so the write-side invalidation is treated as an explicit production contract.

#### Cache Invalidation Test

The cache behavior was independently verified:

```
CACHE SET
    ↓
CACHE HIT
    ↓
INVALIDATE
    ↓
CACHE MISS
```

**Test result:**

```
BEFORE: {'outstanding': 420000}
AFTER:  None
```

---

### 4. Multi-Tenant Economics

A single tenant should not be able to consume the entire system's resources. The implementation provides per-tenant usage limits.

**Limits:**

| Resource                     | Limit          |
|------------------------------|----------------|
| Maximum requests             | 400 / hour     |
| Maximum LLM requests         | 100 / hour     |
| Maximum estimated LLM tokens | 100,000 / hour |

Usage is tracked independently for each tenant.

**Request Limit Test:**
```
400 requests  → Allowed
401 requests  → TenantLimitExceeded
```

**LLM Request Limit Test:**
```
100 LLM requests  → Allowed
101 LLM requests  → TenantLimitExceeded
```

**Token Budget Test:**
```
100 LLM requests × 1,000 estimated tokens = 100,000 tokens
→ Next request rejected after reaching the configured token budget
```

> **Note:** The current limiter uses in-memory state. For a production multi-instance deployment, **Redis-based atomic counters** should be used so that tenant limits are shared across all application instances.

---

### 5. Regression Safety

Optimization can introduce regressions. Changes to routing, prompts, query handlers, or financial logic can affect existing behavior.

**Benchmark coverage:**
- Customer data
- Intent routing
- Query handlers
- Financial calculations
- Optimized database queries
- Customer summaries
- Comparisons
- Business-risk questions

The benchmark was rerun after the Level 3 changes.

**Result: ✅ 14 / 14 successful**

The tested financial and operational results remained correct.

These benchmarks should run in CI whenever changes are made to:
- Routing logic
- Prompts
- Query handlers
- Financial calculations
- Cache behavior

---

### 6. Knowing When to Shut Up

Sometimes the safest answer is:

> *"The provided data does not contain enough information to answer that."*

The LLM is instructed to:
- Use only the provided data
- Not invent facts
- Not invent financial values
- Avoid unsupported recommendations
- State when the provided data is insufficient

**Intended behavior:**

```
Required data exists          Required data missing
       ↓                              ↓
     Answer                        Abstain
```

This is particularly important for financial and business-risk questions.

> The system should **prefer an explicit limitation** over a confident hallucination.

---

## Architecture

```
                         ┌─────────────────┐
                         │  User Question  │
                         └────────┬────────┘
                                  ↓
                         ┌─────────────────┐
                         │  Intent Router  │
                         └────────┬────────┘
                                  ↓
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
           ┌─────────────────┐         ┌─────────────────┐
           │  Deterministic  │         │     Complex     │
           │     Query       │         │     Query       │
           └────────┬────────┘         └────────┬────────┘
                    ↓                           ↓
           ┌─────────────────┐         ┌─────────────────┐
           │ Targeted DB     │         │ Customer Data   │
           │ Aggregation     │         │ Retrieval       │
           └────────┬────────┘         └────────┬────────┘
                    ↓                           ↓
           ┌─────────────────┐         ┌─────────────────┐
           │ Application     │         │      LLM        │
           │ Arithmetic      │         │    Reasoning    │
           └────────┬────────┘         └────────┬────────┘
                    │                           ↓
                    │                  ┌─────────────────┐
                    │                  │    Financial    │
                    │                  │    Validation   │
                    │                  └────────┬────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ↓
                         ┌─────────────────┐
                         │    Response     │
                         └─────────────────┘


              ┌────────────────────────────────┐
              │             Redis              │
              │                                │
              │  Customer Summary Cache        │
              │  Tenant Usage Limiting         │
              └────────────────────────────────┘
```

---

## Trade-offs

| Optimization               | Benefit                          | Trade-off                                    |
|----------------------------|----------------------------------|----------------------------------------------|
| Targeted DB retrieval      | Less data and faster processing  | Requires reliable customer/intent extraction |
| Deterministic calculations | Financial correctness            | More application logic                       |
| Intent routing             | Avoids unnecessary LLM calls     | Router can misclassify questions             |
| LLM for complex queries    | Handles semantic reasoning       | Higher latency and potential cost            |
| Redis caching              | Faster repeated queries          | Requires cache invalidation                  |
| Tenant limits              | Prevents noisy-neighbor problems | Requests can be rejected at quota            |




                    User Question
                         │
                         ▼
                  Intent Router
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    Deterministic    Analytics       Unsupported
          │              │              │
          ▼              ▼              ▼
       Database      DB + Formatter   Abstain
          │              │
          └───────┬──────┘
                  │
                  ▼
          Genuine Complex Query
                  │
                  ▼
                 LLM
                  │
                  ▼
        Financial Validation
                  │
          ┌───────┴────────┐
          ▼                ▼
       Valid             Invalid
          │                │
          ▼                ▼
       Answer           Safe Abstain


---

## Final Benchmark — Baseline vs Optimized

> Results generated by running the full 26-question benchmark suite against both the baseline and optimized implementations.

| Metric             | Baseline  | Optimized       |
|--------------------|----------:|----------------:|
| Accuracy           | 33.33%    | **100.00%**     |
| Average latency    | 0.8577s   | **0.7887s**     |
| P50 latency        | 0.0050s   | **0.0044s**     |
| P95 latency        | 3.5650s   | 5.1668s         |
| LLM calls          | N/A       | **4**           |
| Prompt tokens      | N/A       | 962             |
| Completion tokens  | N/A       | 1,584           |
| Total tokens       | N/A       | 2,546           |
| Total LLM cost     | N/A       | **$0.020932**   |

> **Note:** P95 latency is higher in the optimized run because 4 genuine LLM-fallback queries were included. The P50 (median) latency improved, confirming that the vast majority of queries are faster.

---

### Final Optimization Result

| Metric | Result |
|---|---|
| Benchmark queries correct | **26 / 26** |
| Benchmark accuracy | **100%** |
| Automated tests passed | **30 / 30** |
| LLM calls out of 26 queries | **4** |
| Queries handled without LLM | **22 / 26 (84.6%)** |
| Total LLM tokens | **2,546** |
| Total LLM cost | **$0.020932** |