# SafeDate AI: AI-Powered Tools for Safer and Fun Dating

SafeDate AI is an innovative suite of AI-driven tools designed to enhance dating experiences by prioritizing safety, fun, and virality. Built for the Puch AI Hackathon, this project uses Groq AI for natural language analysis, Google Places for location-based recommendations, Tavily for trending searches, and more. It runs as an MCP (Modular Capability Provider) server, exposing tools via a RESTful API that can be integrated with Puch AI or other platforms.

The core focus is on empowering users to:
- Detect risks and red flags in conversations.
- Get personalized date ideas, outfit feedback, and recommendations.
- Ensure safety with emergency tools and SOS sharing.
- Create shareable memes and reports for social media engagement (#SafeDateVibes).

Whether you're planning a date, analyzing a chat, or sharing funny insights, SafeDate makes dating secure, insightful, and entertaining.

## Key Features

SafeDate provides 10 specialized tools, each with a clear purpose, input requirements, and shareable outputs for social media virality:

1. **Text Vibe Checker** (`text_vibe_checker`): Analyzes chat conversations for overall vibes (e.g., Flirty, Bored, Manipulative) using Groq AI. Returns a confidence score, witty reason, GIF, and a shareable meme. Ideal for quick tone assessments.
   
2. **DM Risk Meter** (`dm_risk_meter`): Evaluates unsolicited DMs for creepiness levels (e.g., Harmless, Run) with a danger gauge. Provides a funny roast summary and reasoning. Use for safety screening before replying.

3. **Best Restaurants Near Me** (`best_restaurants_near_me`): Searches for top romantic restaurants based on location using Google Places API, filtered and styled by Groq AI. Includes fun reviews, pro tips, and backups. Perfect for date night planning.

4. **Outfit Rater** (`outfit_rater`): Scores outfits on style, fit, and uniqueness from text descriptions or images. Supports "roast mode" for playful feedback. Great for pre-date fashion advice.

5. **Safety Tools** (`safety_tools`): Locates nearby police stations via Google Places, provides emergency contacts, and generates SOS sharing links (e.g., WhatsApp, Google Maps). Essential for real-time safety during dates.

6. **Best Date Idea** (`best_date_idea`): Generates quirky, unique date ideas tailored to location, weather, and budget using Groq AI. Includes a catchy title, description, and bonus tip. Use for creative, screenshot-worthy suggestions.

7. **Rate My Date** (`rate_my_date`): Rates post-date experiences with scores for humor, vibe, and chemistry. Delivers a fun "Date Report Card" with reviews, improvements, and second-date predictions.

8. **Date Analyzer** (`date_analyzer`): Detects manipulation tactics (e.g., gaslighting, love bombing) in conversations using Groq AI. Returns detected issues, confidence, and explanations. Crucial for spotting red flags.

9. **Trendy Date Spotter** (`trendy_date_spotter`): Searches for trending date spots in a location using Tavily's real-time web search. Returns top results with snippets and URLs. Ideal for discovering hot, viral spots.

10. **Date Meme Generator** (`date_meme_generator`): Creates funny, shareable memes from date texts or conversations with AI-generated captions. Adds a viral touch with hashtags like #SafeDateMeme.

All tools include error handling, input validation with Pydantic, and async operations for efficiency. Outputs often feature "share_text" for easy social media posting.

## Why SafeDate AI?
In a world where online dating can be risky, SafeDate combines cutting-edge AI with practical tools to promote safety (e.g., red flag detection, emergency resources) and enjoyment (e.g., memes, personalized ideas). Built with scalability in mind, it's perfect for integration into dating apps or chatbots. For the Puch AI Hackathon, it demonstrates modular tool design, real-time API interactions, and user-centric features like virality.

## Project Structure
- **`src/main.py`**: Entry point for the MCP server, registers all tools, and handles authentication.
- **`src/tools/`**: Directory containing individual tool implementations (e.g., `text_vibe_checker.py`).
- **`.env`**: Stores API keys and secrets (not committed to Git).
- **`requirements.txt`**: Lists dependencies for easy installation.

## Installation and Setup
1. **Clone the Repository**:
   ```
   git clone https://github.com/yourusername/safedate-ai.git
   cd safedate-ai
   ```

2. **Install Dependencies**:
   Create a virtual environment and install packages:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

   Sample `requirements.txt`:
   ```
   fastmcp
   groq
   pydantic
   httpx
   pillow
   python-dotenv
   re
   json
   base64
   io
   random
   urllib.parse
   datetime
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory with your API keys:
   ```
   GROQ_API_KEY=your_groq_api_key
   GOOGLE_API_KEY=your_google_api_key
   TAVILY_API_KEY=your_tavily_api_key
   GIPHY_API_KEY=your_giphy_api_key  # Note: It's GIPHY, but code uses Giphy—ensure consistency
   AUTH_TOKEN=your_auth_token_for_mcp
   MY_NUMBER=your_puch_validation_number
   ```

   Obtain keys from:
   - Groq: For LLM analysis.
   - Google Cloud: For Places API (enable Places API in console).
   - Tavily: For web search.
   - Giphy: For GIFs.
   - Puch AI: For AUTH_TOKEN and MY_NUMBER.

4. **Run the Server**:
   ```
   python main.py
   ```
   The server starts on `http://0.0.0.0:8086`. You'll see debug prints for registered tools.

5. **Expose with Ngrok** (for public access or Puch AI integration):
   ```
   ngrok http 8086
   ```
   Copy the ngrok URL (e.g., `https://abc.ngrok.io`) and use it in Puch AI or for testing.

## Usage
- **Test Tools Locally**: Use curl with your AUTH_TOKEN:
  ```
  curl -H "Authorization: Bearer $AUTH_TOKEN" -X POST http://localhost:8086/validate
  curl -H "Authorization: Bearer $AUTH_TOKEN" -X POST http://localhost:8086/text_vibe_checker -d '{"messages": "Hey, you're amazing! 😊", "raw": false}'
  ```
- **Integration with Puch AI**: Provide the ngrok URL as your MCP endpoint. Tools are discoverable via the MCP framework.
- **Error Handling**: Tools validate inputs and raise descriptive errors (e.g., invalid params, API failures).
- **Async and Scalable**: Built with `asyncio` and `httpx` for efficient API calls.

## Potential Improvements
- Add more tools (e.g., profile analyzer using X search).
- Integrate vision models for advanced image analysis in `outfit_rater`.
- Expand emergency contacts for international users.

## License
MIT License. Feel free to fork and contribute!

## Contact
For questions or collaboration, reach out via [your email] or GitHub issues.

