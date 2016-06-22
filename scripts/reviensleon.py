#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import json
from urllib2 import urlopen
import bs4 as BeautifulSoup
from geopy.geocoders import Nominatim
from osgeo import ogr, osr

driver = ogr.GetDriverByName('GeoJSON')
outjson = 'reviensleon.geojson'
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
        if place != '':
            location = geolocator.geocode(place)
            lat = location.latitude
            lon = location.longitude
        else:
            lat = 0
            lon = 0

        feature = ogr.Feature(defn)
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature.SetGeometry(point)

        a = o.find("a", attrs={"class":"gaOffre"})
        titre = a.get("title").encode('utf-8')
        employeur = a.get("data-employeur").encode('utf-8')
        link = a.get("href").encode('utf-8')

        feature.SetField('titre', titre)
        feature.SetField('employeur', employeur)
        feature.SetField('link', link)
        feature.SetField('place', place)
        layer.CreateFeature(feature)

    del soup
    off += 16

layer = None
json_ds.Destroy()

# loclist = 'list.json'
# with open(loclist, 'w') as fp:
#     json.dump(res, fp, indent = 4, separators = (',', ': '), ensure_ascii=False)
