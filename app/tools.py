import os
import httpx
from typing import Any, Callable
from dotenv import load_dotenv

load_dotenv()

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

MOCK_PLACES = {
    "Iceland": [
        {
            "name": "Blue Lagoon",
            "category": "hot_springs",
            "location": "Grindavik",
            "estimated_duration_hours": 3
        },
        {
            "name": "Thingvellir National Park",
            "category": "nature",
            "location": "Thingvellir",
            "estimated_duration_hours": 2
        },
        {
            "name": "Gullfoss",
            "category": "nature",
            "location": "Golden Circle",
            "estimated_duration_hours": 1.5
        },
        {
            "name": "Reykjavik",
            "category": "city",
            "location": "Reykjavik",
            "estimated_duration_hours": 4
        }
    ]
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "search_places",
        "description": "Search for places to visit in a destination.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Destination country or city"
                },
                "category": {
                    "type": ["string", "null"],
                    "enum": [
                        "touristy",
                        "attraction",
                        "sights",
                        "restaurant",
                        "spa",
                        None
                    ],
                    "description": "Type of place to search for"
                }
            },
            "required": [
                "destination",
                "category"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
]

CATEGORY_MAP = {
    "touristy": "tourism",
    "attraction": "tourism.attraction",
    "restaurant": "catering.restaurant",
    "sights": "tourism.sights",
    "nature": "natural",
    "hot_springs": "natural.water.hot_spring",
    "museum": "entertainment.museum",
    "spa": "leisure.spa",
    "hotel": "accommodation.hotel",
}

def search_places_mock_data(destination: str, category: str | None = None) -> list[dict[str, Any]]:
    places = MOCK_PLACES.get(destination, [])

    if(category is None):
        return places

    return [
        place 
        for place in places
        if(place["category"] == category)
    ]

def get_geoapify_category(category: str) -> str:
    geoapify_category = CATEGORY_MAP.get(category)

    if geoapify_category is None:
        raise ValueError(
            f"Unsupported place category: {category}"
        )

    return geoapify_category

def search_places(destination: str, category: str | None = None) -> list[dict[str, Any]]:
    geocoded = geocode_destination(destination)

    geoapify_category = get_geoapify_category(category)

    if not geocoded["found"]:
        return []

    # geoapify_category = CATEGORY_MAP.get(
    #     category,
    #     "tourism",
    # )
    
    response = httpx.get(
        "https://api.geoapify.com/v2/places",
        params={
            "categories": geoapify_category,
            "filter": f"place:{geocoded['place_id']}",
            "limit": 25,
            "lang": "en",
            "apiKey": GEOAPIFY_API_KEY,
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    places = []

    for feature in data.get("features", []):
        properties = feature.get("properties", {})

        places.append(
            {
                "name": properties.get("name"),
                "category": category,
                "formatted_address": properties.get("formatted"),
                "city": properties.get("city"),
                "country": properties.get("country"),
                "lat": properties.get("lat"),
                "lon": properties.get("lon"),
                "place_id": properties.get("place_id"),
            }
        )
    
    return places


def geocode_destination(destination: str) -> dict:
    if not GEOAPIFY_API_KEY:
        raise RuntimeError(
            "GEOAPIFY_API_KEY is not configured"
        )

    response = httpx.get(
        "https://api.geoapify.com/v1/geocode/search",
        params={
            "text": destination,
            "format": "json",
            "limit": 1,
            "apiKey": GEOAPIFY_API_KEY,
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results", [])

    if not results:
        return {
            "found": False,
            "destination": destination,
        }

    result = results[0]

    return {
        "found": True,
        "destination": destination,
        "formatted": result.get("formatted"),
        "lat": result.get("lat"),
        "lon": result.get("lon"),
        "country": result.get("country"),
        "city": result.get("city"),
        "place_id": result.get("place_id"),
    }

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "search_places": search_places,
}    

class ToolExecutor:

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:

        tool = TOOL_REGISTRY.get(tool_name)

        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        return tool(**arguments)    