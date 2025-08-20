import os
import json
import pathlib
from mcp.server.fastmcp import FastMCP
from config import config
import requests
from bugzilla import Bugzilla
from bugzilla.bug import Bug
from functools import lru_cache
from typing import Any

mcp = FastMCP("Bugzilla MCP Server")
# api_url = Config
BUGZILLA_CACHE = ".bugzilla.cache.json"
api_url = config.bugzilla_url
bzapi = Bugzilla(config.bugzilla_url, api_key=config.bugzilla_api_key)
suse_default_query_params = {
    "product": "SUSEConnect",
    "component": "General",
    "status": "NEW",
    "priority": "P2",
    "severity": "Medium",
    "assigned_to": "",
    "creator": "",
    "limit": 5,
    "offset": 0,
}
config.default_query_parameters = suse_default_query_params

@mcp.tool(title="Who am I?",description="Who am I - Get information about current user")
def who_am_i() -> dict[str, Any]:
    return "Bugzilla MCP server"

@mcp.tool(title="timezone")
def timezone() -> dict[str, Any]:
    timezone = requests.get(f"{api_url}/rest/timezone")
    return timezone.json()

@mcp.tool(title="get_bug")
def get_bug(bug_id: int):
    assert bzapi.logged_in
    bug: Bug = bzapi.getbug(bug_id)
    return convert_bug_to_dict(bug)

@mcp.tool(title="query_bugs")
def query_bugs(
    product: str = None,
    component: str = None,
    status: str = None,
    priority: str = None,
    severity: str = None,
    assigned_to: str = None,
    creator: str = None,
    limit: int = 20,
    offset: int = 0
) -> dict[str, Any]:
    """
    Search for bugs using various criteria.
    
    Args:
    {
    "status": "NEW",
    "priority": "P2",
    "severity": "Medium",
    "assigned_to": "",
    "creator": "",
    "limit": 5,
    "offset": 0,
}
        product: Product name to search in, Eg. 
    "product": "SUSEConnect",
        component: Component name to search in
    "component": "General",
        status: Bug status (e.g., NEW, ASSIGNED, RESOLVED)
        priority: Bug priority (e.g., P1, P2, P3, P4, P5)
        severity: Bug severity (e.g., blocker, critical, major, normal, minor, trivial)
        assigned_to: Email of the person assigned to the bug
        creator: Email of the bug creator
        limit: Maximum number of results to return (default: 50)
        offset: Number of results to skip (default: 0)
    
    Returns:
        Dictionary containing search results and metadata
        total_results: Total count of bugs
        offset: query offset
        limit: query limit
        query_parameters: query parameters
        bugs: Queried bugs
    """
    assert bzapi.logged_in
    
    # Build query parameters
    query_params = {}
    
    if product:
        query_params['product'] = product or "SUSEConnect"
    if component:
        query_params['component'] = component or "General"
    if status:
        query_params['status'] = status or "NEW"
    if priority:
        query_params['priority'] = priority or "P2 - High"
    if severity:
        query_params['severity'] = severity or "Medium"
    if assigned_to:
        query_params['assigned_to'] = assigned_to or ""
    if creator:
        query_params['creator'] = creator or ""
    
    # Set limit and offset
    query_params['limit'] = min(limit, 20)  # Cap at 100 for performance
    query_params['offset'] = offset
    params = bzapi.build_query(query_params)
    
    try:
        # Execute the query
        bugs = bzapi.query(params)
        
        # Convert bugs to dictionaries
        bug_list = []
        for bug in bugs:
            bug_dict = convert_bug_to_dict(bug)
            bug_list.append(bug_dict)
        
        return {
            "total_results": len(bug_list),
            "offset": offset,
            "limit": query_params['limit'],
            "query_parameters": query_params,
            "bugs": bug_list
        }
        
    except Exception as e:
        return {
            "error": f"Query failed: {str(e)}",
            "query_parameters": query_params
        }


@mcp.tool(title="get_search_options")
async def get_search_options() -> dict[str, Any]:
    """
    Get available search options like products, components, statuses, etc.
    
    Returns:
        Dictionary containing available search options
    """
    assert bzapi.logged_in
    fields = {}
    cache_path = pathlib.PosixPath(os.path.join(os.curdir, BUGZILLA_CACHE))
    if pathlib.Path.exists(cache_path):
        with open(cache_path, "r") as fp:
            raw_content = fp.read()
            fields = json.loads(raw_content)
    else:
        try:
            # Get available products
            products = bzapi.getproducts()
            product_names = [p['name'] for p in products]
            
            # Get field information for statuses, priorities, etc.
            bugfields = bzapi.getbugfields()
            
            # Extract common field values
            status_options = []
            priority_options = []
            severity_options = []
            
            for field in bugfields:
                if field['name'] == 'bug_status':
                    status_options = [v['name'] for v in field.get('values', [])]
                elif field['name'] == 'priority':
                    priority_options = [v['name'] for v in field.get('values', [])]
                elif field['name'] == 'bug_severity':
                    severity_options = [v['name'] for v in field.get('values', [])]
            
            fields = {
                "products": product_names,
                "statuses": status_options,
                "priorities": priority_options,
                "severities": severity_options,
                "search_tips": {
                    "status": "Common values: NEW, ASSIGNED, RESOLVED, VERIFIED, CLOSED",
                    "priority": "Common values: P1 (highest) to P5 (lowest)",
                    "severity": "Common values: blocker, critical, major, normal, minor, trivial",
                    "wildcards": "Use * for wildcards in text searches",
                    "multiple_values": "Separate multiple values with commas"
                }
            }
        except Exception as e:
            return {
                "error": f"Failed to get search options: {str(e)}"
            }
        finally:
            if len(fields.keys()) > 0:
                with open(cache_path, "w+") as fp:
                    fp.write(fields)

    return fields


def convert_bug_to_dict(bug:Bug) -> dict[str, str]:
    return {
        "product_name": bug.product,
        "bug_id": bug.id,
        "bug_priority": bug.priority,
        "created": bug.creation_time,
        "status": bug.status,
        "summary": bug.summary,
        "severity": bug.severity,
        "bug_cc": bug.cc,
        "creator": bug.creator_detail["email"],
        "platform": bug.platform,
        "keywords": ";".join(bug.keywords),
        "component": bug.component,
        "groups": " ".join(bug.groups),
        "weburl": bug.weburl,
        "confirmed": bug.is_confirmed
    }