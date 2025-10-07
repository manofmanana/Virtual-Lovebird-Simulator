"""API handler moved out of project.py for modularity.

Provides APIHandler for weather and bird facts used by the game.
"""
import time
import random

class APIHandler:
    """Handle external API calls for weather, time, and bird facts."""
    
    def __init__(self):
        self.weather_data = None
        self.bird_fact = None
        self.last_weather_update = 0
        self.last_bird_fact_update = 0
        self.weather_update_interval = 1800  # 30 minutes
        self.bird_fact_update_interval = 3600  # 1 hour
    
    def get_weather(self):
        """Get current weather data (using a free weather API).

        For the purposes of the game this returns simulated weather data if
        no external API key is configured. The method caches results briefly.
        """
        current_time = time.time()
        if current_time - self.last_weather_update > self.weather_update_interval:
            try:
                weather_conditions = ["sunny", "cloudy", "rainy", "stormy", "snowy"]
                temperature = random.randint(-10, 35)
                condition = random.choice(weather_conditions)
                self.weather_data = {
                    "temperature": temperature,
                    "condition": condition,
                    "description": f"{condition.title()} weather, {temperature}°C"
                }
                self.last_weather_update = current_time
            except Exception as e:
                print(f"Weather API error: {e}")
                self.weather_data = {
                    "temperature": 20,
                    "condition": "sunny",
                    "description": "Sunny weather, 20°C"
                }
        return self.weather_data

    def get_bird_fact(self):
        """Get a random bird fact.

        Caches a fact for a while to avoid frequent lookups.
        """
        current_time = time.time()
        if current_time - self.last_bird_fact_update > self.bird_fact_update_interval:
            try:
                bird_facts = [
                    "Lovebirds are native to Africa and Madagascar!",
                    "Lovebirds can live up to 15 years in captivity!",
                    "These birds got their name because they form strong pair bonds!",
                    "Lovebirds are very social and can learn to mimic sounds!",
                    "They can recognize themselves in mirrors!",
                    "Lovebirds sleep with their heads tucked under their wings!",
                    "They can fly up to 35 miles per hour!",
                    "Lovebirds have excellent color vision!",
                    "They communicate through various chirps and calls!",
                    "These birds are known for their playful personalities!"
                ]
                self.bird_fact = random.choice(bird_facts)
                self.last_bird_fact_update = current_time
            except Exception as e:
                print(f"Bird facts API error: {e}")
                self.bird_fact = "Birds are amazing creatures! 🦜"
        return self.bird_fact

    def get_weather_mood_effect(self):
        """Get how weather affects Mango's mood (positive/negative integer).

        Returns a small integer which the game applies to happiness. Negative
        values reduce mood; positive values increase it.
        """
        weather = self.get_weather()
        if not weather:
            return 0
        condition = weather["condition"]
        temperature = weather["temperature"]
        mood_effect = 0
        if condition == "sunny":
            mood_effect = 5
        elif condition == "cloudy":
            mood_effect = 0
        elif condition in ["rainy", "stormy"]:
            mood_effect = -10
        elif condition == "snowy":
            mood_effect = -5
        if temperature < 0 or temperature > 30:
            mood_effect -= 5
        return mood_effect
