import httpx


async def get_weather(city: str):
    coordinates = {
        "Moscow": {"latitude": 55.7558, "longitude": 37.6173},
        "Saint Petersburg": {"latitude": 59.9343, "longitude": 30.3351},
        "Novosibirsk": {"latitude": 55.0084, "longitude": 82.9357}
    }
    if city in coordinates:
        latitude = coordinates[city]["latitude"]
        longitude = coordinates[city]["longitude"]
    else:
        # Получаем координаты для других городов через функцию
        latitude, longitude = await get_coordinates(city)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m&daily=temperature_2m_max,temperature_2m_min&timezone=Europe/Moscow")
        weather_data = response.json()

    return {
        "current": weather_data['hourly']['temperature_2m'][0],
        "forecast": weather_data['daily']
    }

async def get_coordinates(city: str):
    api_key = "AIzaSyCZQ4fjEjNFbCYptEmgEG_idQ1H_gIW-l0"
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={city}&inputtype=textquery&fields=geometry&key={api_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        coordinates = data["candidates"][0]["geometry"]["location"]
        return coordinates["lat"], coordinates["lng"]


async def get_place_suggestions(query: str):
    api_key = "AIzaSyCZQ4fjEjNFbCYptEmgEG_idQ1H_gIW-l0"
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={query}&types=(cities)&key={api_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        suggestions = [{"description": place["description"], "place_id": place["place_id"]} for place in data["predictions"]]
        return suggestions