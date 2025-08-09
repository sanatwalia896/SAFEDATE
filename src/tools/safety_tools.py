import requests
from urllib.parse import quote
from mcp.server import Tool
from typing import Dict, Any, List

class SafetyTools(Tool):
    def __init__(self, google_api_key: str):
        super().__init__("safety_tools", "Find nearby police stations, emergency numbers & SOS sharing")
        self.google_api_key = google_api_key

    def _find_nearby_police(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        """Uses Google Places API to get nearby police stations."""
        url = (
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            f"?location={lat},{lon}&radius=5000&type=police&key={self.google_api_key}"
        )
        r = requests.get(url)
        data = r.json()
        results = []
        for place in data.get("results", []):
            results.append({
                "name": place.get("name"),
                "address": place.get("vicinity"),
                "maps_link": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}"
            })
        return results

    def _emergency_contacts(self) -> List[Dict[str, str]]:
        """Static emergency numbers (could be expanded per country)."""
        return [
            {"name": "Police", "number": "100"},
            {"name": "Ambulance", "number": "102"},
            {"name": "Women’s Helpline", "number": "1091"}
        ]

    def _share_location_link(self, lat: float, lon: float) -> str:
        """Generate a Google Maps location link."""
        return f"https://maps.google.com/?q={lat},{lon}"

    def _whatsapp_sos_link(self, lat: float, lon: float) -> str:
        """Generate WhatsApp SOS message with location."""
        maps_link = self._share_location_link(lat, lon)
        message = f"🚨 SOS! I need help! My location: {maps_link}"
        return f"https://wa.me/?text={quote(message)}"

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        lat = inputs.get("latitude")
        lon = inputs.get("longitude")

        if not lat or not lon:
            return {"error": "Latitude and longitude are required"}

        police_stations = self._find_nearby_police(lat, lon)
        emergency_numbers = self._emergency_contacts()
        location_link = self._share_location_link(lat, lon)
        whatsapp_sos = self._whatsapp_sos_link(lat, lon)

        return {
            "police_stations": police_stations,
            "emergency_contacts": emergency_numbers,
            "share_location_link": location_link,
            "call_police_now": "tel:100",
            "whatsapp_sos_link": whatsapp_sos
        }
