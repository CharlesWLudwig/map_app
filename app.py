from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from shapely.geometry import Point as Shapely_point, mapping
from geojson import Point as Geoj_point, Polygon as Geoj_polygon, Feature, FeatureCollection
import folium
import os 
from folium import plugins
import pandas as pd
import numpy as np
import re
from pprint import pprint
import random
import requests
import json
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your secret key'

def creatingFoliumMap(browser_latitude, browser_longitude):   
    params = {'point': f'{browser_latitude},{browser_longitude}',  
            'unit': 'mph', 'thickness': 14, 
            'key': os.getenv('TOMTOM_API_KEY')}
    
    base_url = 'https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json'
    
    data = requests.get(base_url, params=params)
    
    data = data.json()

    road_types = {'FRC0': 'Motorway', 'FRC1': 'Major road', 'FRC2': 'Other major road', 'FRC3': 'Secondary road',
                'FRC4': 'Local connecting road', 'FRC5': 'Local road of high importance', 'FRC6': 'Local road'}

    if data['flowSegmentData']['roadClosure']:
        reply = 'Unfortunately this road is closed!'
    else:
        reply = (f"Your nearest road is classified as a {road_types[data['flowSegmentData']['frc']]}.  "
                f"The current average speed is {data['flowSegmentData']['currentSpeed']} mph and "
                f"would take {data['flowSegmentData']['currentTravelTime']} seconds to pass this section of road.  "
                f"With no traffic, the speed would be {data['flowSegmentData']['freeFlowSpeed']} mph and would "
                f"take {data['flowSegmentData']['freeFlowTravelTime']} seconds.")

    points = [(i['latitude'], i['longitude']) for i in data['flowSegmentData']['coordinates']['coordinate']]
    
    return reply, points

def getBrowserLocation(browser_latitude, browser_longitude):
    geocode_data_info = [] 

    mapquest_api = os.getenv('MAPQUEST_API')

    # Reverse geocode browser longitude and latitude to an address
    geocode_url = f'https://www.mapquestapi.com/geocoding/v1/reverse?key={mapquest_api}&location={browser_latitude},{browser_longitude}&includeRoadMetadata=true&includeNearestIntersection=true'

    geocode_data = requests.get(geocode_url)

    if geocode_data.status_code == 200:
        geocode_data = geocode_data.json()

        geocode_data_list = list()

        for i in geocode_data['results']:
            geocode_data_list.append(i)
   
        for i in geocode_data_list[0]['locations']:
            geocode_data_info.append(i)

        """
        adminArea1 = geocode_data_info[00]['adminArea1']
        adminArea3 = geocode_data_info[0]['adminArea3']
        adminArea4 = geocode_data_info[0]['adminArea4']
        adminArea5 = geocode_data_info[0]['adminArea5']
        adminArea6 = geocode_data_info[0]['adminArea6']
        postalcode = geocode_data_info[0]['postalCode']
        browserLat = geocode_data_info[0]['displayLatLng']['lat']
        browserLng = geocode_data_info[0]['displayLatLng']['lng']
        roadMetadata = geocode_data_info[0]['roadMetadata']
        roadSpeedLimit = geocode_data_info[0]['roadMetadata']['speedLimit']
        roadSpeedLimitUnits = geocode_data_info[0]['roadMetadata']['speedLimitUnits']
        tollRoad = geocode_data_info[0]['roadMetadata']['tollRoad']

        geocode_data_info = [
            adminArea1, 
            adminArea3, 
            adminArea4, 
            adminArea5, 
            adminArea6,
            postalcode,
            browserLat,
            browserLng,
            roadMetadata,
            roadSpeedLimit,
            roadSpeedLimitUnits,
            tollRoad
        ]
        """
    return geocode_data_info

def getCurrentWeather(browser_latitude, browser_longitude):
    mapquest_api = os.getenv('OPENWEATHER_API')

    # Reverse geocode browser longitude and latitude to an address
    weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat={browser_latitude}&lon={browser_longitude}&units=imperial&appid={mapquest_api}'

    weather_data = requests.get(weather_url)

    if weather_data.status_code == 200:
        weather_data = weather_data.json()

    reply = (f"It's a {weather_data['weather'][0]['description']} today."
             f"\nThe temperature is {weather_data['main']['temp']}, and it feels like {weather_data['main']['feels_like']}."
             f"\nThe sunrise will occur at {weather_data['sys']['sunrise']} and the sunset will occur at {weather_data['sys']['sunset']}")
    
    return reply

def getForecastWeather(browser_latitude, browser_longitude):
    # Forecasting
    forecast_url = f"https://api.tomtom.com/weatherforecast/v1/hourly?lat={browser_latitude}&lon={browser_longitude}&forecastHours=24&key={os.getenv('TOMTOM_API_KEY')}"

    forecast_data = requests.get(forecast_url)

    if forecast_data.status_code == 200:
        forecast_data = forecast_data.json()

    print(forecast_data)

    return forecast_data

@app.route('/', methods =["GET", "POST"])
def index():
    if request.method == "POST":
       browser_latitude = request.form.get("browser_latitude")
       browser_longitude = request.form.get("browser_longitude")

       geocode_data = getBrowserLocation(browser_latitude=browser_latitude, 
       browser_longitude=browser_longitude)
             
       df = pd.DataFrame(geocode_data)

       # print(df)
       """
       try: 
            ###############################
            df = df[[
                'street',
                'adminArea5',
                'adminArea4',
                'adminArea3',
                'adminArea1',
                'postalCode',
                ]].copy()
            
            df.rename(columns={
                'street': 'Street', 
                'adminArea5': 'City',
                'adminArea4': 'County',
                'adminArea3': 'State',
                'adminArea1': 'Country',
                'postalCode': 'Zip Code'
                }, inplace=True)
                ###############################
       except Exception as e:
           print(e)

       """

       # Starting Map of User Location
       map = folium.Map(location=[browser_latitude, browser_longitude], tiles='Stamen Terrain', zoom_start=12)

       folium.Marker(
            [browser_latitude, browser_longitude], popup="<i>Home Location</i>", 
        ).add_to(map)
       
       # Starting to add road conditions
       reply, points = creatingFoliumMap(browser_latitude=browser_latitude, browser_longitude=browser_longitude)
       
       folium.PolyLine(points, color='green', weight=10).add_to(map)

       # Plotting data from dataframes
       data = pd.DataFrame({
            'lon':[-58, 2, 145, 30.32, -4.03, -73.57, 36.82, -38.5],
            'lat':[-34, 49, -38, 59.93, 5.33, 45.52, -1.29, -12.97],
            'name':['Buenos Aires', 'Paris', 'melbourne', 'St Petersbourg', 'Abidjan', 'Montreal', 'Nairobi', 'Salvador'],
            'value':[10, 12, 40, 70, 23, 43, 100, 43]
        }, dtype=str)

       for i in range(0,len(data)):
            folium.Marker(
                location=[data.iloc[i]['lat'], data.iloc[i]['lon']],
                popup=data.iloc[i]['name'],
            ).add_to(map)
            
       current_weather = getCurrentWeather(browser_latitude=browser_latitude, browser_longitude=browser_longitude)

       forecast_weather = getForecastWeather(browser_latitude=browser_latitude, browser_longitude=browser_longitude)

       return render_template("index.html", map = map, browser_latitude = browser_latitude, browser_longitude = browser_longitude, reply = reply, geocode_data = geocode_data, current_weather = current_weather, forecast_weather = forecast_weather)   

    return render_template("index.html")

if __name__=='__main__':
   app.run(debug=True)