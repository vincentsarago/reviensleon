#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import time
from osgeo import ogr, osr
from urllib2 import urlopen
import bs4 as BeautifulSoup
from boto3.session import Session
from geopy.geocoders import Nominatim

#AWS S3 Account Informations
session = Session(aws_access_key_id='',
                  aws_secret_access_key='',
                  region_name='')

driver = ogr.GetDriverByName('GeoJSON')
outjson = '/tmp/reviensleon.geojson'
if os.path.isfile(outjson):
    os.remove(outjson)

json_ds = driver.CreateDataSource(outjson)
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)

layer = json_ds.CreateLayer('jobs', srs, geom_type=ogr.wkbPoint)
layer.CreateField(ogr.FieldDefn("titre", ogr.OFTString))
layer.CreateField(ogr.FieldDefn("employeur", ogr.OFTString))
layer.CreateField(ogr.FieldDefn("link", ogr.OFTString))
layer.CreateField(ogr.FieldDefn("place", ogr.OFTString))
defn = layer.GetLayerDefn()

geolocator = Nominatim()
off = 0
while True:
    html = urlopen('http://www.reviensleon.com/Postuler/Offres-Start-ups/(offset)/{}'.format(off)).read().decode('utf-8')
    soup = BeautifulSoup.BeautifulSoup(html, "html.parser")
    offres = soup.find('div', attrs={"class": "liste-offres page-listing-offre"}).find_all('article')
    if len(offres) == 0:
        break

    for o in offres:
        ep = (o.find("p", attrs={"class":"mt10"}).text).split(' / ')
        place = ep[1] if len(ep) == 2 else ''
        lat = 0
        lon = 0
        if place != '':
            print(place)
            try:
                location = geolocator.geocode(place)
            except:
                print("Geopy Error for {}".format(place))
            if location:
                lat = location.latitude
                lon = location.longitude
            time.sleep(1) #sleep 1 sec to not overcall Nominatim

        feature = ogr.Feature(defn)
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature.SetGeometry(point)

        a = o.find("a", attrs={"class":"gaOffre"})
        titre = a.get("title").encode('utf-8')
        employeur = a.get("data-employeur").encode('utf-8')
        link = a.get("href").encode('utf-8')

        feature.SetField("titre", titre)
        feature.SetField("employeur", employeur)
        feature.SetField("link", link)
        feature.SetField("place", place.encode('utf-8'))
        layer.CreateFeature(feature)

    del soup
    off += 16

layer = None
json_ds.Destroy()

#Upload image to S3
if os.path.exists(outjson):
    s3 = session.resource('s3')
    fname = 'data/{}'.format(os.path.basename(outjson))
    s3.Bucket('remotepixel').upload_file(outjson, fname, ExtraArgs={'ACL': 'public-read'})
    print("file uploaded to AWS S3")
