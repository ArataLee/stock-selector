# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Backend
cd backend && pip install -e ".[dev]"    # Install deps (first time)
cd backend && pytest                      # Run all tests (44 tests, asyncio_mode=auto)
cd backend && pytest tests/path/test.py -v   # Run single test file
cd backend && stock-selector server start --reload   # Dev server at :8000

# Frontend
cd frontend && npm install                # Install deps (first time)
cd frontend && npm run dev                # Dev server at :5173 (proxies /api → :8000)
cd frontend && npx tsc --noEmit           # Type check
```

## Architecture

DDD layered Python backend + React/TypeScript frontend. Python files use **PascalCase**.

**Bootstrap DI**: `bootstrap.py` loads `config/default.yaml`, wires all components into `AppContext`. Config is flat — LLM providers and data source tokens both go in `default.yaml` (single-user tool, no layering needed).

**Data flow**: `ScreenStockUseCase` orchestrates Market(quotes+financials) → LLM(scoring). Returns `ScreeningOutcome` (results, errors, skipped) — not plain list. `DiscoveryService` handles "推荐3只消费股"-style NL queries by using LLM to expand broad terms (消费→食品,白酒,家电,零售) into stock-name-matchable keywords, then sourcing candidates via THS concept names → Sina spot data, scoring all candidates, returning top N.

**Multi-source degradation**: Data adapters have priority chains. Sina is primary for quotes (`stock_zh_a_spot`) because East Money APIs (`stock_zh_a_spot_em`, `stock_board_*_cons_em`) aggressively rate-limit. For financials: 同花顺 → 新浪.

**Repository method names are disambiguated**: `QuoteRepository.fetch_quotes()`, `FinancialRepository.fetch_financials()` — they were both named `fetch_batch` in the original design, but Python would shadow one.

## Conventions

- `StockCode.parse("600001")` auto-infers market from 6-digit prefix. Accepts both `600001` and `600001.SH`.
- Stock names in Sina data use format `sh600519`, not pure digits — extract `raw[-6:]` for the digit part.
- Financial data from 同花顺 is in ascending date order — use `df.iloc[::-1].head(N)` to get most recent periods.
- Prompt templates in `llm/domain/Prompt.py` have JSON braces escaped as `{{` `}}` because of Python `.format()`.
- All LLM scoring output must include `建议仅供参考，不构成任何投资建议。` at the end.

## Gotchas

- East Money board APIs (`stock_board_concept_cons_em`, `stock_board_industry_cons_em`) return `ConnectionError` when rate-limited. Test individual AKShare function availability before assuming they work.
- `--reload` does not detect creation of new files — manually restart the server after `git checkout` or file creation.
- Stock names do not contain full sector names like "半导体" or "消费" — they contain fragments like "半导", "食品". The `DiscoveryService` uses ≥2-char fuzzy matching as fallback.
