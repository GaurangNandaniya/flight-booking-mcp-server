# Flight Booking MCP Server

A powerful flight booking assistant server built using MCP (Model Context Protocol) that provides flight search and booking capabilities through natural language interactions.

## Features

- Natural language flight search interface using MCP protocol
- Real-time flight search using SerpAPI
- Support for one-way and round-trip flights
- Detailed flight information including:
  - Pricing
  - Flight duration
  - Number of stops
  - Airline details
  - Carbon emissions data
  - Legroom information
- Temporary storage of search results
- Automatic cleanup of old search data

## Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- SerpAPI account and API key
- Claude Desktop App (for local development)

## Installation

1. Clone the repository:

```bash
git clone git@github.com:GaurangNandaniya/flight-booking-mcp-server.git
cd flight-booking-mcp-server
```

2. Initialize the project with uv:

```bash
uv init
```

3. Install dependencies:

```bash
uv add "mcp[cli]"
```

4. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Configuration

### Environment Variables

1. Create a `.env` file in the project root with your SerpAPI key:

```
SERPAPI_KEY=your_api_key_here
```

2. Additional environment variables you might need:

```
# Optional: Set the port for the MCP server
MCP_PORT=8000

# Optional: Set the host for the MCP server
MCP_HOST=localhost
```

### Claude Desktop Integration

1. Install Claude Desktop App from [Anthropic's website](https://claude.ai/download)

2. Configure the app to connect to your local MCP server:

   - Set the server URL to: `http://localhost:8000` (or your custom host:port)

3. Install the server in Claude Desktop with environment variables:

   ```bash
   # Method 1: Load from .env file
   uv run mcp install main.py -f .env

   # Method 2: Set individual variables
   uv run mcp install main.py -v SERPAPI_KEY=your_key_here -v MCP_PORT=8000 -v TEMP_FLIGHT_SEARCH_DIR=dir_here
   ```

## Running the Development Server

### Development Mode

The fastest way to test and debug your server is with the MCP Inspector:

```bash
uv run mcp dev main.py
```

### Claude Desktop Integration

Once your server is ready, install it in Claude Desktop:

```bash
# With environment variables from .env file
uv run mcp install main.py -f .env

# Or with individual environment variables
uv run mcp install main.py -v SERPAPI_KEY=your_key_here -v TEMP_FLIGHT_SEARCH_DIR=dir_here
```

### Direct Execution

For advanced scenarios like custom deployments:

```bash
uv run mcp run main.py
```

## Project Structure

- `main.py`: Core server implementation with flight search and booking logic
  - `FlightSearchStorage`: Manages temporary storage of search results
  - `FlightBookingServer`: Implements MCP server with flight search capabilities
  - `@mcp.tool()`: Exposes flight search functionality to LLMs
  - `@mcp.prompt()`: Defines the flight booking assistant's behavior
- `temp_search_results/`: Directory for storing temporary search results
- `pyproject.toml`: Project configuration and dependencies
- `.env`: Environment variables (not tracked in git)
- `uv.lock`: uv dependency lock file

## MCP Implementation Details

This server implements the following MCP primitives:

1. **Tools**

   - `search_flights`: Searches for flights based on user criteria
   - `filter_flights`: Filters and sorts flight search results

2. **Prompts**

   - `flight_booking_assistant`: Defines the behavior and guidelines for the flight booking assistant

3. **Resources**
   - Temporary storage of flight search results
   - Automatic cleanup of old search data

## Usage

The flight booking assistant can help you with:

1. Finding flights between cities
2. Comparing prices and flight durations
3. Filtering results based on preferences
4. Getting detailed information about specific flights

Example conversation flow:

```
User: I want to book a flight from Bangalore to Ahmedabad
Assistant: I can help you with that. When would you like to travel?
User: On May 3rd
Assistant: Would you like a one-way or round-trip ticket?
...
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
