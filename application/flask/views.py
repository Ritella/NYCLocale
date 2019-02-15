from flask import Flask, request, render_template 
from flaskexample import app
# other modules
import gmaps
import gmaps.datasets
import pandas as pd
import geopandas as gpd
from ipywidgets.embed import embed_minimal_html
import json
import geocoder
from shapely.geometry import Point
import numpy as np
import os

@app.before_first_request
def make_the_base_map():
    # set constants
    main_path = 'data'
    global api_key
    api_key = open(main_path + '/config.py', 'r')
    api_key = api_key.read().replace('api_key = ',
            '').replace('“','').replace('”','')
    gmaps.configure(api_key=api_key) # Your Google API key

    # get information
    df = pd.read_csv(main_path + '/nyc_blk_map_with_vals_for_front_end_FILTERED.csv')
    with open(main_path + '/BoroughBoundaries.geojson') as f:
        geometry = json.load(f)
    global nbhd_map
    nbhd_map = gpd.read_file(main_path + '/nyc_nbhd_map.shp')

    # Control the display
    global new_york_coordinates
    new_york_coordinates = (40.75, -73.9)
    heatmap_gradient = [
        (250, 185, 123, 0),
        'yellow',
        (249, 127, 77, 1),
        'red',
    ]

    # define layers
    global geojson_layer
    global heatmap_layer
    geojson_layer = gmaps.geojson_layer(geometry, fill_color=(0,0,0,0), 
            fill_opacity=1, stroke_weight=0.5)
    heatmap_layer = gmaps.heatmap_layer(df[['latitude', 'longitude']], 
            weights=df['magnitude'], max_intensity=10, 
            point_radius=0.00075, opacity=1, gradient=heatmap_gradient,
            dissipating=False)

@app.route('/')
@app.route('/index')
@app.route('/home')
@app.route('/input')
def map_input():
    # make the figure
    global fig
    fig = gmaps.figure(center=new_york_coordinates, zoom_level=10)
    fig.add_layer(geojson_layer)
    fig.add_layer(heatmap_layer)

    # make the html file
    embed_minimal_html('flaskexample/templates/export.html', views=[fig])
    
    # flask code to render index file
    return render_template("input.html")

@app.route('/output')
def map_output():
    # get address info
    user_input = request.args.get('input_address')
    address = user_input
    address += "; NY"
    address_coords = geocoder.google(address,
                             key=api_key)
    address_point_df = pd.DataFrame(data={'geometry': \
            [Point(address_coords.latlng[1], address_coords.latlng[0])]})
    address_point_map = gpd.GeoDataFrame(address_point_df, 
            geometry='geometry', crs=nbhd_map.crs)
    combined = gpd.tools.sjoin(address_point_map, nbhd_map, how='left')
    if combined.isna().loc[0,'Neighborho']:
        return render_template("error.html")
    else:
        address_dict = [{'input_address': user_input, 
            'nbhd': combined.loc[0, 'Neighborho'],
            'location': (address_coords.latlng[0], address_coords.latlng[1])}]
        info_box_template = """
        <dl>
        <dt>Address</dt><dd>{input_address}</dd>
        <dt>Neighborhood</dt><dd>{nbhd}</dd>
        </dl>
        """
        address_info = [info_box_template.format(**address) for address in address_dict]
        address_location = [address['location'] for address in address_dict]
        marker_layer = gmaps.marker_layer(address_location, 
            info_box_content=address_info,
            hover_text='Click for Information')
    
        # add to the figure
        fig.add_layer(marker_layer)
    
        # make the html map file
        embed_minimal_html('flaskexample/templates/export_marker.html', views=[fig])

        # flask code to render output file
        return render_template("output.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")
