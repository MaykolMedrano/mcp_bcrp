# mcp-bcrp

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/MaykolMedrano/mcp_bcrp)
[![PyPI](https://img.shields.io/pypi/v/mcp-bcrp.svg)](https://pypi.org/project/mcp-bcrp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![User Guide](https://img.shields.io/badge/Guide-User_Guide_(Spanish)-green?style=for-the-badge&logo=jupyter)](https://github.com/MaykolMedrano/mcp_bcrp/blob/main/examples/Guia_Usuario_BCRP.ipynb)
[![Colab](https://img.shields.io/badge/Open_in_Colab-blue?style=for-the-badge&logo=googlecolab)](https://colab.research.google.com/github/MaykolMedrano/mcp_bcrp/blob/main/examples/Guia_Usuario_BCRP.ipynb)

MCP Server and Python library for the **Banco Central de Reserva del Perú (BCRP)** Statistical API. Access over 5,000 macroeconomic indicators directly from your AI agent or Python environment.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [MCP Server](#as-mcp-server)
  - [Python Library](#as-python-library)
- [Available Tools](#available-tools-mcp)
- [Key Indicators](#key-indicators)
- [Search Engine](#search-engine)
- [Architecture](#architecture)
- [Limitations and Warnings](#limitations-and-warnings)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Overview

The `mcp-bcrp` package provides a standardized interface to the BCRP statistical database through the Model Context Protocol (MCP). It supports both direct Python usage and integration with AI assistants such as Claude, Gemini, and other MCP-compatible agents.

The library implements:
- Asynchronous HTTP client for efficient data retrieval
- Deterministic search engine with fuzzy matching capabilities
- Spanish language processing for query canonicalization
- Automatic frequency detection (daily, monthly, quarterly, annual)

---

## Features

| Feature | Description |
|---------|-------------|
| **Smart Search** | Deterministic search engine with fuzzy matching, attribute extraction, and ambiguity detection |
| **Async Native** | Built on `httpx` for non-blocking HTTP requests with connection pooling |
| **Dual Interface** | Use as MCP server for AI agents or as standalone Python library |
| **Chart Generation** | Generate publication-ready charts with automatic Spanish date parsing |
| **Full Coverage** | Access to 5,000+ BCRP economic indicators across all categories |
| **Metadata Cache** | Local caching of 17MB metadata file for fast offline searches |

---

## Requirements

- Python 3.10 or higher
- Internet connection for API requests
- Dependencies: `httpx`, `pandas`, `fastmcp`, `rapidfuzz`, `matplotlib`

---

## Installation

### From PyPI (when published)

```bash
pip install mcp-bcrp
```

### From Source

```bash
git clone https://github.com/YOUR_USERNAME/mcp-bcrp.git
cd mcp-bcrp
pip install -e .
```

### With Optional Dependencies

```bash
pip install mcp-bcrp[charts]  # Include matplotlib for chart generation
pip install mcp-bcrp[dev]     # Include development dependencies
```

---

## Configuration

### MCP Server Configuration

Add the following to your MCP configuration file (e.g., `mcp_config.json`):

```json
{
  "mcpServers": {
    "bcrp-api": {
      "command": "python",
      "args": ["C:/absolute/path/to/mcp_bcrp/run.py"]
    }
  }
}
```

> [!TIP]
> If you have installed the package via pip, you can also use `["-m", "mcp_bcrp"]` as the arguments.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BCRP_CACHE_DIR` | Directory for metadata cache | User cache dir |
| `BCRP_TIMEOUT` | HTTP request timeout in seconds | 120 |

---

## Usage

### As MCP Server

Once configured, the server can be invoked by MCP-compatible AI assistants:

```
User: What is the current policy interest rate in Peru?
Agent: [calls search_series("tasa politica monetaria")]
Agent: [calls get_data(["PD04722MM"], "2024-01/2025-01")]
```

### As Python Library

```python
import asyncio
from mcp_bcrp.client import AsyncBCRPClient, BCRPMetadata

async def main():
    # Initialize metadata client
    metadata = BCRPMetadata()
    await metadata.load()
    
    # Search for an indicator (deterministic)
    result = metadata.solve("tasa politica monetaria")
    print(result)
    # Output: {'codigo_serie': 'PD04722MM', 'confidence': 1.0, ...}
    
    # Fetch time series data
    client = AsyncBCRPClient()
    df = await client.get_series(
        series_codes=["PD04722MM"],
        start_date="2024-01",
        end_date="2025-01"
    )
    print(df.head())

asyncio.run(main())
```

---

## Available Tools (MCP)

| Tool | Parameters | Description |
|------|------------|-------------|
| `search_series` | `query: str` | Search BCRP indicators by keyword. Returns deterministic match or ambiguity error. |
| `get_data` | `series_codes: list[str]`, `period: str` | Fetch raw time series data. Period format: `YYYY-MM/YYYY-MM`. |
| `get_table` | `series_codes: list[str]`, `names: list[str]`, `period: str` | Get formatted table with optional custom column names. |
| `plot_chart` | `series_codes: list[str]`, `period: str`, `title: str`, `names: list[str]`, `output_path: str` | Generate professional PNG chart with automatic date parsing. |

### Available Prompts

| Prompt | Description |
|--------|-------------|
| `economista_peruano` | System prompt to analyze data as a BCRP Senior Economist with rigorous methodology |

---

## Key Indicators

The following are commonly used indicator codes:

| Category | Code | Description | Frequency |
|----------|------|-------------|-----------|
| Monetary Policy | `PD04722MM` | Reference Interest Rate | Monthly |
| Exchange Rate | `PD04638PD` | Interbank Exchange Rate (Sell) | Daily |
| Inflation | `PN01270PM` | CPI Lima Metropolitan | Monthly |
| Copper Price | `PN01652XM` | International Copper Price (c/lb) | Monthly |
| GDP Growth | `PN01713AM` | Agricultural GDP (Var. %) | Annual |
| Business Expectations | `PD38048AM` | GDP Expectations 12 months | Monthly |
| International Reserves | `PN00015MM` | Net International Reserves | Monthly |

> [!NOTE]
> Series codes follow the BCRP naming convention. Use `search_series` to find the appropriate code for your query.

---

## Search Engine

The search engine implements a deterministic pipeline designed for high precision:

```
Query Input
    │
    ▼
┌─────────────────────────────┐
│  1. Canonicalization        │  Lowercase, remove accents, filter stopwords
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  2. Attribute Extraction    │  Currency (USD/PEN), horizon, component type
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  3. Hard Filters            │  Eliminate series not matching attributes
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  4. Fuzzy Scoring           │  Token sort ratio using RapidFuzz
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  5. Ambiguity Detection     │  Return error if top matches are too close
└─────────────────────────────┘
    │
    ▼
Deterministic Result or Explicit Ambiguity Error
```

---

## Architecture

```
mcp_bcrp/
├── __init__.py          # Package initialization and version
├── server.py            # FastMCP server with tool definitions
├── client.py            # AsyncBCRPClient and BCRPMetadata classes
└── search_engine.py     # Deterministic search pipeline implementation

run.py                   # MCP server entry point
bcrp_metadata.json       # Cached metadata (17MB, auto-downloaded)
```

---

## Limitations and Warnings

> [!WARNING]
> **API Rate Limits**: The BCRP API does not publish official rate limits. Implement appropriate delays between requests in production applications to avoid IP blocking.

> [!WARNING]
> **Data Freshness**: Metadata cache (`bcrp_metadata.json`) may become stale. Delete the file periodically to force a refresh of available indicators.

> [!CAUTION]
> **Unofficial Package**: This is an independent implementation and is not officially endorsed by the Banco Central de Reserva del Peru. Data accuracy depends on the upstream API.

### Known Limitations

1. **Date Format**: The BCRP API returns dates in Spanish format (e.g., "Ene.2024"). The library handles this automatically, but custom date parsing may be required for edge cases.

2. **Series Availability**: Not all series are available for all time periods. The API returns empty responses for unavailable date ranges.

3. **Metadata Size**: The complete metadata file is approximately 17MB. Initial load may take several seconds on slow connections.

4. **Frequency Detection**: The library attempts to auto-detect series frequency, but some series may require explicit specification.

---

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes with descriptive messages
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.

---

## Acknowledgments

- [Banco Central de Reserva del Peru](https://www.bcrp.gob.pe/) for providing the public statistical API
- [FastMCP](https://github.com/jlowin/fastmcp) for the Model Context Protocol framework
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) for fuzzy string matching
- [usebcrp](https://github.com/mauricioalvaradoo/usebcrp) for inspiration on BCRP API integration

---

## See Also

| Project | Description |
|---------|-------------|
| [wbgapi360](https://github.com/MaykolMedrano/mcp_wbgapi360) | Enterprise-grade MCP Client for World Bank Data API. Provides access to World Development Indicators, global rankings, country comparisons, and professional FT-style visualizations. |

Both libraries can be used together to build comprehensive macroeconomic analysis pipelines combining Peru-specific BCRP data with global World Bank indicators.

---

**Disclaimer**: This software is provided "as is" without warranty of any kind. The authors are not responsible for any errors in the data or any decisions made based on the information provided by this library.
