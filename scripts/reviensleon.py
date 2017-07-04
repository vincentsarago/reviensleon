import os
import json

from geopy.geocoders import Nominatim
from algoliasearch import algoliasearch

geolocator = Nominatim()

API_url = 'https://csekhvms53-dsn.algolia.net'

app_id = os.environ.get('APPLICATION_ID')
app_key = os.environ.get('APPLICATION_KEY')

geojson = {"type": "FeatureCollection", "features": []}

client = algoliasearch.Client(app_id, app_key)

index = client.init_index("wk_jobs_production")
offres = index.browse_all({"query": ""})

knw_place = {}

for offre in offres:

    try:
        titre = offre['name']
        employeur = offre['company_name']
        place = offre['office']
        link = offre['websites_urls'][0]['url']

        lat = 0
        lon = 0
        if place != '':
            if place in knw_place.keys():
                lat = knw_place[place]['lat']
                lon = knw_place[place]['lon']
            else:
                try:
                    location = geolocator.geocode(place)
                except:
                    print("Geopy Error for {}".format(place))

                if location:
                    lat = location.latitude
                    lon = location.longitude
                    knw_place[place] = {}
                    knw_place[place]['lat'] = lat
                    knw_place[place]['lon']  = lon


            feature = {
                "type": "Feature",
                "properties": {
                    "titre": "",
                    "employeur": "",
                    "place": "",
                    "link": ""
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": []
                }
            }

            feature["geometry"]["coordinates"] = [lon, lat, 0]
            feature["properties"]["titre"] = titre
            feature["properties"]["employeur"] = employeur
            feature["properties"]["link"] = link
            feature["properties"]["place"] = place
            geojson["features"].append(feature)
    except:
        print(offre)

with open('reviensleon.geojson', 'w') as f:
    json.dump(geojson, f)
