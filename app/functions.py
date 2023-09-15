from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from shapely.geometry import Point as Shapely_point, mapping
from geojson import Point as Geoj_point, Polygon as Geoj_polygon, Feature, FeatureCollection
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

        print(geocode_data_pop)

        webcams_api_key = os.getenv("WEBCAMS_API_KEY")

        webcams_api_host = os.getenv("WEBCAMS_API_HOST")
        
        url = f"https://webcamstravel.p.rapidapi.com/webcams/list/nearby=%7{browser_latitude}%7D,%7{browser_longitude}%7D,%7Bradius%7D"

        params = {
            "show":"webcams:image,location",
            "lang":"en"
        }

        headers = {
            "X-RapidAPI-Key": webcams_api_key,
            "X-RapidAPI-Host": webcams_api_host
        }

        response = requests.get(url, headers=headers, params=params)

        print(response.json())

    return geocode_data_info

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

def convert_latlon_geojson(browser_latitude, browser_longitude):
    buffer_geocircle_distance = 1.0
    
    error_response = {}

    #is lon valid and numeric or not
    try:
        browser_longitude = float(browser_longitude)
    except ValueError:
        error_response['longitude error'] = 'longitude argument should be numeric'
        error_response['value given'] = browser_longitude
        return jsonify(error_response)

    # is lon in or out of range
    if browser_longitude < -180.0 or browser_longitude > 180.0:
        error_response['longitude error'] = 'longitude argument value out of range'
        error_response['value given'] = browser_longitude
        return jsonify(error_response)

    #is lat valid and numeric or not
    try:
        browser_latitude = float(browser_latitude)
    except ValueError:
        error_response['latitude error'] = 'latitude argument should be numeric'
        error_response['value given'] = browser_latitude
        return jsonify(error_response)

    # is lat in or out of range
    if browser_latitude < -90.0 or browser_latitude > 90.0:
        error_response['latitude error'] = 'latitude argument value out of range'
        error_response['value given'] = browser_latitude
        return jsonify(error_response)

    # check to see if buffer_geocircle_distance argument is numeric and valid
    try:
        buffer_geocircle_distance = float(buffer_geocircle_distance)
    except ValueError:
        error_response['buffer distance error'] = 'buffer_geocircle_distance argument should be numeric'
        error_response['value given'] = buffer_geocircle_distance
        return jsonify(error_response)

    # is lat in or out of range
    if buffer_geocircle_distance < -0.001 or buffer_geocircle_distance > 100:
        error_response['buffer distance error'] = 'buffer_geocircle_distance argument value out of range'
        error_response['value given'] = buffer_geocircle_distance
        return jsonify(error_response)

    # Choose a shapely point
    shapely_point = Shapely_point(browser_longitude, browser_latitude)
    
    # use SHapely buffer function to create Shapely point to create a buffer polygon
    shapely_point_buffer = shapely_point.buffer(buffer_geocircle_distance / 111)
    #use Shapely mapping function to create a dictionary from polygon object [type, coordinate]
    shapely_point_buff_dict = mapping(shapely_point_buffer)
    # get the coordinates from the dictionary
    shapely_point_buff_coords = shapely_point_buff_dict['coordinates']

    # use the geojson library to create two features (a point and its buffer)
    point_feature = Feature(geometry=Geoj_point((browser_longitude, browser_latitude)))

    point_feature['properties']['name'] = 'API Point'
    point_feature['properties']['marker-color'] = 'red'

    # buffer polygon, colored blue 
    poly_feature = Feature(geometry=Geoj_polygon(shapely_point_buff_coords))
    poly_feature['properties']['name'] = "API point buffer"
    poly_feature['properties']['stroke'] = 'blue'
    poly_feature['properties']['fill'] = 'blue'
    poly_feature['properties']['fill-capacity'] = 0.3

    # create a feature collection with polgyon and point
    feature_col_res = FeatureCollection([point_feature, poly_feature])

    # return jsonify(feature_col_res)
    # json_endpoint = jsonify(feature_col_res)
    json_endpoint = json.dumps(feature_col_res)

    return json_endpoint

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

    return weather_dict

def getStateAlerts(state):
    alerts_url = f"https://api.weather.gov/alerts/active?area={state}"

    alerts_response = requests.get(alerts_url)

    if alerts_response.status_code == 200:
        alerts_response_json = alerts_response.json()

    return alerts_response_json