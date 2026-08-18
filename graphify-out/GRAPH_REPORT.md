# Graph Report - ms-jwt-research  (2026-08-18)

## Corpus Check
- 51 files · ~23,233 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 250 nodes · 288 edges · 29 communities (23 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ba332765`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- env-report.py
- scripts
- gateway/package.json
- order-service/package.json
- product-service/package.json
- user-service/package.json
- analyze.py
- order-service/src/app.js
- product-service/src/app.js
- gateway/src/app.js
- burst-traffic.js
- normal-traffic.js
- user-service/src/app.js
- run-experiment.js
- user-service/src/middleware/auth.js
- 📌 **Judul Terpilih**
- Microservices JWT Research
- run-all.sh
- rules/graphify.md
- workflows/graphify.md
- environment-spec.md
- error.md
- notes.md

## God Nodes (most connected - your core abstractions)
1. `collect_specs()` - 15 edges
2. `run()` - 11 edges
3. `main()` - 10 edges
4. `main()` - 9 edges
5. `run-all.sh script` - 9 edges
6. `Microservices JWT Research` - 8 edges
7. `📌 **Judul Terpilih**` - 6 edges
8. `scripts` - 5 edges
9. `compute_stats()` - 5 edges
10. `print_table()` - 5 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (29 total, 6 thin omitted)

### Community 0 - "env-report.py"
Cohesion: 0.12
Nodes (31): collect_specs(), detect_arch(), detect_cpu(), detect_k6(), detect_machine(), detect_node(), detect_npm(), detect_npm_package() (+23 more)

### Community 1 - "scripts"
Cohesion: 0.15
Nodes (12): concurrently, cross-env, devDependencies, concurrently, cross-env, name, scripts, install:all (+4 more)

### Community 2 - "gateway/package.json"
Cohesion: 0.09
Nodes (21): express-rate-limit, author, dependencies, dotenv, express, express-rate-limit, http-proxy-middleware, jsonwebtoken (+13 more)

### Community 3 - "order-service/package.json"
Cohesion: 0.10
Nodes (19): author, dependencies, bcryptjs, dotenv, express, jsonwebtoken, description, bcryptjs (+11 more)

### Community 4 - "product-service/package.json"
Cohesion: 0.10
Nodes (19): author, dependencies, bcryptjs, dotenv, express, jsonwebtoken, description, bcryptjs (+11 more)

### Community 5 - "user-service/package.json"
Cohesion: 0.10
Nodes (19): author, dependencies, bcryptjs, dotenv, express, jsonwebtoken, description, bcryptjs (+11 more)

### Community 6 - "analyze.py"
Cohesion: 0.16
Nodes (24): _bar_with_errbar(), compute_stats(), export_reviewer_latex_table(), extract_metrics(), fig3_normal_latency(), fig4_burst_traffic(), fig5_throughput(), fmt() (+16 more)

### Community 7 - "order-service/src/app.js"
Cohesion: 0.29
Nodes (6): app, express, orders, { verifyToken }, jwt, verifyToken()

### Community 8 - "product-service/src/app.js"
Cohesion: 0.29
Nodes (6): app, express, products, { verifyToken }, jwt, verifyToken()

### Community 9 - "gateway/src/app.js"
Cohesion: 0.29
Nodes (6): app, authLimiter, { createProxyMiddleware }, express, globalLimiter, rateLimit

### Community 10 - "burst-traffic.js"
Cohesion: 0.29
Nodes (6): blockedReqs, errorRate, loginLatency, options, productLatency, totalRequests

### Community 11 - "normal-traffic.js"
Cohesion: 0.29
Nodes (6): errorRate, loginLatency, options, orderLatency, productLatency, totalRequests

### Community 12 - "user-service/src/app.js"
Cohesion: 0.40
Nodes (4): app, express, jwt, users

### Community 13 - "run-experiment.js"
Cohesion: 0.50
Nodes (3): errorRate, latency, options

### Community 20 - "📌 **Judul Terpilih**"
Cohesion: 0.18
Nodes (10): 1. 🔧 Step-by-step implementasi, 2. 🧪 Template eksperimen & load testing, 3. 📝 Outline paper IEEE, ⚙️ **Gambaran Sistem**, 🧠 **Inti Ide Penelitian**, 📌 **Judul Terpilih**, 🎯 **Kontribusi Utama**, 🧪 **Metodologi Singkat** (+2 more)

### Community 21 - "Microservices JWT Research"
Cohesion: 0.18
Nodes (10): Environment Specification Report, Individual Load Testing (Manual), Microservices JWT Research, Project Structure, Quick Start (One-time Setup), Repeated Experiments (for Statistical Validity), Requirements, Running the Project (Manual) (+2 more)

### Community 22 - "run-all.sh"
Cohesion: 0.49
Nodes (9): log_error(), log_info(), log_ok(), log_section(), log_warn(), run-all.sh script, start_services(), stop_services() (+1 more)

## Knowledge Gaps
- **118 isolated node(s):** `name`, `version`, `description`, `main`, `test` (+113 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `name`, `version`, `description` to the rest of the system?**
  _118 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `env-report.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11553030303030302 - nodes in this community are weakly interconnected._
- **Should `gateway/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `order-service/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `product-service/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `user-service/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._