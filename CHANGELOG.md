# Changelog

## [0.4.1](https://github.com/fhswf/soccer-agent/compare/soccer-agent-v0.4.0...soccer-agent-v0.4.1) (2026-05-23)


### Bug Fixes

* disable DNS rebinding protection and bump project version to 0.4.0 ([4bc09ca](https://github.com/fhswf/soccer-agent/commit/4bc09ca9c18557034214bbeaaa419e95bde64de8))

## [0.4.0](https://github.com/fhswf/soccer-agent/compare/soccer-agent-v0.3.0...soccer-agent-v0.4.0) (2026-05-23)


### Features

* add ROOT_PATH configuration to MCP server for deployment behind reverse proxy ([161c9cb](https://github.com/fhswf/soccer-agent/commit/161c9cb41a29cf96315116ac31700d59a110dd07))
* integrate FastMCP into FastAPI server and update ingress routes to support native MCP endpoints ([54917d1](https://github.com/fhswf/soccer-agent/commit/54917d1693b555e4a1fa4368dc779d4ea2aac5fe))

## [0.3.0](https://github.com/fhswf/soccer-agent/compare/soccer-agent-v0.2.0...soccer-agent-v0.3.0) (2026-05-23)


### Features

* add data-pipeline CI workflow, implement REST API endpoints in mcp-server, and update K8s configuration and release management ([82f348f](https://github.com/fhswf/soccer-agent/commit/82f348fd73d668dbe46bbd56da547a47f6d1fd32))
* add opponent probability tracking to tournament simulation and display in CLI ([0256bda](https://github.com/fhswf/soccer-agent/commit/0256bda5a5a12d0b7c7a23856fce9d6ee23b0c25))
* add Traefik middleware to strip /mcp prefix from ingress requests ([3aa4196](https://github.com/fhswf/soccer-agent/commit/3aa4196eec1e3ca199eb5162fa791315f3c8eff0))
* implement Monte Carlo tournament simulation CLI command, add configurable top-N ranking, and correct ELO data mapping for Scotland ([aa1e2a8](https://github.com/fhswf/soccer-agent/commit/aa1e2a85f2f732b22fe657df865ef6a0b6989a89))

## [0.2.0](https://github.com/fhswf/soccer-agent/compare/soccer-agent-v0.1.0...soccer-agent-v0.2.0) (2026-05-22)


### Features

* implement soccer agent infrastructure with K8s manifests, MCP integration, and workshop notebooks ([bac5e29](https://github.com/fhswf/soccer-agent/commit/bac5e294fb65105a17b339ea834dadc807d9716b))
