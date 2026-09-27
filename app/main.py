from uuid import uuid4
from fastapi import FastAPI, HTTPException
from app import planner
from app.models import TripRequest, TripState
from app.tools import ToolExecutor, search_places
from app.planner import TravelPlanner
from app.tools import geocode_destination

app = FastAPI(title="Travel Planner")

trips: dict[str, TripState] = {}

tool_executor = ToolExecutor()

planner = TravelPlanner()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/trips")
def create_trip(trip: TripRequest):
    trip_id = str(uuid4())
    state = TripState(trip_id=trip_id,
                      request=trip
            )
    trips[trip_id] = state
    return state

@app.get("/trips/{trip_id}")
def get_trip(trip_id: str):
    if trip_id not in trips:
        raise HTTPException(
            status_code=404,
            detail="Trip not Found"
        )
    return trips[trip_id]

@app.get("/places")
def get_places(destination: str, category: str | None = None):
    return search_places(destination=destination, category=category) 

@app.post("/tools/{tool_name}")
def execute_tool(tool_name: str, arguments: dict):
    try:
        result = tool_executor.execute(tool_name=tool_name, arguments=arguments)

        return {
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        }
    except ValueError as exec:
        raise HTTPException(
            status_code=400,
            detail=str(exec))

@app.post("/plan")
def plan_trip(request: dict):
    user_request = request["request"]

    return planner.plan(user_request)

@app.get("/geocode")
def geocode(destination: str):
    return geocode_destination(destination)            
