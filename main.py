from flask import Flask, request, render_template
import sys
import base64
import requests
from datetime import datetime
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

API_KEY = ""
FORECAST_ENDPOINT = "http://api.openweathermap.org/data/2.5/forecast"

WIND_DIRECTIONS_LV = {
    "N": "Ziemeļu",
    "NE": "Ziemeļaustrumu",
    "E": "Austrumu",
    "SE": "Dienvidaustrumu",
    "S": "Dienvidu",
    "SW": "Dienvidrietumu",
    "W": "Rietumu",
    "NW": "Ziemeļrietumu"
}

WEATHER_DESCRIPTIONS_LV = {
    "clear sky": "skaidras debesis",
    "few clouds": "daži mākoņi",
    "scattered clouds": "izkliedēti mākoņi",
    "broken clouds": "daļēji mākoņains",
    "overcast clouds": "apmācies",
    "shower rain": "stiprs lietus",
    "rain": "lietus",
    "thunderstorm": "pērkona negaiss",
    "snow": "sniegs",
    "mist": "migla"
}

def get_wind_direction_lv(deg):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return WIND_DIRECTIONS_LV[directions[round(deg / 45) % 8]]

def create_temperature_plot(dates, temps):
    plt.figure(figsize=(12, 6))
    plt.plot(dates, temps, marker='o', color='b', linestyle='-', markersize=8)
    plt.title('Weekly Temperature Forecast', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Temperature (°C)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True)

    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def get_weather_data(city):
    response = requests.get(FORECAST_ENDPOINT, 
                          params={"q": city, "appid": API_KEY, "units": "metric"})

    if response.status_code != 200:
        return None

    data = response.json()
    daily_data = data["list"][::8]

    forecast_data = []
    for item in daily_data:
        forecast_data.append({
            "time": datetime.fromtimestamp(item["dt"]).strftime('%a, %d.%m'),
            "temperature": item["main"]["temp"],
            "humidity": item["main"]["humidity"],
            "description": WEATHER_DESCRIPTIONS_LV.get(
                item["weather"][0]["description"], 
                item["weather"][0]["description"]
            ),
            "wind_speed": item["wind"]["speed"],
            "wind_direction": get_wind_direction_lv(item["wind"]["deg"])
        })

    dates = [item["time"] for item in forecast_data]
    temps = [item["temperature"] for item in forecast_data]

    return {
        "city": data["city"]["name"],
        "country": data["city"]["country"],
        "forecast": forecast_data,
        "graph_url": create_temperature_plot(dates, temps)
    }

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city = request.form['city']
        weather_data = get_weather_data(city)

        if weather_data:
            graph_url = weather_data.pop("graph_url")
            return render_template('index.html', 
                                 weather_data=weather_data, 
                                 graph_url=graph_url)

        return render_template('index.html', 
                             error_message="Pilsēta nav atrasta vai notika kļūda ar API.")

    return render_template('index.html')

if __name__ == '__main__':
    if input("Vai atvērt mājaslapu? (y/n): ").lower() != 'y':
        print("Izvēlējāties neatsākt mājaslapu.")
        sys.exit()

    print("Palaižu mājaslapu...")
    app.run(host='0.0.0.0', port=8080)
