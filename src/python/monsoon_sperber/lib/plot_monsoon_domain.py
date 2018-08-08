from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

def draw_screen_poly( lats, lons, m):
    x, y = m( lons, lats )
    xy = zip(x,y)
    poly = Polygon( xy, facecolor='red', alpha=0.4, edgecolor='red', linewidth=2)
    plt.gca().add_patch(poly)

lats = {}
lons = {}

lats['AIR'] = [ 7, 25, 25, 7 ]
lons['AIR'] = [ 65, 65, 85, 85 ]

lats['AUS'] = [ -20, -10, -10, -20 ]
lons['AUS'] = [ 120, 120, 150, 150 ]

lats['Sahel'] = [ 13, 18, 18, 13 ]
lons['Sahel'] = [ -10, -10, 10, 10 ]

lats['GoG'] = [ 0, 5, 5, 0 ]
lons['GoG'] = [ -10, -10, 10, 10 ]

lats['NAM'] = [ 20, 37, 37, 20 ]
lons['NAM'] = [ -112, -112, -103, -103 ]

lats['SAM'] = [ -20, -2.5, -2.5, -20 ]
lons['SAM'] = [ -65, -65, -40, -40 ]

regions = lats.keys()

plt.figure(figsize=(12,6))

m = Basemap(lon_0=0)
m.drawmapboundary(fill_color='aqua')
m.fillcontinents(color='grey',lake_color='aqua')
m.drawcoastlines()

for region in regions:
    draw_screen_poly( lats[region], lons[region], m )

plt.savefig('monsoon_domain_map.png')
