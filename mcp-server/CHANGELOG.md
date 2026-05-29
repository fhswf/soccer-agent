# Changelog

## [0.8.1](https://github.com/fhswf/soccer-agent/compare/mcp-server-v0.8.0...mcp-server-v0.8.1) (2026-05-28)


### Bug Fixes

* add release-please triggers to scrape_news.py and server.py ([2963f0f](https://github.com/fhswf/soccer-agent/commit/2963f0f3bf8dca73936317edea8268e2abfb1c0a))

## [0.8.0](https://github.com/fhswf/soccer-agent/compare/mcp-server-v0.7.0...mcp-server-v0.8.0) (2026-05-28)


### Features

* add data-pipeline CI workflow, implement REST API endpoints in mcp-server, and update K8s configuration and release management ([82f348f](https://github.com/fhswf/soccer-agent/commit/82f348fd73d668dbe46bbd56da547a47f6d1fd32))
* add opponent probability tracking to tournament simulation and display in CLI ([0256bda](https://github.com/fhswf/soccer-agent/commit/0256bda5a5a12d0b7c7a23856fce9d6ee23b0c25))
* add ROOT_PATH configuration to MCP server for deployment behind reverse proxy ([161c9cb](https://github.com/fhswf/soccer-agent/commit/161c9cb41a29cf96315116ac31700d59a110dd07))
* fetch and display live Polymarket odds in tournament simulation ([4a8dbaa](https://github.com/fhswf/soccer-agent/commit/4a8dbaa5334bbd9f877f1034f64a3e49c5a684b1))
* implement automated official FIFA news scraping and integrate into the data pipeline and MCP server. ([069ffd3](https://github.com/fhswf/soccer-agent/commit/069ffd38c57095b6e1f83da694ccd525b78cec7b))
* implement bracket-based knockout simulation using dynamic fixture placeholders ([9cf98a4](https://github.com/fhswf/soccer-agent/commit/9cf98a443a3b52d2686e6c5ff37deea482297a48))
* implement dynamic three-way match simulation using Elo-based probabilities for win, loss, and draw outcomes ([3435b86](https://github.com/fhswf/soccer-agent/commit/3435b86d58a2a60edf6e1944d9f3f2723dee4b06))
* implement Monte Carlo tournament simulation CLI command, add configurable top-N ranking, and correct ELO data mapping for Scotland ([aa1e2a8](https://github.com/fhswf/soccer-agent/commit/aa1e2a85f2f732b22fe657df865ef6a0b6989a89))
* implement soccer agent infrastructure with K8s manifests, MCP integration, and workshop notebooks ([bac5e29](https://github.com/fhswf/soccer-agent/commit/bac5e294fb65105a17b339ea834dadc807d9716b))
* integrate FastMCP into FastAPI server and update ingress routes to support native MCP endpoints ([54917d1](https://github.com/fhswf/soccer-agent/commit/54917d1693b555e4a1fa4368dc779d4ea2aac5fe))


### Bug Fixes

* clear global fixture ELO map before rebuilding to prevent stale data accumulation ([283427f](https://github.com/fhswf/soccer-agent/commit/283427f05a7482bd50b1355bf39752618c709225))
* disable DNS rebinding protection and bump project version to 0.4.0 ([4bc09ca](https://github.com/fhswf/soccer-agent/commit/4bc09ca9c18557034214bbeaaa419e95bde64de8))
* localize tournament round names to German in simulation tool ([d450b03](https://github.com/fhswf/soccer-agent/commit/d450b0397ca0d4dd064637f756fac5d3debffc5f))
