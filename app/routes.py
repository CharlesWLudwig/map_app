from flask import render_template, flash, redirect, url_for, request, jsonify, make_response
from icalendar import Calendar, Event as Event_Cal, vCalAddress, vText
import pytz
from pathlib import Path
import os
import openrouteservice
from openrouteservice import convert
import pandas as pd
from pprint import pprint
from datetime import datetime
from app import app, db
from app.forms import EventForm, RegistrationForm, LoginForm
import folium
from folium import plugins
from folium.elements import *
import requests
from flask_login import current_user, logout_user, login_user, login_required
from app.models import User
import json
from werkzeug.urls import url_parse

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

from app.models import Event, User

def getLatLon(street, city, state, postalcode, country):
    url = f'https://geocode.maps.co/search?street={street}&city={city}&state={state}&postalcode={postalcode}&country={country}'

    response = requests.get(url=url)

    if response.status_code == 200:
        data = response.json()
        data_dict = {}
       
        for i in data:
            data_dict['lat'] = i['lat']
            data_dict['lon'] = i['lon']
            data_dict['display_name'] = i['display_name']
           
        latitude = data_dict.get('lat', 0)                
        longitude = data_dict.get('lon', 0)
        """
        display_name = data_dict.get('display_name', 0)
        km = distance([float(latitude), float(longitude)])
        miles = distance([float(latitude), float(longitude)]).miles"""
       # print(latitude, longitude)

        return latitude, longitude

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def home():
    traffic_key = os.getenv('TRAFFIC_KEY')

    return render_template("home.html", traffic_key = traffic_key)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('get_events'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Username or password not found')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('get_events')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('get_events'))
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

@app.route('/events', methods=['GET'])
@login_required
def get_events():
    if current_user.is_authenticated:       
        form = EventForm()
        
        events = current_user.events.all()
        
        if events is None:
            df = pd.DataFrame(
                columns=[
                    'name', 
                    'street',
                    'city', 
                    'state',
                    'country', 
                    'type',
                    'postalcode', 
                    'duration',
                ]
            )
            
            df['latitude'] = ''
            df['longitude'] = ''

        else: 
            df = pd.DataFrame(
                [(
                    e.event_name,
                    e.event_street,
                    e.event_city,
                    e.event_state,
                    e.event_country,
                    e.event_type, 
                    e.event_postalcode, 
                    e.event_latitude, 
                    e.event_longitude,
                    e.event_duration
                    ) 
                    for e in events
                ], 
                columns=[
                    'name', 
                    'street',
                    'city', 
                    'state',
                    'country', 
                    'type',
                    'postalcode',
                    'latitude',
                    'longitude',
                    'duration',
                ]
            )
            
        if not df.empty:
            return render_template("event.html", events=events, form = form, user = current_user)
        else:
            return render_template("event.html", events=events, form = form, user = current_user)
    else:
        return redirect(url_for('login'))  

@app.route('/events/create', methods=['POST'])
@login_required
def create():
    form = EventForm()
    global value

    if form.validate_on_submit():
        print(f"Starting data Value : {form.adding.data}")
        print(f"Ending data Value : {form.updating.data}")

        flash(
            f"You submitted name {form.event_name.data} via button {'Adding' if form.adding.data else 'Updating'}")
           
        if form.adding.data:

            user = User.query.filter_by(username=current_user.username).first_or_404()
            events = user.events.all()
            
            event = Event.query.filter_by(event_name=form.event_name.data).first()

            if event not in events:   
                function_latitude, function_longitude = getLatLon(
                    street = form.event_street.data,
                    city = form.event_city.data,
                    state = form.event_state.data,
                    country = form.event_country.data,
                    postalcode = form.event_postalcode.data,
                )

                event = Event(
                    event_name = form.event_name.data, 
                    event_street = form.event_street.data,
                    event_city = form.event_city.data,
                    event_state = form.event_state.data,
                    event_country = form.event_country.data,
                    event_type = form.event_type.data,
                    event_time = form.event_time.data.strftime('%I:%M %p'),
                    event_date = form.event_date.data.strftime('%Y-%m-%d'),
                    event_postalcode = form.event_postalcode.data,
                    event_latitude = function_latitude, 
                    event_longitude = function_longitude, 
                    event_duration = form.event_duration.data,
                    scheduler=current_user
                )

                db.session.add(event)
                db.session.commit()
            else:
                pass
        
            return redirect(url_for('get_events'))
        
        elif form.updating.data:
            user = User.query.filter_by(username=current_user.username).first_or_404()
            
            events = user.events.all()

            event = Event.query.filter_by(event_name=form.event_name.data).first()

            if event in events:   
                function_latitude, function_longitude = getLatLon(
                    street = form.event_street.data,
                    city = form.event_city.data,
                    state = form.event_state.data,
                    country = form.event_country.data,
                    postalcode = form.event_postalcode.data,
                )

                event.event_name = form.event_name.data 
                event.event_street = form.event_street.data
                event.event_city = form.event_city.data
                event.event_state = form.event_state.data
                event.event_country = form.event_country.data
                event.event_type = form.event_type.data
                event.event_time = form.event_time.data.strftime('%I:%M %p')
                event.event_date = form.event_date.data.strftime('%Y-%m-%d')
                event.event_postalcode = form.event_postalcode.data
                event.event_latitude = function_latitude 
                event.event_longitude = function_longitude 
                event.event_duration = form.event_duration.data   
                event.scheduler = current_user

            db.session.commit()

            return redirect(url_for('get_events'))

        else:
            pass

    if form.errors:
        for error_field, error_message in form.errors.items():
            flash(f"Field : {error_field}; error : {error_message}")

    return redirect(url_for('get_events'))

@app.route("/events/cameras/<int:id>")
@login_required
def cameras(id):
    if current_user.is_authenticated:
        event = Event.query.filter_by(id=id).first()      
        traffic_key = os.getenv('TRAFFIC_KEY')

        event_id = event.id
        event_name = event.event_name
        latitude = event.event_latitude
        longitude = event.event_longitude

        return render_template("traffic.html", event_latitude = latitude, event_id = event_id, event_longitude = longitude, event_name = event_name, traffic_key = traffic_key)

@app.route("/events/forecast/<int:id>", methods=['GET', 'POST'])
@login_required
def forecast(id):
    if current_user.is_authenticated:
        event = Event.query.filter_by(id=id).first()

        """
        NOAA
        forecast - forecast for 12h periods over the next seven days
        forecastHourly - forecast for hourly periods over the next seven days
        forecastGridData - raw forecast data over the next seven days
        """
        latitude = event.event_latitude
        longitude = event.event_longitude
        event_id = event.id
        event_name = event.event_name
        event_street = event.event_street
        event_city = event.event_city
        event_state = event.event_state
        event_country = event.event_country
        event_latitude = event.event_latitude
        event_longitude = event.event_longitude
        event_postalcode = event.event_postalcode
        
        weather_url = f"https://api.weather.gov/points/{latitude},{longitude}"

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

        day_dict = {}
        night_dict = {}
        
        for key, value in forecast_dict.items():
            if 'Night' in key:
                night_dict[key] = value
            elif 'night' in key:
                night_dict[key] = value
            else:
                day_dict[key] = value
       
        map = folium.Map(location=[latitude, longitude], zoom_start=6)

        folium.GeoJson(
            weather_dict['fireWeatherZone'],
            name='Fire Zones'
        ).add_to(map)

        folium.GeoJson(
            weather_dict['county'], 
            name='county'
        ).add_to(map)

        folium.GeoJson(
            weather_dict['observationStations'],
            marker = folium.CircleMarker(
            radius = 8,
            weight = 5,
            fill_color = 'yellow', 
            fill_opacity = 1),
            tooltip = folium.GeoJsonTooltip(fields = [
                'stationIdentifier', 
                'name',
                ],              
            aliases=[
                'Station: ', 
                'Location: ',
                ],
            # popup = f'<b>{weather_dict["observationStations"]["@id"][-4:]}</b>',
            sticky = True),
            name='Observation Stations'
            ).add_to(map)     

        folium.GeoJson(
            weather_dict['forecastZone'], 
            name='Forecast Zone'
        ).add_to(map)

        folium.Marker(
            [latitude, longitude], 
            name='My Location', 
            popup=f"""
                    <div style="width: 100px; text-align: center; font-weight: 600;">
                    <i>
                    <p>{event_name}</p>
                    <p>{event_street}</p>
                    <p>{event_city}</p>
                    <p>{event_state}</p>
                    <p>{event_country}</p>
                    <p>{event_postalcode}</p>
                   </i>
                   </div>"""
        ).add_to(map)

        # Getting the Forecasting Office 
        forecast_office_url = f"{weather_dict['forecastOffice']}"
        response = requests.get(forecast_office_url)

        if response.status_code == 200:
            forecastOfficeAddress = response.json()
           
            response = requests.get(forecastOfficeAddress['parentOrganization'])

            if response.status_code == 200:
                parentOfficeAddress = response.json()            

                parent_office_dict = [
                    parentOfficeAddress['address'], parentOfficeAddress['telephone'], parentOfficeAddress['email']
                ]

        forecasting_office_dict = [
            forecastOfficeAddress['address'], forecastOfficeAddress['telephone'], forecastOfficeAddress['email']
        ]

        plugins.Fullscreen(
            position = "topright",
            title = "Open full-screen map",
            title_cancel = "Close full-screen map", force_separate_button = True,
        ).add_to(map) 

        folium.CircleMarker(location=([latitude, longitude]),radius=50, fill_color='red', #popup=f'https://forecast.weather.gov/data/obhistory/{[forecastOfficeAddress["approvedObservationStations"]]}.html'
        ).add_to(map)

        folium.LayerControl(collapsed=False).add_to(map)
        
        minimap = plugins.MiniMap(position = "bottomleft")
        map.add_child(minimap)

        """        
        nearby_state_alerts = getStateAlerts(state=weather_dict['relativeLocation']['properties']['state'])

        print(nearby_state_alerts)
        """

        return render_template("weather.html", map = map, browser_latitude = latitude, browser_longitude =  longitude, forecast_dict = forecast_dict, day_dict = day_dict, night_dict = night_dict, user = current_user, office_dict = forecasting_office_dict, event_name = event_name, event_id = event_id, event_latitude = event_latitude, event_longitude = event_longitude,  parent_office_dict = parent_office_dict)   
    else:
        pass
    return redirect(url_for("get_events"))

@app.route("/events/delete/<int:id>")
@login_required
def delete(id):
    if current_user.is_authenticated:
        event = Event.query.filter_by(id=id).first()
        db.session.delete(event)
        db.session.commit()
    else:
        pass
    return redirect(url_for("get_events"))

@app.route("/events/calendar/<int:id>", methods=['GET'])
@login_required
def calendar(id):
    if current_user.is_authenticated:
        event = Event.query.filter_by(id=id).first()

        # username details
        user_name = current_user.username 
        user_email = current_user.email

        # event details
        event_id = event.id
        event_name = event.event_name
        event_street = event.event_street
        event_city = event.event_city
        event_state = event.event_state
        event_country = event.event_country
        event_type = event.event_type
        event_postalcode = event.event_postalcode
        event_duration = event.event_duration
        event_date = event.event_date
        event_time = event.event_time

        # calculating date conventions
        event_year = int(event_date[:4])
        event_month = int(event_date[5:7])
        event_day = int(event_date[-2:])

        event_cal_duration = float(event_duration)
        event_cal_hours, event_cal_minutes = str(event_cal_duration).split(".") 

        event_cal_hours = int(event_cal_hours)
        event_cal_minutes = int(event_cal_minutes)

        event_hour = int(event_time[:2])
        event_minute = int(event_time[3:5])
        event_second = 0
        # This is AM or PM (meridian designation)
        event_time_meridian = event_time[-2:]

        if event_cal_hours is not None:
            ending_event_hour = event_hour + event_cal_hours
        if event_cal_minutes is not None:
            ending_event_minute = event_minute + event_cal_minutes
            
        cal = Calendar()
        cal.add('prodid', '-//MapPy Travel Planner//mappy.com//')
        cal.add('version', '2.0')
        cal.add('attendee', f'MAILTO:{user_email}')

        event_cal = Event_Cal()
        event_cal.add('name', f'{event_name}')
        event_cal.add('description', f'{event_type}')
        event_cal.add('dtstart', datetime(event_year, event_month, event_day, event_hour, event_minute, event_second, tzinfo=pytz.utc))
        # print(f"datetime({event_year}, {event_month}, {event_day}, {event_hour}, {event_minute}, {event_second})")
        event_cal.add('dtend', datetime(event_year, event_month, event_day, ending_event_hour, ending_event_minute, event_second, tzinfo=pytz.utc))
        # print(f"datetime({event_year}, {event_month}, {event_day}, {ending_event_hour}, {ending_event_minute}, {event_second})")
        event_cal.add('dtstamp', datetime(event_year, event_month, event_day, ending_event_hour, ending_event_minute, event_second, tzinfo=pytz.utc))

        uid = datetime(event_year, event_month, event_day, ending_event_hour, ending_event_minute, event_second, tzinfo=pytz.utc)
        uid = str(uid)[:-1]

        organizer = vCalAddress(f'MAILTO:{user_email}')
        organizer.params['name'] = vText(f'{user_name}')
        organizer.params['role'] = vText('Organizer')
        event_cal['uid'] = f'{uid}/{event_id}@mappy.com'
        event_cal['organizer'] = organizer
        event_cal['location'] = vText(f'{event_street}, {event_city}, {event_state} {event_postalcode}, {event_country}')

        cal.add_component(event_cal)
        
        response = make_response(cal.to_ical())
        response.headers["Content-Disposition"] = f"attachment; filename={event_name}.ics"

        return response
    
    return redirect(url_for('get_events'))
