# Dune Dashboard MCP

A Model Control Protocol (MCP) server that allows AI agents to retrieve data from Dune Analytics dashboards.

## Features

- Extract chart data from any public Dune dashboard
- Parse dashboard URLs to retrieve visualization data
- Return structured JSON data for all charts in a dashboard

## Setup

1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your Cloudflare cookies (see below)
3. Install dependencies: `pip install -r requirements.txt` or `pip install -e .`

## Usage

1. Start the MCP server:

```bash
python main.py
```

2. Call the tool with a Dune dashboard URL:

```
get_dashboard_data("https://dune.com/cryptokoryo/crypto-buy-signal")
```

The tool will return a JSON string containing all chart data from the dashboard.

## Handling Cloudflare Protection

Dune Analytics uses Cloudflare to protect against automated scraping. To bypass this protection, you need to:

1. Copy the `.env.example` file to `.env`
2. Manually obtain cookies from your browser:
   - Visit dune.com in your browser
   - Open Developer Tools (F12)
   - Go to Application tab > Cookies > dune.com
   - Find the 'cf_clearance' cookie and copy its value to `CF_CLEARANCE` in the .env file
   - Optionally, copy the full cookie string from a request header to `DUNE_COOKIES` in the .env file

These cookies allow the MCP to bypass Cloudflare protection. Note that cookies expire, so you may need to update them periodically.

## Example Response

```json
{
  "dashboard_name": "Crypto Buy Signal",
  "dashboard_slug": "crypto-buy-signal",
  "dashboard_id": 120839,
  "user": "cryptokoryo",
  "charts": [
    {
      "visualization_id": 5466888,
      "visualization_type": "chart",
      "visualization_name": "Chart",
      "query_id": 3265994,
      "options": { ... },
      "columns": ["BTC_Price", "Resistance", "Support", "date", "mv_ratio"],
      "columns_metadata": [ ... ],
      "data": [
        {
          "BTC_Price": 8216.510381944427,
          "Resistance": "0.9",
          "Support": "0.1",
          "date": "2019-06-01 00:00:00.000 UTC",
          "mv_ratio": 0.5364287388739318
        },
        ...
      ],
      "total_row_count": 2173
    }
  ]
}
```

## Requirements

- Python 3.13+
- MCP 1.4.1+
- httpx
- pandas
- python-dotenv

## License

See LICENSE file.
