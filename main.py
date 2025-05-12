from mcp.server.fastmcp import FastMCP
import json
import pandas as pd
import subprocess
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Initialize MCP server
mcp = FastMCP(
    name="Dune Dashboard MCP",
    description="Retrieve raw data from Dune dashboards",
    dependencies=["pandas", "python-dotenv"],
)

# API endpoints
GRAPHQL_API = 'https://core-api.dune.com/public/graphql'
EXECUTION_API = 'https://core-api.dune.com/public/execution'

# Direct cookie string from the example
DUNE_COOKIES = 'AMP_MKTG_e76ce253e6=JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE; _ga=GA1.1.1640660718.1747030585; cf_clearance=sMwBpEr3lhXc7M9xrNSMmE7kCPHqobnJh.PJezDPafs-1747030587-1.2.1.1-YFKOda.i7A834ldSVk.QLT67tPP_biogN9jeZbQHOzNL_TF7Hsn8yKhzDXsfg1zTJmaSLB1hRbH9AFwpO5IAS_txvciAi8gLPm6WIvjSM82PMjU_uNY95tOIqAKX7ePB3PGZ29eSTx.OJ6sIWh3tLqGfeAhD.J6mZorrSIeB0lZCE2NpTZ20w8Zgdd0is.VM3yQhQIFOFOMWc2BRTNW4nsVvuyoE2eOe_Rp6IcoH9PS6UNCXYdhZGxuW5XwbfhH.NywCNliLdw2cw5WiVLho6NY0uDrDJRrqMsownM3X3ZJYExvbxLdxf7y8.bcJK9_7njeRq62AIkPnyJUrs3JO13ciwuOOqZzBan4evmYxaH0; AMP_e76ce253e6=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjIzYmQzNjA5Yy05Y2E3LTRjMmItYWY0Mi0wZjRmNDdjMDkzMmYlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzQ3MDMwNTg1MzMxJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc0NzAzMDU5MTE0MCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMyU3RA==; __hstc=178244666.fffa39c8772dae9627b24c2b43611b27.1747030592582.1747030592582.1747030592582.1; hubspotutk=fffa39c8772dae9627b24c2b43611b27; __hssrc=1; __stripe_mid=075ed6b0-13a3-4ffc-a0c3-868fd5ec6ab12938d7; __stripe_sid=55a22581-621f-4658-b6ab-45a29a41771f3af967; _ga_H1G057R0KN=GS2.1.s1747030585$o1$g1$t1747030621$j0$l0$h0; __hssc=178244666.2.1747030592582'

# GraphQL queries
FIND_DASHBOARD_QUERY = """query FindDashboard($filters: DashboardFilterInput!) {
    dashboards(filters: $filters, pagination: {first: 1}) {
        edges {
            node {
                ...FindDashboard
                __typename
            }
            __typename
        }
        __typename
    }
}

fragment User on User {
    id
    name
    profile_image_url: profileImageUrl
    __typename
}

fragment Team on Team {
    id
    name
    handle
    profile_image_url: profileImageUrl
    __typename
}

fragment DashboardVisualization on Visualization {
    id
    type
    name
    description
    options
    created_at: createdAt
    query_details: query {
        query_id: id
        name
        description
        show_watermark: showWatermark
        parameters
        dataset_id: datasetId
        user {
            ...User
            __typename
        }
        team {
            ...Team
            __typename
        }
        __typename
    }
    __typename
}

fragment FindDashboard on Dashboard {
    id
    name
    slug
    isPrivate
    isArchived
    createdAt
    repoLink
    tags
    hasStarred
    isTrending
    mintable
    verificationStatus
    starCount
    pageViewCount(timeframe: TIMEFRAME_ALL)
    user {
        ...User
        __typename
    }
    team {
        ...Team
        __typename
    }
    forkedDashboard {
        slug
        name
        user {
            name
            __typename
        }
        team {
            handle
            __typename
        }
        __typename
    }
    textWidgets {
        id
        text
        options
        __typename
    }
    visualizationWidgets {
        id
        options
        visualization {
            ...DashboardVisualization
            __typename
        }
        __typename
    }
    paramWidgets {
        id
        key
        visualization_widget_id: visualizationWidgetId
        query_id: queryId
        dashboard_id: dashboardId
        options
        __typename
    }
    __typename
}"""

GET_EXECUTION_QUERY = """query GetLatestResultSetIds($canRefresh: Boolean!, $queryId: Int!, $parameters: [ExecutionParameterInput!]) {
    resultSetForQuery(
        canRefresh: $canRefresh
        queryId: $queryId
        parameters: $parameters
    ) {
        completedExecutionId
        failedExecutionId
        pendingExecutionId
        __typename
    }
}"""

def run_curl_command(url, data, is_json=True):
    """
    Run a curl command to make an HTTP request.
    
    Args:
        url: The URL to send the request to
        data: The data to send (either JSON or raw data)
        is_json: Whether the data is JSON (if True, adds Content-Type header)
        
    Returns:
        dict: Response data parsed as JSON or None if failed
    """
    try:
        # Create the curl command
        cmd = [
            'curl', url,
            '-H', 'accept: */*',
            '-H', 'accept-language: zh-CN,zh;q=0.9',
            '-b', DUNE_COOKIES,
            '-H', 'origin: https://dune.com',
            '-H', 'priority: u=1, i',
            '-H', 'referer: https://dune.com/',
            '-H', 'sec-ch-ua: "Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            '-H', 'sec-ch-ua-mobile: ?0',
            '-H', 'sec-ch-ua-platform: "macOS"',
            '-H', 'sec-fetch-dest: empty',
            '-H', 'sec-fetch-mode: cors',
            '-H', 'sec-fetch-site: same-site',
            '-H', 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        ]
        
        # Add Content-Type header if JSON
        if is_json:
            cmd.extend(['-H', 'content-type: application/json'])
            
        # Add data
        if isinstance(data, dict) or isinstance(data, list):
            data_str = json.dumps(data)
            cmd.extend(['--data-raw', data_str])
        else:
            cmd.extend(['--data-raw', str(data)])
        
        print(f"Running curl command: {' '.join(cmd[:5])}... [truncated]")
        
        # Run the curl command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        
        try:
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response: {result.stdout[:200]}...")
            return None
            
    except Exception as e:
        print(f"Error running curl command: {e}")
        return None

def parse_dune_url(url):
    """
    Parse a Dune dashboard URL to extract handle and slug.
    
    Args:
        url: The Dune dashboard URL
        
    Returns:
        tuple: (handle, slug) or (None, None) if invalid
    """
    parsed_url = urlparse(url)
    if 'dune.com' not in parsed_url.netloc:
        return None, None
    
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) != 2:
        return None, None
    
    return path_parts[0], path_parts[1]

def fetch_dashboard_info(handle, slug):
    """
    Fetch dashboard information from Dune API.
    
    Args:
        handle: The user/team handle
        slug: The dashboard slug
        
    Returns:
        dict: Dashboard data or None if failed
    """
    dashboard_query = {
        "operationName": "FindDashboard",
        "variables": {
            "filters": {
                "slug": {"equals": slug},
                "handle": {"equals": handle}
            }
        },
        "query": FIND_DASHBOARD_QUERY
    }
    
    response = run_curl_command(GRAPHQL_API, dashboard_query)
    
    if not response:
        return None
    
    # Check if dashboard exists
    if not response.get('data', {}).get('dashboards', {}).get('edges'):
        return None
    
    return response['data']['dashboards']['edges'][0]['node']

def get_execution_id(query_id, parameters):
    """
    Get execution ID for a query.
    
    Args:
        query_id: The query ID
        parameters: Query parameters
        
    Returns:
        str: Execution ID or None if failed
    """
    execution_query = {
        "operationName": "GetLatestResultSetIds",
        "variables": {
            "queryId": query_id,
            "parameters": parameters,
            "canRefresh": True
        },
        "query": GET_EXECUTION_QUERY
    }
    
    response = run_curl_command(GRAPHQL_API, execution_query)
    
    if not response:
        return None
    
    return response.get('data', {}).get('resultSetForQuery', {}).get('completedExecutionId')

def fetch_chart_data(execution_id, query_id, parameters, columns):
    """
    Fetch chart data using execution ID.
    
    Args:
        execution_id: The execution ID
        query_id: The query ID
        parameters: Query parameters
        columns: Output columns to fetch
        
    Returns:
        dict: Chart data or None if failed
    """
    chart_data_query = {
        "execution_id": execution_id,
        "query_id": query_id,
        "parameters": parameters,
        "output_columns": columns,
        "sampling": {"count": 8000}
    }
    
    response = run_curl_command(EXECUTION_API, chart_data_query)
    
    return response

def process_visualization(visualization):
    """
    Process a visualization to extract query details and options.
    
    Args:
        visualization: The visualization data
        
    Returns:
        tuple: (query_id, parameters, options, columns, viz_info) or None if invalid
    """
    if not visualization:
        return None
    
    query_details = visualization.get('query_details', {})
    if not query_details:
        return None
    
    query_id = query_details.get('query_id')
    parameters = query_details.get('parameters', [])
    
    if not query_id:
        return None
    
    # Extract visualization info
    viz_info = {
        "visualization_id": visualization.get('id'),
        "visualization_type": visualization.get('type'),
        "visualization_name": visualization.get('name')
    }
    
    # Process options
    options = visualization.get('options', {})
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except:
            options = {}
    
    # Extract columns from options
    columns = []
    column_mapping = options.get('columnMapping', {})
    if column_mapping:
        columns = list(column_mapping.keys())
    
    return query_id, parameters, options, columns, viz_info

# @mcp.tool()
def get_dashboard_data(url: str) -> str:
    """
    Retrieve chart data from a Dune dashboard URL.
    
    Args:
        url: The URL of the Dune dashboard, e.g., https://dune.com/cryptokoryo/crypto-buy-signal
    
    Returns:
        JSON string containing the chart data
    """
    try:
        # Step 1: Parse URL to get handle and slug
        handle, slug = parse_dune_url(url)
        if not handle or not slug:
            return json.dumps({"error": "Invalid Dune dashboard URL format"})
            
        # Step 2: Fetch dashboard info
        print(f"Fetching dashboard info for {handle}/{slug}...")
        dashboard_node = fetch_dashboard_info(handle, slug)
        if not dashboard_node:
            return json.dumps({"error": "Dashboard not found or access denied by Cloudflare."})
        
        # Get visualization widgets
        visualization_widgets = dashboard_node.get('visualizationWidgets', [])
        if not visualization_widgets:
            return json.dumps({"error": "No visualizations found in dashboard"})
        
        # Step 3: Process each visualization widget
        charts_data = []
        
        for widget in visualization_widgets:
            visualization = widget.get('visualization', {})
            processed_data = process_visualization(visualization)
            
            if not processed_data:
                continue
                
            query_id, parameters, options, columns, viz_info = processed_data
            
            # Step 4: Get execution ID for the query
            print(f"Getting execution ID for query {query_id}...")
            execution_id = get_execution_id(query_id, parameters)
            if not execution_id:
                continue
            
            # Step 5: Fetch chart data
            print(f"Fetching chart data for execution {execution_id}...")
            chart_data = fetch_chart_data(execution_id, query_id, parameters, columns)
            if not chart_data:
                continue
            
            # Step 6: Extract and format chart result
            chart_result = {
                **viz_info,
                "query_id": query_id,
                "options": options
            }
            
            if chart_data.get('execution_succeeded'):
                succeeded_data = chart_data['execution_succeeded']
                chart_result['columns'] = succeeded_data.get('columns', [])
                chart_result['columns_metadata'] = succeeded_data.get('columns_metadata', [])
                chart_result['data'] = succeeded_data.get('data', [])
                chart_result['total_row_count'] = succeeded_data.get('total_row_count', 0)
            
            charts_data.append(chart_result)
        
        # Step 7: Return dashboard data with all charts
        result = {
            "dashboard_name": dashboard_node.get('name'),
            "dashboard_slug": dashboard_node.get('slug'),
            "dashboard_id": dashboard_node.get('id'),
            "user": dashboard_node.get('user', {}).get('name'),
            "charts": charts_data
        }

        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to process dashboard: {str(e)}"})

if __name__ == "__main__":
    # print("Testing dashboard data retrieval...")
    # result = fetch_dashboard_info("cryptokoryo", "crypto-buy-signal")
    # if result:
    #     print("Successfully retrieved dashboard info!")
    #     print(json.dumps(result, indent=2)[:500] + "...")  # Print truncated result
    # else:
    #     print("Failed to retrieve dashboard info.")
    
    # Uncomment to run MCP server
    # print("Starting Dune Dashboard MCP server...")
    # print(get_dashboard_data("https://dune.com/cryptokoryo/crypto-buy-signal"))
    mcp.run()
