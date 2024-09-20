from .dtypes import Weather

from typing import TYPE_CHECKING

class WeatherEffect:
    def __init__(self, weather: Weather, turns):
        self.weather = weather 
        self.turns = turns  
        self.remaining_turns = turns 

    def weather_tick(self) -> str:
        if self.weather != Weather.clear and self.remaining_turns >= 0:
            self.remaining_turns -= 1
            if self.remaining_turns == 0:
                self.weather = Weather.clear
                return "The weather cleared"
        elif self.weather == Weather.rain:
            return "The rain continues to fall!"
        elif self.weather == Weather.sun:
            return "The sun shines bright!"
        elif self.weather == Weather.snow:
            return "The snow continues to fall!"
        elif self.weather == Weather.sand:
            return "The sandstorm continues!"
        else:
           return None