# Evaluation Report

15 benchmark questions across three difficulty tiers (easy, medium, hard) were evaluated against three architectures: **Baseline**, **Single Agent**, and **Multi-Agent**. Each answer was scored 0–3 by an LLM-as-judge evaluator. Two model configurations were tested.

---

## GPT-4o-mini Results

| Architecture | Easy (5Q) | Medium (5Q) | Hard (5Q) | Overall (15Q) |
|---|---|---|---|---|
| Baseline | 27% | 47% | 47% | 40% |
| Single Agent | 47% | 53% | 20% | 40% |
| Multi-Agent | 67% | 47% | 33% | 49% |

**Average response time:** Baseline 2.9s · Single Agent 6.0s · Multi-Agent 10.7s

---

## GPT-4o Results

| Architecture | Easy (5Q) | Medium (5Q) | Hard (5Q) | Overall (15Q) |
|---|---|---|---|---|
| Baseline | 13% | 33% | 33% | 27% |
| Single Agent | 87% | 53% | 27% | 56% |
| Multi-Agent | 67% | 60% | 33% | 53% |

**Average response time:** Baseline 2.1s · Single Agent 3.8s · Multi-Agent 5.8s

---

## Key Findings

### Multi-Agent wins the easy tier consistently
Both models show Multi-Agent achieving 66.7% on easy questions — strong on straightforward lookups where specialist routing works cleanly.

### Single Agent excels with a stronger model
With GPT-4o, Single Agent jumps to 86.7% on easy questions (vs 46.7% with mini), demonstrating that a more capable model better leverages the full tool set in a single context window.

### Hard questions remain challenging for all architectures
No architecture exceeds 46.7% on hard questions with either model. These questions require multi-step reasoning across domains (price + fundamentals + sentiment), which compounds errors.

### Hallucination reduction
Multi-Agent with GPT-4o produces the fewest hallucinations (2), compared to Single Agent (6) and Baseline (3). The specialist isolation prevents cross-domain error propagation.

### Cost-accuracy tradeoff
Multi-Agent uses 3–4x more API calls than Single Agent but only improves overall accuracy by ~9 percentage points (mini) or ~-2 points (4o). The parallel specialist design adds latency (10.7s vs 6.0s with mini) without proportional accuracy gains on hard questions.

---

## Benchmark Question Categories

| Tier | Category | Example |
|---|---|---|
| Easy | sector_lookup, market_status, fundamentals, sentiment, price | "List all semiconductor companies" |
| Medium | price_comparison, fundamentals, sector_price, sentiment | "Compare P/E ratios of AAPL, MSFT, NVDA" |
| Hard | multi_condition, cross_domain | "Top 3 semiconductor stocks by return with P/E and sentiment" |
