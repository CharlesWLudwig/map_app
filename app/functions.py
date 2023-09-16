from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pprint import pprint
from flask_sqlalchemy import SQLAlchemy
import folium
from folium import plugins
import pandas as pd
import numpy as np
import os
import random
import requests
import json

def creatingFoliumMap(browser_latitude, browser_longitude):  
    reply = {} 

    params = {'point': f'{browser_latitude},{browser_longitude}',  
            'unit': 'mph', 'thickness': 14, 
            'key': os.getenv('TOMTOM_API_KEY')}
    
    base_url = 'https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json'
    
    data = requests.get(base_url, params=params)
    
    data = data.json()

    road_types = {'FRC0': 'Motorway', 'FRC1': 'Major road', 'FRC2': 'Other major road', 'FRC3': 'Secondary road',
                'FRC4': 'Local connecting road', 'FRC5': 'Local road of high importance', 'FRC6': 'Local road'}

    if data['flowSegmentData']['roadClosure']:
        reply['road_closure'] = 'The road is closed!'
    else:
        reply['road type'] = road_types[data['flowSegmentData']['frc']]
        reply['road speed'] = f"{data['flowSegmentData']['currentSpeed']} mph"
        reply['road speed time'] = f"{data['flowSegmentData']['currentTravelTime']} seconds to pass"

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
        
        adminArea1 = geocode_data_info[0]['adminArea1']
        adminArea3 = geocode_data_info[0]['adminArea3']
        postalcode = geocode_data_info[0]['postalCode']
        """
        browserLat = geocode_data_info[0]['displayLatLng']['lat']
        browserLng = geocode_data_info[0]['displayLatLng']['lng']
        roadMetadata = geocode_data_info[0]['roadMetadata']
        roadSpeedLimit = geocode_data_info[0]['roadMetadata']['speedLimit']
        roadSpeedLimitUnits = geocode_data_info[0]['roadMetadata']['speedLimitUnits']
        tollRoad = geocode_data_info[0]['roadMetadata']['tollRoad']
        """
        geocode_data_pop = {
            "country": adminArea1, 
            "state": adminArea3, 
            "postal_code": postalcode,
        }

        webcams_api_key = os.getenv("WEBCAMS_API_KEY")

        webcams_api_host = os.getenv("WEBCAMS_API_HOST")

        webcam_url = f"https://api.windy.com/webcams/api/v3/webcams?lang=en&limit=50&offset=0&sortKey=popularity&sortDirection=desc&nearby={browser_latitude}%2C{browser_longitude}%2C250&include=categories,images,location,player,urls&categories=landscape,traffic,meteo,building,indoor,city,water,airport,square,sportarea"

        headers = {
            "x-windy-api-key": webcams_api_key,
            'Accept': "application/json"
        }

        webcam_response = requests.get(webcam_url, headers=headers)

        if webcam_response.status_code == 200:
            webcam_dict_response = webcam_response.json()

            print("WEBCAM RESPONSE")
            print(webcam_dict_response)

    return geocode_data_info, webcam_dict_response
"""
def getCurrentWeather(browser_latitude, browser_longitude):
    mapquest_api = os.getenv('OPENWEATHER_API')

    reply = {}

    # Reverse geocode browser longitude and latitude to an address
    weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat={browser_latitude}&lon={browser_longitude}&units=imperial&appid={mapquest_api}'

    weather_data = requests.get(weather_url)

    if weather_data.status_code == 200:
        weather_data = weather_data.json()

    reply['description'] = weather_data['weather'][0]['description']
    reply['temperature'] = weather_data['main']['temp'] 
    reply['feeling'] =weather_data['main']['feels_like']
    reply['sunrise time'] = weather_data['sys']['sunrise']
    reply['sunset time'] = weather_data['sys']['sunset']

    return reply
    """

def getWeatherForecast(browser_latitude, browser_longitude):
    """
    NOAA
    forecast - forecast for 12h periods over the next seven days
    forecastHourly - forecast for hourly periods over the next seven days
    forecastGridData - raw forecast data over the next seven days
    """

    weather_url = f"https://api.weather.gov/points/{browser_latitude},{browser_longitude}"

    response = requests.get(weather_url)

    if response.status_code == 200:
        weather_resp = response.json()
        weather_dict = {}

    for i in weather_resp['properties']:
        weather_dict[i] = weather_resp['properties'][i]

    future_url = weather_dict['forecast']

    response = requests.get(future_url)
    if response.status_code == 200:
        daily_dict = {}

        future_data = response.json()

    for i in future_data['properties']:
        daily_dict[i] = future_data['properties'][i]
    
    forecast_dict = {}

    for i in daily_dict['periods']:
        forecast_dict[f"{i['name']}"] = i

    return weather_dict, forecast_dict

def getStateAlerts(state):
    alerts_url = f"https://api.weather.gov/alerts/active?area={state}"

    alerts_response = requests.get(alerts_url)

    if alerts_response.status_code == 200:
        alerts_response_json = alerts_response.json()

    return alerts_response_json