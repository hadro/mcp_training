# tools/api_tools.py

from server import mcp
import requests
import os
import json
from typing import List

@mcp.tool()
def search_items(query: str, max_results: int = 5) -> List[str] | str:
    """
    Search for items in the Library of Congress digital collections and store their information.

    Args:
        query: The query to search for
        max_results: The max number of results to retrieve (default: 5)

    Returns: 
        List of item IDs found in the search
    """

    response = requests.get(f"https://www.loc.gov/search/?q={query}&fo=json&c={max_results}").json()
    results = response['results']

    return process_results(query, results)


@mcp.tool()
def get_item_details(item_id: str) -> str:
    """Get the metadata details for a single item from the Library of Congress collections. 

    Args: 
        item_id: The identifier for the item

    Returns: 
        Dictionary of selected parts of description of the item.
    """
    
    item_id = item_id if not "http" in item_id else item_id.strip('/').split('/')[-1]


    response = requests.get(f"https://www.loc.gov/item/{item_id}/?fo=json").json()
    
    item = response['item']

    path = os.path.join("items", item_id.lower().replace(" ","_"))
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "item_info.json")

    try:
        with open(file_path, "r") as json_file:
            item_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        item_info = {}


    item_info = {
        'title': item.get("title", ""),
        "contributor[s]": [contributor for contributor in item.get('contributors',"") or item.get("contributor","")],
        "description": item.get("description", ""),
        "date": item.get('date', ""),
        "link": item.get("id", ""),
        "thumbnail": item.get("image_url", ["None"])[0] if 0 < len(item.get("image_url")) else item.get("image_url", ["None"]),
        "digitized": item.get("digitized", False),
        "genre": item.get("genre"), 
        "subjects": item.get("subject")
    }

    with open(file_path, "w") as json_file:
        json.dump(item_info, json_file, indent=2)

    print(f"Item info is saved in {file_path}")
    return item_id, item_info


@mcp.tool()
def search_collections(query: str, max_results: int = 5) -> str:
    query = query
    collections_json = requests.get(f"https://www.loc.gov/collections/?fo=json&at=results&q={query}&c={max_results}").json()
    return collections_json


# @mcp.tool()
# def get_all_collections() -> str:
#     collections_json = requests.get("https://www.loc.gov/collections/?fo=json&at=results").json()
#     return collections_json


@mcp.tool()
def format_search(query: str, format: str = "photos", max_results: int = 5) -> List[str] | str:
    """Search for items from the Library of Congress collections by both keyword and format.

    Format can be one of: 
        Audio Recordings:       audio
        Books/Printed Material: books
        Film, Videos:           film-and-videos
        Legislation:            legislation
        Manuscripts:            manuscripts
        Maps:                   maps
        Newspapers:             newspapers
        Photo, Print, Drawing:  photos
        Printed Music:          notated-music
        Web Archives:           web-archives 
    
    Args:
        query: The query to search for
        format: The format used to limit the search
        max_results: The max number of results to retrieve (default: 5)
    
    """
    
    query = query
    format = format
    max_results = max_results
    response = requests.get(f"https://www.loc.gov/{format}/?q={query}&fo=json&at=results&c={max_results}").json()
    results = response['results']
    
    return process_results(query, results)

    
@mcp.tool()
def get_trending_content() -> str:
    r = requests.get("https://www.loc.gov/?fo=json&at=trending_content")
    r.json() #print out the results:
    return r


def process_results(query: str, results: str) -> List[str] | str:    
    query = query
    results = results

    path = os.path.join("queries", query.lower().replace(" ","_"))
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "items_info.json")

    try:
        with open(file_path, "r") as json_file:
            items_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        items_info = {}

    item_ids = []
    for item in results:
        #print(item)
        item_ids.append(item['id'])
        item_info = {
            'title': item.get("title", ""),
            "contributor[s]": [contributor for contributor in item.get('contributors',"") or item.get("contributor","")],
            "description": item.get("description", ""), 
            "link": item.get("id", ""),
            "thumbnail": item.get("image_url", ["None"])[0] if 0 < len(item.get("image_url")) else item.get("image_url", ["None"]),
            "digitized": item.get("digitized", False),
            "genre": item.get("genre"), 
            "subjects": item.get("subject")
    }
        items_info[item['id']] = item_info

    with open(file_path, "w") as json_file:
        json.dump(items_info, json_file, indent=2)

    print(f"Results are saved in {file_path}")
    return item_ids, items_info

@mcp.prompt()
def generate_search_prompt(query: str, format: str = "", limit: int = 5) -> str:
    """Generate a prompt to find and summarize LOC items related to a specific query.
    """
    return f"""
    Create a document that supplies information about the items in a search of the Library of Congress's digital collections.
    
    If there is a format provided then search for {limit} {format} items about '{query}' using the format_search tool.
    
    Otherwise search for {limit} items about '{query}' using the search_items tool. 

    
    For all responses, follow these instructions:
    1. First, search for items using either search_items(query='{query}', max_results={limit}) or format_search(query='{query}', format={format}, max_results={limit}) based on the instructions above.
    2. For each item, extract and organize the following information: 
    - Relevance to the query '{query}'
    - Item title
    - Contributor
    - Date
    - Link
    - Thumbnail

    For the thumbnail, I want you to include it as a markdown image, using the following format: 
    ![Item title](Thumbnail)
    
    3. Organize your findings in a clear, structured format with headings and bullet points for easy readability.
    """