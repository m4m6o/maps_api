import pygame
import requests
import sys
import os
import math
from distance import lonlat_distance
from geo import reverse_geocode
from bis import find_business

LAT_STEP = 0.008
LON_STEP = 0.02
coord_to_geo_x = 0.0000428
coord_to_geo_y = 0.0000428
zoom = 17
router_mode = True
lb = False
points = []

def ll(x, y):
    return "{0},{1}".format(x, y)


class SearchResult(object):
    def __init__(self, point, address, postal_code=None):
        self.point = point
        self.address = address
        self.postal_code = postal_code

class MapParams(object):
    global zoom, router_mode, x1, x2, y1, y2
    def __init__(self):
        self.lat = 43.231171
        self.lon = 76.917695
        self.zoom = zoom
        self.type = "map"

        self.search_result = None
        self.use_postal_code = False

    def ll(self):
        return ll(self.lon, self.lat)

    def update(self, event):
        if event.key == 276:
            self.lon -= LON_STEP * math.pow(2, 15 - self.zoom)
        elif event.key == 275:
            self.lon += LON_STEP * math.pow(2, 15 - self.zoom)
        elif event.key == 273 and self.lat < 85:
            self.lat += LAT_STEP * math.pow(2, 15 - self.zoom)
        elif event.key == 274 and self.lat > -85:
            self.lat -= LAT_STEP * math.pow(2, 15 - self.zoom)
            
        elif event.key == 119:
            self.lat += 0.0005 * (19 - zoom) / 2
        elif event.key == 115:
            self.lat -= 0.0005 * (19 - zoom) / 2
        elif event.key == 97:
            self.lon -= 0.0005 * (19 - zoom) / 2
        elif event.key == 100:
            self.lon += 0.0005 * (19 - zoom) / 2
            
        elif event.key == 49:
            self.type = "map"
        elif event.key == 50:
            self.type = "sat"
        elif event.key == 51:
            self.type = "sat,skl"
            
        elif event.key == 269:
            self.zoom -= 1
        elif event.key == 270:
            self.zoom += 1
            
        elif event.key == 127:
            self.search_result = None
        elif event.key == 277:
            self.use_postal_code = not self.use_postal_code

        elif event.key == 114:
            router_mode = True
            
        if self.lon > 180: self.lon -= 360
        if self.lon < -180: self.lon += 360

    def screen_to_geo(self, pos):
        dy = 225 - pos[1]
        dx = pos[0] - 300
        lx = self.lon + dx * coord_to_geo_x * math.pow(2, 15 - self.zoom)
        ly = self.lat + dy * coord_to_geo_y * math.cos(math.radians(self.lat)) * math.pow(2, 15 - self.zoom)
        return lx, ly

    def add_reverse_toponym_search1(self, pos):
        point1 = self.screen_to_geo(pos)
        x1 = point1[0]
        y1 = point1[1]
        toponym1 = reverse_geocode(ll(x1, y1))
        self.search_result = SearchResult(
            point1,
            toponym1["metaDataProperty"]["GeocoderMetaData"]["text"] if toponym1 else None,
            toponym1["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code") if toponym1 else None)
        
    def add_reverse_toponym_search2(self, pos):
        point2 = self.screen_to_geo(pos)
        x2 = point2[0]
        y2 = point2[1]
        toponym2 = reverse_geocode(ll(x2, y2))
        self.search_result = SearchResult(
            point2, 
            toponym2["metaDataProperty"]["GeocoderMetaData"]["text"] if toponym2 else None, 
            toponym2["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code") if toponym2 else None)    

    def add_reverse_org_search(self, pos):
        self.search_result = None
        point = self.screen_to_geo(pos)
        org = find_business(ll(point[0], point[1]))
        if not org:
            return

        org_point = org["geometry"]["coordinates"]
        org_lon = float(org_point[0])
        org_lat = float(org_point[1])

        if lonlat_distance((org_lon, org_lat), point) <= 50:
            self.search_result = SearchResult(point, org["properties"]["CompanyMetaData"]["name"])


def load_map(mp):
    map_request = "http://static-maps.yandex.ru/1.x/?ll={ll}&z={z}&l={type}".format(ll=mp.ll(), z=mp.zoom, type=mp.type)
    if mp.search_result:
        map_request += "&pt={0},{1},flag".format(mp.search_result.point[0], mp.search_result.point[1])
    response = requests.get(map_request)
    if not response:
        print("Error:")
        print(map_request)
        print("http:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Exception:", ex)
        sys.exit(2)
    return map_file

def render_text(text):
    font = pygame.font.Font(None, 30)
    return font.render(text, 1, (100, 0, 100))

def main():
    global router_mode, x1, x2, y1, y2, pnts, points
    pygame.init()
    screen = pygame.display.set_mode((600, 450))
    mp = MapParams()
    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            break
        elif event.type == pygame.KEYUP:
            mp.update(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                router_mode = True            
                x1, y1 = event.pos
                points.append((event.pos))
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                router_mode = True
            elif event.button == 3:
                points=[]
                router_mode = False
                mp.add_reverse_toponym_search1(event.pos)           
            elif event.button == 2:
                points=[]
                router_mode = False
                mp.add_reverse_org_search(event.pos)
        elif event.type == pygame.K_1:
            pass
        elif event.type == pygame.K_2:
            pass
        elif event.type == pygame.K_3:
            pass
        elif event.type == pygame.K_4:
            pass        
        else:
            continue
        
        map_file = load_map(mp)
        screen.blit(pygame.image.load(map_file), (0, 0))
        if mp.search_result:
            if mp.use_postal_code and mp.search_result.postal_code:
                text = render_text(mp.search_result.postal_code + ", " + mp.search_result.address)
            else:
                text = render_text(mp.search_result.address)       
            screen.blit(text, (20, 400))
        if router_mode and len(points) >= 2:
            pygame.draw.polygon(screen, ((56, 176, 222)), points, 3)
            pygame.draw.line(screen, ((248, 24, 148)), points[0], points[-1], 4)
        pygame.display.flip()        
    pygame.quit()
    os.remove(map_file)


if __name__ == "__main__":
    main()
