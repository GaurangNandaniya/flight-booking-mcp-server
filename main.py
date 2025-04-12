from mcp.server.fastmcp import FastMCP, Context
import json
from datetime import datetime
from typing import Dict, Optional
from serpapi import GoogleSearch
import uuid
from pathlib import Path
import os

# Create an MCP server
mcp = FastMCP("flight-booking-assistant", dependencies=["google-search-results"] ,env=["SERPAPI_KEY","TEMP_FLIGHT_SEARCH_DIR"])

class FlightSearchStorage:
    """
    Handles temporary storage of flight search results.
    
    This class manages the storage and retrieval of flight search results in temporary files.
    It provides methods to save, retrieve, and clean up old search results.
    
    Attributes:
        temp_dir (Path): Directory path for storing temporary search results
    """
    def __init__(self):
        """Initialize the storage with a temporary directory for search results."""
        self.temp_dir = Path(os.getenv("TEMP_FLIGHT_SEARCH_DIR")) 
        # Create the temporary directory if it doesn't exist
        self.temp_dir.mkdir(exist_ok=True)
    
    def save_search_results(self, search_id: str, results: dict) -> None:
        """
        Save flight search results to a temporary file.
        
        Args:
            search_id (str): Unique identifier for the search
            results (dict): Flight search results to store
        """
        file_path = self.temp_dir / f"search_{search_id}.json"
        with open(file_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f)
    
    def get_search_results(self, search_id: str) -> Optional[dict]:
        """
        Retrieve stored flight search results.
        
        Args:
            search_id (str): Unique identifier for the search
            
        Returns:
            Optional[dict]: Stored search results if found, None otherwise
        """
        file_path = self.temp_dir / f"search_{search_id}.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                # print(f"Loading search results from {file_path}")
                data = json.load(f)
                # print(f"Loaded data: {data}")
                return data
        return None
    
    def cleanup_old_searches(self, max_age_hours: int = 24) -> None:
        """
        Remove search results older than the specified age.
        
        Args:
            max_age_hours (int): Maximum age in hours for search results to keep
        """
        current_time = datetime.now()
        for file in self.temp_dir.glob("search_*.json"):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    file_time = datetime.fromisoformat(data['timestamp'])
                    if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                        file.unlink()
            except Exception:
                continue

class FlightBookingServer:
    """
    MCP server implementation for flight booking assistance.
    
    This server provides tools and resources for flight search and booking.
    It handles airport code lookup, flight search, and result filtering.
    """
    def __init__(self):
        """Initialize the flight booking server with storage and airport data."""
        self.storage = FlightSearchStorage()

    def _transform_flight_data(self, api_response: dict, search_params: dict) -> dict:
        """
        Transform SerpAPI response into standardized flight data format.
        
        Args:
            api_response (dict): Raw response from SerpAPI
            search_params (dict): Search parameters used
            
        Returns:
            dict: Transformed flight data
        """
        transformed_flights = []
        
        # Combine best_flights and other_flights
        all_flights = api_response.get("best_flights", []) + api_response.get("other_flights", [])
        
        for flight_itinerary in all_flights:
            if not flight_itinerary.get("flights"):
                continue
                
            flight_segments = []
            for segment in flight_itinerary["flights"]:
                flight_segments.append({
                    "airline": segment.get("airline", ""),
                    "flight_number": segment.get("flight_number", ""),
                    "airplane": segment.get("airplane", ""),
                    "travel_class": segment.get("travel_class", ""),
                    "departure_airport": {
                        "name": segment["departure_airport"]["name"],
                        "id": segment["departure_airport"]["id"],
                        "time": segment["departure_airport"]["time"]
                    },
                    "arrival_airport": {
                        "name": segment["arrival_airport"]["name"],
                        "id": segment["arrival_airport"]["id"],
                        "time": segment["arrival_airport"]["time"]
                    },
                    "duration": segment.get("duration", 0),  # Duration of this segment
                    "airline_logo": segment.get("airline_logo", ""),
                    "legroom": segment.get("legroom", ""),
                    "overnight": segment.get("overnight", False),
                    "plane_and_crew_by": segment.get("plane_and_crew_by", ""),
                    "often_delayed_by_over_30_min": segment.get("often_delayed_by_over_30_min", False)
                })
            
            transformed_flights.append({
                "price": float(flight_itinerary.get("price", 0)),
                "currency": search_params.get("currency", "USD"),
                "total_duration": int(flight_itinerary.get("total_duration", 0)),  # Total journey duration
                "stops": len(flight_itinerary["flights"]) - 1,  # Number of stops (segments - 1)
                "type": flight_itinerary.get("type", ""),  # Round trip/One way
                "airline_logo": flight_itinerary.get("airline_logo", ""),
                "segments": flight_segments,  # All flight segments including layovers
                "carbon_emissions": flight_itinerary.get("carbon_emissions", {}),
                # For convenience, also include direct references to first and last flight
                "departure": {
                    "airport": flight_segments[0]["departure_airport"],
                    "time": flight_segments[0]["departure_airport"]["time"]
                },
                "arrival": {
                    "airport": flight_segments[-1]["arrival_airport"],
                    "time": flight_segments[-1]["arrival_airport"]["time"]
                }
            })
        
        return {
            "search_id": str(uuid.uuid4()),
            # "search_id": 1,
            "timestamp": datetime.now().isoformat(),
            "search_params": search_params,
            "flights": transformed_flights,
            "status": "success"
        }

@mcp.prompt()
def flight_booking_assistant() -> str:
    """
    Define the behavior and guidelines for the flight booking assistant.
    
    This prompt instructs the AI model on how to:
    - Gather flight search information
    - Handle airport disambiguation
    - Manage error cases
    - Guide the conversation flow
    
    Returns:
        str: Comprehensive instructions for the AI model
    """
    return """
    You are a flight booking assistant. Your role is to help users find and book flights by following these guidelines:

    1. INFORMATION GATHERING:
    Required details to collect:
    - Departure location (city)
    - Destination location (city)
    - Departure date (YYYY-MM-DD format)
    - Trip type (round-trip or one-way)
    - Return date (if round-trip, in YYYY-MM-DD format)

    Guidelines:
    - For city names, use your own knowledge to convert to airport IATA codes
    - Always confirm round-trip preference if not explicitly stated
    - Verify dates are clear and valid
    - Handle one missing piece of information at a time
    - Only proceed to search after ALL information is verified

    2. CONVERSATION FLOW:
    - Start by asking for travel plans
    - Collect missing information one piece at a time
    - Confirm details before searching
    - Present results clearly with pricing and timing
    - Help with filtering if needed

    3. ERROR HANDLING:
    - For invalid dates: Explain the issue and request correct format
    - For invalid airports: Ask for clarification or alternative airports
    - For no flights found: Suggest checking alternate dates

    Remember to:
    - Stay professional but friendly
    - Ask one question at a time
    - Confirm understanding before proceeding
    - Use the search_flights tool only when all required information is complete
    """

@mcp.tool()
async def search_flights(
    ctx: Context,
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: Optional[str] = None,
    currency: str = "INR"
) -> Dict:
    """
    Search for flights using the SerpAPI Google Flights engine.
    
    Args:
        ctx: The MCP context
        departure_id: Departure airport IATA code
        arrival_id: Arrival airport IATA code
        outbound_date: Departure date in YYYY-MM-DD format
        return_date: Optional return date for round trips
        currency: Currency code for pricing
        
    Returns:
        Dict: Search results with a unique search ID
    """
    server = FlightBookingServer()
    
    # Validate API key
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return {
            "status": "error",
            "error": "SERPAPI_KEY environment variable is not set"
        }

    # Prepare search parameters
    search_params = {
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "INR",
        "type": 1 if return_date else 2  # 1 for round trip, 2 for one way
    }

    # Prepare API parameters
    params = {
        "engine": "google_flights",
        "hl": "en",
        "gl": "in",
        "api_key": api_key,
        **search_params
    }

    try:
        # Report progress to the user
        await ctx.info(f"Searching flights from {departure_id} to {arrival_id}...")
        
        # Perform the search
        search = GoogleSearch(params)
        api_response = search.get_dict()

        # Check if we got valid results
        if "error" in api_response:
            return {
                "status": "error",
                "error": f"API Error: {api_response['error']}"
            }

        # Transform the response
        transformed_data = server._transform_flight_data(api_response, search_params)
        
        # Store the results
        server.storage.save_search_results(transformed_data["search_id"], transformed_data)
        
        return {
            "status": "success",
            "search_id": transformed_data["search_id"],
            "flights_count": len(transformed_data["flights"]),
            "currency": currency,
            "path": server.storage.temp_dir,
            # "transformed_data": transformed_data
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Search failed: {str(e)}"
        }

@mcp.tool()
def filter_flights(
    filters: Dict
) -> Dict:
    """
    Filter and sort flight search results based on criteria.
    
    Args:
        filters (Dict): Filtering and sorting criteria including:
            - search_id : str: Unique identifier for the search
            - max_price (float): Maximum price
            - max_duration (int): Maximum total flight duration in minutes
            - max_stops (int): Maximum number of stops
            - preferred_airlines (List[str]): List of preferred airlines
            - departure_time_range (Tuple[str, str]): Time range for departure
            - sort_by (str): Field to sort by (price, duration, departure_time)
            - sort_order (str): Sort order (asc, desc)
            
    Returns:
        Dict: Filtered and sorted flight results with counts
    """
    # Load the search results from the storage
    search_id = filters.get("search_id")
    storage = FlightSearchStorage()
    flights_data = storage.get_search_results(search_id)

    if not flights_data:
        return {
            "status": "error",
            "error": "No search results found for the provided search ID"
        }
    
    # Get the flights from the results
    # Another correct way:
    flights = flights_data["results"]["flights"] if flights_data and "results" in flights_data else []
    filtered_flights = []
    # Apply filters
    
    for flight in flights:
        # Apply price filter
        if "max_price" in filters:
            if float(flight.get("price", float("inf"))) > filters["max_price"]:
                continue
        
        # Apply duration filter
        if "max_duration" in filters:
            if int(flight.get("total_duration", float("inf"))) > filters["max_duration"]:
                continue
        
        # Apply stops filter
        if "max_stops" in filters:
            if flight.get("stops", 0) > filters["max_stops"]:
                continue
        
        # Apply airline filter
        if "preferred_airlines" in filters:
            # Check if any segment matches preferred airlines
            segment_airlines = {segment["airline"] for segment in flight["segments"]}
            if not any(airline in filters["preferred_airlines"] for airline in segment_airlines):
                continue
        
        # Apply departure time filter
        if "departure_time_range" in filters:
            start_time, end_time = filters["departure_time_range"]
            departure_time = flight["departure"]["time"]
            if not (start_time <= departure_time <= end_time):
                continue
        
        filtered_flights.append(flight)
    
    # Apply sorting
    if "sort_by" in filters:
        sort_key = filters["sort_by"]
        reverse = filters.get("sort_order", "asc") == "desc"
        
        if sort_key == "price":
            filtered_flights.sort(key=lambda x: float(x.get("price", float("inf"))), reverse=reverse)
        elif sort_key == "duration":
            filtered_flights.sort(key=lambda x: int(x.get("total_duration", 0)), reverse=reverse)
        elif sort_key == "departure_time":
            filtered_flights.sort(key=lambda x: x["departure"]["time"], reverse=reverse)
    
    return {
        "filtered_count": len(filtered_flights),
        "total_count": len(flights),
        "flights": filtered_flights,
        "storage":storage.temp_dir / f"search_{search_id}.json"
    }

if __name__ == "__main__":
    mcp.run()