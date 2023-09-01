from flask import render_template, request
from app import app 

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():        
    return render_template("index.html")

@app.route('/map', methods=['GET', 'POST'])
def map():
    import folium
    import pandas as pd
    import requests
    import json
    
    tooltip = 'Click For More Info'

    # GeoCoding User Location
    street = '555+5th+Ave'
    city = 'New+York'
    state = 'NY'
    postalcode = '10017'
    country = 'US'
 
    url = f'https://geocode.maps.co/search?street={street}&city={city}&state={state}&postalcode={postalcode}&country={country}'

    resp = requests.get(url=url)

    json_str = json.dumps(resp.json()) 
    
    data = json.loads(json_str)

    print(f'Longitude {data[0]["lat"]}')
    print(f'Latitude {data[0]["lon"]}')

    browser_latitude = data[0]["lat"]
    browser_longitude = data[0]["lon"]

    m = folium.Map(location=[browser_latitude, browser_longitude], zoom_start=9)

    # Geo-ording website location
    folium.CircleMarker(
        location=[browser_latitude, browser_longitude],
        radius=100,
        popup='Home Base',
        color='lightblue',
        fill=True,
        fill_color='lightblue'
    ).add_to(m)

    df = pd.read_csv("app/datasets/uscities.csv")

    # Preceptron
    df = df.head(60)

    print(df.head(2))

    for index, row in df.iterrows():
        city = row['city']
        city_ascii = row['city_ascii']
        state_id = row['state_id']
        state_name = row['state_name']
        county_fips = row['county_fips']
        county_name = row['county_name']
        latitude = row['lat']
        longitude = row['lng']
        population = row['population']
        density = row['density']
        source = row['source']
        military = row['military']
        incorporated = row['incorporated']
        timezone = row['timezone']
        ranking = row['ranking']
        zips = row['zips']
        zip_codes = zips.split()
        id = row['id']

        folium.Marker([float(latitude), float(longitude)],
                    popup=f'''
                    <ul>
                        <li>City: {city}</li>
                        <li>City Ascii: {city_ascii}</li>
                        <li>State ID: {state_id}</li>
                        <li>State Name: {state_name}</li>
                        <li>County Flips: {county_fips}</li>
                        <li>County Name: {county_name}</li>
                        <li>Latitude: {latitude}</li>
                        <li>Longitude: {longitude}</li>
                        <li>Population: {population}</li>
                        <li>Density: {density}</li>
                        <li>Source: {source}</li>
                        <li>Military: {military}</li>
                        <li>Incorporated: {incorporated}</li>
                        <li>Timezone: {timezone}</li>
                        <li>Ranking: {ranking}</li>
                        <li>Zip Codes: {zip_codes[0]} - {zip_codes[-1]}</li>
                        <li>ID: {id}</li>
                    </u>    
                    ''',
                    tooltip=tooltip,
                    icon=folium.Icon(icon='cloud')).add_to(m)        

    return m._repr_html_()