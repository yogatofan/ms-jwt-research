# Microservices JWT Research

Experimental implementation for the paper:
**"Enhancing Microservices API Security using JWT and Rate Limiting: A Performance Evaluation"**

## Project Structure
```
ms-jwt-research/
├── gateway/          # API Gateway (port 3000)
├── user-service/     # Authentication service (port 3001)
├── product-service/  # Product service (port 3002)
├── order-service/    # Order service (port 3003)
├── load-testing/     # k6 test scripts & results
├── visualisasi/      # Python visualization scripts
└── notes/            # Research notes
```

## Requirements
- Node.js v18+
- k6 v1.6+
- Python 3.x + matplotlib

## Running the project
```bash
# With security
npm run start:with-security

# Without security (baseline)
npm run start:no-security
```

## Load Testing
```bash
cd load-testing
k6 run normal-traffic.js
k6 run burst-traffic.js
```