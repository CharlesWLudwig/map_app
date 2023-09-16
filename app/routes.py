from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pprint import pprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests
from .forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import folium
from folium import plugins
from folium.elements import *
from datetime import datetime
import pandas as pd
from .config import ConfigClass
import json
from .models import User
from .functions import creatingFoliumMap, getBrowserLocation, getStateAlerts, getWeatherForecast
from app import app, db

@app.route('/home')
@login_required
def home():
    posts = []
   
    return render_template('landingpage.html', title='Home', posts=posts)

@app.route('/')
@app.route('/index')
def index():

    """
    getStateAlerts
    """
    return render_template('landingpage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile_get'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Username or password not found')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('profile_get')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        prospective_user = User(username=form.username.data, email=form.email.data)

        user = User.query.filter_by(username=prospective_user.username).first()

        email = User.query.filter_by(email=prospective_user.email).first()

        if user is not None:
            flash('Please use a different username.')
            return redirect(url_for('register'))
        
        if email is not None:
            flash('Please use a different email.')
            return redirect(url_for('register'))
        
        user = User(username=form.username.data, email=form.email.data)

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        
        flash('Thank you for registering!')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route('/profile', methods=["GET"])
@login_required
def profile_get():
    user = "user"

    # Plotting data from dataframes (main cities example)
    countries_url = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'
    response = requests.get(countries_url)
    data = response.json()

    map = folium.Map(location=[0, 0], zoom_start=2)

    folium.GeoJson(data).add_to(map)
           
    return render_template("profile.html", map = map, user=user)   

@app.route('/profile', methods = ["POST"])
@login_required
def profile_post():
    user = "user"

    if request.method == "POST":      
       browser_latitude = request.form.get("browser_latitude")
       browser_longitude = request.form.get("browser_longitude")

       geocode_data, webcam_data = getBrowserLocation(browser_latitude=browser_latitude, 
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
       # Starting to add road conditions
       reply, points = creatingFoliumMap(browser_latitude=browser_latitude, browser_longitude=browser_longitude)

       weather_dict, forecast_dict = getWeatherForecast(browser_latitude=browser_latitude, browser_longitude=browser_longitude)

       day_dict = {}
       night_dict = {}
        
       for key, value in forecast_dict.items():
#          print(key)

           if 'Night' in key:
               night_dict[key] = value
           elif 'night' in key:
               night_dict[key] = value
           else:
               day_dict[key] = value
       """"
       for key in day_dict.keys():
           print(key)

       for key in night_dict.keys():
           print(key)
       """
       
       """
       print(f"GridX: {weather_dict['gridX']}")
       print(f"GridY: {weather_dict['gridY']}")         
       print(f"fireWeatherZone: {weather_dict['fireWeatherZone']}")
       print(f"ForecastOffice: {weather_dict['forecastOffice']}")
       print(f"County: {weather_dict['county']}")
       print(f"Forecast: {weather_dict['forecast']}")
       print(f"ForecastZone: {weather_dict['forecastZone']}")
       print(f"Observation Station: {weather_dict['observationStations']}")
       print(f"Forecast Hourly: {weather_dict['forecastHourly']}")
       print(f"Forecast Grid Data: {weather_dict['forecastGridData']}")
       print(f"TimeZone: {weather_dict['timeZone']}")
       print(f"Radar Station: {weather_dict['radarStation']}")
       print(f"City: {weather_dict['relativeLocation']['properties']['city']}")
       print(f"State: {weather_dict['relativeLocation']['properties']['state']}")
       print(f"Distance: {weather_dict['relativeLocation']['properties']['distance']}")
       print(f"Bearing: {weather_dict['relativeLocation']['properties']['bearing']}")
       """
       
       map = folium.Map(location=[browser_latitude, browser_longitude], zoom_start=6)

       folium.GeoJson(weather_dict['fireWeatherZone'], name='Fire Zones').add_to(map)

       folium.GeoJson(weather_dict['county'], name='county').add_to(map)

       folium.GeoJson(weather_dict['observationStations'], name='Observation Stations').add_to(map)     

       folium.GeoJson(weather_dict['forecastZone'], name='Forecast Zone').add_to(map)

       folium.Marker([browser_latitude, browser_longitude], name='My Location', popup="<i>My Location</i>").add_to(map)

#       forecastOfficeAddress = weather_dict["forecastZone"]["properties"]["forecastOffices"][0]
       # Getting the Forecasting Office 
       forecast_office_url = f"{weather_dict['forecastOffice']}"

       response = requests.get(forecast_office_url)

       if response.status_code == 200:
           forecastOfficeAddress = response.json()

           print(f"Forecast Office Address: {forecastOfficeAddress['address']}")
           print(f"Forecast Office Address: {forecastOfficeAddress['telephone']}")
           print(f"Forecast Office Address: {forecastOfficeAddress['email']}")

       folium.CircleMarker(location=([browser_latitude, browser_longitude]),radius=50, fill_color='red', popup=f'{forecastOfficeAddress}').add_to(map)

       folium.LayerControl(collapsed=False).add_to(map)
        
       minimap = plugins.MiniMap()
       map.add_child(minimap)

       nearby_state_alerts = getStateAlerts(state=weather_dict['relativeLocation']['properties']['state'])

#      print(nearby_state_alerts)
       
#      current_weather = getCurrentWeather(browser_latitude=browser_latitude, browser_longitude=browser_longitude)

       return render_template("profile.html", map = map, browser_latitude = browser_latitude, browser_longitude = browser_longitude, reply = reply, forecast_dict = forecast_dict, day_dict = day_dict, night_dict = night_dict, geocode_data = geocode_data, user=user, webcam_data = webcam_data)   

    return redirect(url_for('profile_get')) 

"""
@app.route('/baseline')
def baseline():
    return "landingpage.html"

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
"""       
       json_df = pd.read_json(f"{weather_dict['fireWeatherZone']}")   
       json_result = json_df.to_json(orient='records')
       parsed = json.loads(json_result)
       json_out = json.dumps(parsed, indent=4)

       with open('fire_data.geojson', 'w') as outfile:
            outfile.write(json_out)
"""
"""
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
"""