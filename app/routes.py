from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .forms import LoginForm
from flask_login import LoginManager
import folium
from folium import plugins
from datetime import datetime
import pandas as pd
from app.config import ConfigClass
import json
from .functions import creatingFoliumMap, getBrowserLocation, getCurrentWeather, convert_latlon_geojson
from app import app

@app.route('/')
@app.route('/index')
def index():
    user = ""
    posts = []
    
    return render_template('index.html', title='Home', user=user, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Login requested for user {form.username.data}, remember_me={form.remember_me.data}')
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/profile', methods=["GET"])
def profile_get():
    user="Charles"

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
        
    return render_template("profile.html", map = map, user=user)   

@app.route('/profile', methods = ["POST"])
def profile_post():
    user = "Charles"

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

       return render_template("profile.html", map = map, browser_latitude = browser_latitude, browser_longitude = browser_longitude, reply = reply, geocode_data = geocode_data, current_weather = current_weather, geojson_data = geojson_data, json_result = json_result, user=user)   

    return redirect(url_for('profile')) 

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
