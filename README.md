# 🌊 ProxyFlow — Async Proxy Orchestrator

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-V1.0_Ready-34D399?style=for-the-badge)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**ProxyFlow** is a high-performance, asynchronous proxy management suite designed for professional web scraping and automation. It eliminates the friction of managing proxy health by providing a self-healing pool with low-latency smart routing.

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| ⚡ **Async Engine** | Built on `asyncio`, `aiohttp`, and `aiosqlite` for non-blocking concurrent checks |
| 🔗 **Smart Routing** | `/get-proxy` always serves the fastest verified proxy in your pool |
| 🤖 **Automation Ready** | First-class support for **Playwright** and **Selenium** |
| 📦 **Local-First** | State persisted in a high-performance local SQLite database |
| 📤 **Export Support** | Download your active proxy pool at any time via `/export` |
| 🔄 **Self-Healing** | Continuous health checks automatically remove dead proxies |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/hiericho/proxyflow.git
cd proxyflow
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch the orchestrator

```bash
python -m src.main
```

The API will be available at `http://localhost:8000`. Visit `/docs` for the interactive Swagger UI.

---

## 🛠️ API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/` | `GET` | System status and available endpoints |
| `/get-proxy` | `GET` | Returns the fastest available proxy |
| `/export` | `GET` | Bulk export of active proxies as plain text |
| `/proxies` | `POST` | Add a list of proxy URLs to the pool |
| `/proxies` | `DELETE` | Remove specific URLs from the pool |
| `/dashboard` | `GET` | Real-time health metrics and recent logs |
| `/check-now` | `POST` | Manually trigger a health check cycle |

---

## 🔌 Integration Examples

### Playwright

```python
import requests
from playwright.sync_api import sync_playwright

# ProxyFlow selects the best proxy automatically
proxy_url = requests.get("http://localhost:8000/get-proxy").json()["proxy"]

with sync_playwright() as p:
    browser = p.chromium.launch(proxy={"server": proxy_url})
    page = browser.new_page()
    page.goto("https://example.com")
    # ... your scraping logic
    browser.close()
```

### Selenium

```python
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

proxy_url = requests.get("http://localhost:8000/get-proxy").json()["proxy"]

options = Options()
options.add_argument(f"--proxy-server={proxy_url}")

driver = webdriver.Chrome(options=options)
driver.get("https://example.com")
```

### Adding Proxies via API

```bash
curl -X POST "http://localhost:8000/proxies" \
  -H "Content-Type: application/json" \
  -d '{"proxies": ["http://user:pass@host1:port", "http://user:pass@host2:port"]}'
```

---

## 🗂️ Project Structure

```
proxyflow/
├── src/
│   ├── main.py          # FastAPI app & startup
│   ├── checker.py       # Async health check engine
│   ├── router.py        # API route handlers
│   └── database.py      # SQLite persistence layer
├── requirements.txt
└── README.md
```

---

## 📋 Requirements

- Python **3.10+**
- Dependencies: `fastapi`, `uvicorn`, `aiohttp`, `aiosqlite`

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to open a PR or file an issue.

---

*Built with ❤️ for the Automation Community.*