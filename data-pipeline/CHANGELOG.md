# Changelog

## [1.1.0](https://github.com/fhswf/soccer-agent/compare/data-pipeline-v1.0.1...data-pipeline-v1.1.0) (2026-05-29)


### Features

* expand news scraper to support configurable soccer domains and update CLI/K8s defaults ([1dc60fc](https://github.com/fhswf/soccer-agent/commit/1dc60fc9e10ce0ae55948a23777c41b0bb542149))
* implement incremental ChromaDB ingestion with persistent chunk-based embedding caching and remove Qdrant support. ([3402bfb](https://github.com/fhswf/soccer-agent/commit/3402bfbaf701b02e68189a8a966161cf4efaf826))

## [1.0.1](https://github.com/fhswf/soccer-agent/compare/data-pipeline-v1.0.0...data-pipeline-v1.0.1) (2026-05-28)


### Bug Fixes

* add release-please triggers to scrape_news.py and server.py ([2963f0f](https://github.com/fhswf/soccer-agent/commit/2963f0f3bf8dca73936317edea8268e2abfb1c0a))

## 1.0.0 (2026-05-28)


### Features

* implement automated official FIFA news scraping and integrate into the data pipeline and MCP server. ([069ffd3](https://github.com/fhswf/soccer-agent/commit/069ffd38c57095b6e1f83da694ccd525b78cec7b))
* implement Monte Carlo tournament simulation CLI command, add configurable top-N ranking, and correct ELO data mapping for Scotland ([aa1e2a8](https://github.com/fhswf/soccer-agent/commit/aa1e2a85f2f732b22fe657df865ef6a0b6989a89))
* increase default max_results for FIFA news scraping from 10 to 40 ([879c1be](https://github.com/fhswf/soccer-agent/commit/879c1be77fcb38f7be21fa41db21a0e05f4cdd40))
