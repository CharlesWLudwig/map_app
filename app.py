from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from shapely.geometry import Point as Shapely_point, mapping
from geojson import Point as Geoj_point, Polygon as Geoj_polygon, Feature, FeatureCollection
import folium
from folium import plugins
import pandas as pd
import numpy as np
import re, os
from pprint import pprint
import random
import requests
import json
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your secret key'
app.config['JSON_SORT_KEYS'] = False

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

"""
def getForecastWeather(browser_latitude, browser_longitude):
    # Forecasting
    forecast_url = f"https://api.tomtom.com/weatherforecast/v1/hourly?lat={browser_latitude}&lon={browser_longitude}&forecastHours=24&key={os.getenv('TOMTOM_API_KEY')}"

    forecast_data = requests.get(forecast_url)

    if forecast_data.status_code == 200:
        forecast_data = forecast_data.json()

    print(forecast_data)

    return forecast_data
"""

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

@app.route('/')
def index_get():
    # Starting Map of User Location
    map = folium.Map(location=[0, 0], tiles='Stamen Terrain', zoom_start=12)

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
        
    return render_template("index.html", map = map)   

@app.route('/', methods = ["POST"])
def index_post():
    if request.method == "POST":      
       browser_latitude = request.form.get("browser_latitude")
       browser_longitude = request.form.get("browser_longitude")

       # Starting Map of User Location
       map = folium.Map(location=[browser_latitude, browser_longitude], tiles='Stamen Terrain', zoom_start=12)

       geojson_data = convert_latlon_geojson(browser_latitude=browser_latitude, 
       browser_longitude=browser_longitude)

       folium.GeoJson(geojson_data, name="geojson").add_to(map)

       folium.LayerControl().add_to(map)

       json_df = pd.read_json(geojson_data)   
       json_result = json_df.to_json(orient='records')
       parsed = json.loads(json_result)
       json_out = json.dumps(parsed, indent=4)

       # Send to PostGres Database
#       with open('json_out.json', 'w') as outfile:
#            outfile.write(json_out)

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

       return render_template("index.html", map = map, browser_latitude = browser_latitude, browser_longitude = browser_longitude, reply = reply, geocode_data = geocode_data, current_weather = current_weather, geojson_data = geojson_data, json_result = json_result)   

    return redirect(url_for('index_get')) 

"""
@app.route("/api/country", methods=["GET"])
def get_all_countries():
    if connection_records:
        result = []      
        for record in connection_records:
            print(record)

        return jsonify(connection_records)
    
        for record in connection_records:
            print(record)
            result.append({
                'country': record[0],
                'latitude': record[1],
                'longitude': record[2],
                'name': record[3]})        
        return jsonify(result)
    else:
        return jsonify({"error": f"country not found."}), 404       
"""

if __name__ == '__main__':
   app.run(debug=True)