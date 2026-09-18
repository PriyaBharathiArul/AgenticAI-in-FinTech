# Agentic AI in FinTech

Comparing **Baseline**, **Single-Agent**, and **Multi-Agent** architectures for financial question answering. Built with OpenAI function calling, yfinance, and a local stock database.

## Architecture Overview

### 1. Baseline
One LLM call with no tools — answers from training data alone. Serves as the control group.

<!-- Add your screenshot: ![Baseline](docs/architecture_baseline.png) -->

### 2. Single Agent
One LLM with access to all 7 tools. Loops up to 10 rounds of think → call tool → observe → repeat.

<!-- Add your screenshot: ![Single Agent](docs/architecture_single_agent.png) -->

### 3. Multi-Agent (Parallel Specialists + Aggregator)
Three specialist agents run in parallel, each with a narrow tool set. An Aggregator merges their outputs into one final answer.

<!-- Add your screenshot: ![Multi-Agent](docs/architecture_multi_agent.png) -->

| Component | Role | Tools |
|---|---|---|
| **Market Agent** | Price performance, sector lookup, market status | `get_price_performance`, `get_tickers_by_sector`, `get_market_status`, `get_top_gainers_losers` |
| **Fundamentals Agent** | P/E ratio, EPS, market cap, 52-week range | `get_company_overview`, `query_local_db`, `get_tickers_by_sector` |
| **Sentiment Agent** | News headlines and sentiment scores | `get_news_sentiment`, `query_local_db`, `get_tickers_by_sector` |
| **Aggregator** | Merges specialist answers (no tools) | — |

## The 7 Tools

| Tool | Description | Data Source |
|---|---|---|
| `get_tickers_by_sector(sector)` | Look up companies by sector or industry | Local SQLite DB |
| `get_price_performance(tickers, period)` | Price change over time (1mo, 3mo, 6mo, ytd, 1y) | yfinance |
| `get_company_overview(ticker)` | Fundamentals: P/E, EPS, market cap, 52-week range | Alpha Vantage / yfinance fallback |
| `get_market_status()` | Whether US, UK, Japan markets are open or closed | System clock + timezone logic |
| `get_top_gainers_losers()` | Today's top movers across the market | Yahoo Finance scrape / random fallback |
| `get_news_sentiment(ticker, limit)` | Recent headlines with sentiment labels | yfinance news + random sentiment |
| `query_local_db(sql)` | Run read-only SQL against the stock database | Local SQLite DB |

## Evaluation Results

15 benchmark questions across three difficulty tiers, evaluated by an LLM-as-judge scorer (0–3 scale).

### GPT-4o-mini

| Architecture | Easy | Medium | Hard | Overall | Hallucinations |
|---|---|---|---|---|---|
| Baseline | 26.7% | 46.7% | 46.7% | 40.0% | 3 |
| Single Agent | 46.7% | 53.3% | 20.0% | 40.0% | 9 |
| **Multi-Agent** | **66.7%** | 46.7% | 33.3% | **48.9%** | 4 |

### GPT-4o

| Architecture | Easy | Medium | Hard | Overall | Hallucinations |
|---|---|---|---|---|---|
| Baseline | 13.3% | 33.3% | 33.3% | 26.7% | 3 |
| **Single Agent** | **86.7%** | 53.3% | 26.7% | **55.6%** | 6 |
| Multi-Agent | 66.7% | **60.0%** | 33.3% | 53.3% | **2** |

Full results in [`evaluation/`](evaluation/) and the detailed analysis in [`evaluation/EVALUATION_REPORT.md`](evaluation/EVALUATION_REPORT.md).

## Project Structure

```
├── app.py                     # Streamlit chat UI
├── config.py                  # Shared constants, API client setup
├── agents/
│   ├── base.py                # AgentResult, core agent loop
│   ├── baseline.py            # Baseline (no tools)
│   ├── single_agent.py        # Single agent (all 7 tools)
│   └── multi_agent.py         # 3 specialists + aggregator
├── tools/
│   ├── database.py            # SQLite: create DB, query, sector lookup
│   ├── market.py              # Price performance, market status, top movers
│   ├── fundamentals.py        # Company overview (Alpha Vantage + yfinance)
│   ├── sentiment.py           # News sentiment
│   └── schemas.py             # OpenAI function-calling schemas
├── evaluation/
│   ├── benchmark.py           # 15 benchmark questions + evaluation runner
│   ├── evaluator.py           # LLM-as-judge scorer
│   ├── results_gpt4o_mini.xlsx
│   ├── results_gpt4o.xlsx
│   └── EVALUATION_REPORT.md
├── data/
│   └── sp500_companies.csv    # Sample S&P 500 dataset (30 companies)
└── docs/
    └── architectures.html     # Interactive architecture diagrams
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/PriyaBharathiArul/Agentic-AI-in-FinTech.git
cd Agentic-AI-in-FinTech
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
cp .env.example .env
# Edit .env with your keys:
#   OPENAI_API_KEY=sk-...
#   ALPHAVANTAGE_API_KEY=...  (optional)
```

### 3. Build the stock database

A sample CSV with 30 companies is included in `data/`. For the full S&P 500 dataset, download from [Kaggle](https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks) and place it in `data/`.

```bash
python -c "from tools import create_local_database; create_local_database()"
```

### 4. Run the Streamlit app

```bash
streamlit run app.py
```

### 5. Run the benchmark evaluation (optional)

```bash
python -c "
from evaluation.benchmark import run_full_evaluation
run_full_evaluation('evaluation/results.xlsx')
"
```

## Tech Stack

- **LLM**: OpenAI GPT-4o / GPT-4o-mini with function calling
- **Data**: yfinance, Alpha Vantage API, SQLite
- **UI**: Streamlit
- **Evaluation**: LLM-as-judge (GPT-4o-mini)
