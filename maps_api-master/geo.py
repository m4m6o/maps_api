import requests

def reverse_geocode(ll):
    grt = "http://geocode-maps.yandex.ru/1.x/?geocode={ll}&format=json"
    geocoder_request_template = grt
    geocoder_request = geocoder_request_template.format(**locals())
    response = requests.get(geocoder_request)
    if not response:
        raise RuntimeError(
            """Error:{request}
               http: {status} ({reason})""".format(request=geocoder_request, 
                                                   status=response.status_code, 
                                                   reason=response.reason))
    json_response = response.json()
    features = json_response["response"]["GeoObjectCollection"]["featureMember"]
    if features:
        return features[0]["GeoObject"]
    else:
        return None

