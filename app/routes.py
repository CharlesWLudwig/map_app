from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import folium
from folium import plugins
from datetime import datetime
import pandas as pd
from .config import ConfigClass
import json
from .models import User
from .functions import creatingFoliumMap, getBrowserLocation, getCurrentWeather, convert_latlon_geojson
from app import app, db

@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = []

    return render_template('profile.html', title='Home', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Username or password not found')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('profile')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/landingpage')
def landingpage():
    return render_template('landingpage.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
@login_required
def profile_post():
    user = "user"

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
