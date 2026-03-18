# Providers

## Overview

현재 프로젝트는 문서, 시장 데이터, 검증, 거시 데이터에 대해 아래 provider 구성을 사용한다.

## Provider Matrix

| domain | provider | auth env | current role | runtime status |
| --- | --- | --- | --- | --- |
| documents | SEC EDGAR | `SEC_API_USER_AGENT` | primary document source | active |
| market | FMP | `FMP_API_KEY` | primary market source where endpoint is available | active |
| market | Finnhub | `FINNHUB_API_KEY` | fallback and verification for quote/profile/peers | active |
| market | yfinance | none | fallback for blocked or unavailable endpoints | active |
| macro | FRED | `FRED_API_KEY` | macro gateway | active |

## Field Mapping

### SEC EDGAR

| internal field | source field or derivation |
| --- | --- |
| `document_id` | `CIK:accession_number` |
| `document_type` | Atom entry category term |
| `published_at` | filing date from Atom summary |
| `title` | Atom entry title |
| `uri` | filing index or document URL |
| `text` | fetched filing document text |

### FMP

| internal field | endpoint |
| --- | --- |
| `snapshot.close` | `profile.price` |
| `snapshot.volume` | `profile.volAvg` |
| `currency` | `profile.currency` |
| `shares_outstanding` | `shares-float.outstandingShares` |
| `float_shares` | `shares-float.floatShares` |
| `free_float` | `shares-float.freeFloat` |
| `peers` | `stock-peers` rows |

### Finnhub

| internal field | endpoint |
| --- | --- |
| `verification.close` | `quote.c` |
| `verification.open` | `quote.o` |
| `verification.high` | `quote.h` |
| `verification.low` | `quote.l` |
| `profile` | `stock/profile2` |
| `peer verification` | `stock/peers` |
| `basic_financials` | `stock/metric?metric=all` |

### yfinance

| internal field | source |
| --- | --- |
| `price_history.rows` | `Ticker.history()` |
| `fundamentals.income_statement` | `Ticker.quarterly_income_stmt` or `income_stmt` |
| `fundamentals.balance_sheet` | `Ticker.quarterly_balance_sheet` or `balance_sheet` |
| `fundamentals.cashflow` | `Ticker.quarterly_cashflow` or `cashflow` |
| `shares_outstanding` | `Ticker.info.sharesOutstanding` |

### FRED

| internal field | endpoint |
| --- | --- |
| `seriess` | `series/search` |
| `observations` | `series/observations` |
| `latest_observation` | latest row from `series/observations` |
| `macro snapshot` | repeated `latest_observation` calls |

## Current Fallback Rules

- `get_price_snapshot`: FMP -> Finnhub -> yfinance
- `get_price_history`: FMP -> yfinance
- `get_fundamentals`: FMP -> yfinance, then Finnhub verification attached
- `get_share_count`: FMP -> yfinance
- `get_peer_set`: FMP -> Finnhub -> yfinance, then Finnhub verification attached
- `docs_gateway`: SEC only
- `macro_data_gateway`: FRED only

## Notes

- 현재 FMP plan에서는 일부 endpoint가 `402 Payment Required`를 반환한다.
- 그 경우 market gateway는 자동으로 fallback provider를 사용한다.
- Finnhub는 fallback뿐 아니라 quote/profile/peers 검증 데이터도 제공한다.
- FRED는 macro gateway로 분리되어 있으며, key가 유효해야 live 호출이 가능하다.
