# SafeDate MCP Server

A viral AI-powered social safety & fun toolkit for dating, built as an MCP server.

## Setup

1. Clone the repo.
2. Create a .env file with the required keys (see below).
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python main.py`
5. Test with MCP Inspector: `npx @modelcontextprotocol/inspector uvx python main.py`

## API Keys Needed

- GROQ_API_KEY: For Groq LLM (sign up at console.groq.com)
- GOOGLE_API_KEY: For Google Places API (console.cloud.google.com) - Used for restaurant and safety tools
- TAVILY_API_KEY: For Tavily Search (tavily.com) - Used for trending spots
- GIPHY_API_KEY: For Giphy GIFs (developers.giphy.com) - Used for vibe checker
- AUTH_TOKEN: Puch AI auth token (from hackathon organizers)
- MY_NUMBER: Puch AI number (from hackathon organizers)

Google Places API is relevant: Yes, it's used in `best_restaurants_near_me.py` and `safety_tools.py` for location-based searches (free tier with $200 credit/month).