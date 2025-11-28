import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import LineString


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FIGURES_DIR = os.path.join(PROJECT_ROOT,'data', 'reports', 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

dx = 10
dy = 10
RAIN_DEPTH = 0.1
PIXEL_AREA = 10 * 10

def gen_terrain(shape=(100, 100)):
    x = np.linspace(-5, 5, shape[0])
    y = np.linspace(-5, 5, shape[1])
    X, Y = np.meshgrid(x, y)

    np.random.seed(42)
    noise = np.random.normal(0, 5, shape)

    Z  = 1000 * np.exp(-(X**2 + Y**2)/10)+noise
    dem_data = Z # for intuitive

    plt.figure(figsize=(8, 6))
    plt.imshow(dem_data, cmap='terrain')
    plt.colorbar(label='Elevation (m)')
    plt.title('Synthetic Catchment: The Digital Elevation Model (DEM)')
    plt.savefig(os.path.join(FIGURES_DIR, 'synth_dem.png'))
    print(f"DEM of Synthetic Catchment saved at {os.path.join(FIGURES_DIR, 'synth_dem.png')}.")
    transform = from_origin(0, 0, 10, 10)

    with rasterio.open(os.path.join(FIGURES_DIR, 'synth_d.tif'
    ),
    'w',
    driver='GTiff',
    height=dem_data.shape[0],
    width=dem_data.shape[1],
    count=1,
    dtype=dem_data.dtype,
    crs='+proj=latlong',
    transform=transform,
    ) as dst:
        dst.write(dem_data, 1)
    print(f"DEM Saved to {os.path.join(FIGURES_DIR, 'synth_d.tif')}.")
    return dem_data

def anal_catch(dem_data):
    dz_dy, dz_dx = np.gradient(dem_data,dx, dy)
    aspect = np.arctan2(-dz_dy, -dz_dx)

    plt.figure(figsize=(8, 6))
    plt.imshow(aspect, cmap='hsv')
    plt.colorbar(label='Flow Direction (Radians)')
    plt.title('Where does the water go? (Aspect)')
    plt.savefig(os.path.join(FIGURES_DIR, 'flow_wheel.png'))
    print(f"Flow water direction wheel saved at {os.path.join(FIGURES_DIR, 'flow_wheel.png')}.")

    runoff_coeff = np.where(dem_data > 500, 0.9, 0.3) #hardcode

    plt.figure(figsize=(8, 6))
    plt.imshow(runoff_coeff, cmap='Greens_r') # Dark Green = Forest
    plt.colorbar(label='Runoff Coefficient (C)')
    plt.title('Land Use: Rock (Top) vs Forest (Bottom)')
    plt.savefig(os.path.join(FIGURES_DIR, 'land_use_viz.png'))
    print(f"Land Use Visualization saved at {os.path.join(FIGURES_DIR, 'land_use_viz.png')}.")

    runoff_volume = PIXEL_AREA * RAIN_DEPTH * runoff_coeff # for each pixel cuz unoff coeff diff for diff pixel
    total_rain_input = PIXEL_AREA * RAIN_DEPTH*dem_data.size
    total_runoff_volume = np.sum(runoff_volume)
    print(f"Total Rain Input: {total_rain_input:.2f} m3")
    print(f"Total Runoff Generated: {total_runoff_volume:.2f} m3")
    print(f"Volume of water Lost to Soil (Infiltration): {total_rain_input - total_runoff_volume:.2f} m3.")

    slope = np.sqrt(dz_dy**2+dz_dx**2)
    return slope


def anal_slope(dem_data, slope):
    sl_deg =  np.degrees(np.arctan(slope))
    unsafe_pixel_count = np.where(sl_deg>15, 1, 0)
    unsafe_area = unsafe_pixel_count.sum()*PIXEL_AREA
    print(f"The total unsafe area is {unsafe_area} m2.")

    road_geom = LineString([(50, 90), (50, 50)])
    length = int(road_geom.length)
    points = [road_geom.interpolate(i) for i in range(length)]
    road_slopes = []
    for p in points:
        xn, yn = int(p.x), int(p.y)
        if 0 <= yn < dem_data.shape[0] and 0 <= xn < dem_data.shape[1]:
            val = sl_deg[yn, xn]
            road_slopes.append(val)

    max_road_slope = np.max(road_slopes)
    mean_road_slope = np.mean(road_slopes)

    print(f"Max Slope on Road: {max_road_slope:.2f} degrees")
    print(f"Avg Slope on Road: {mean_road_slope:.2f} degrees")

    if max_road_slope > 15:
        print("VERDICT: ROAD UNSAFE. DO NOT BUILD.")
    else:
        print("VERDICT: ROAD APPROVED.")

    plt.figure(figsize=(8, 6))
    plt.imshow(sl_deg, cmap='Reds')
    plt.colorbar(label='Slope (Degrees)')
    xn, yn = road_geom.xy
    plt.plot(xn, yn, color='blue', linewidth=3, label='Proposed Road')
    plt.title('Route Analysis: Road vs Slope')
    plt.legend()
    plt.savefig(os.path.join(FIGURES_DIR, 'route_viz.png'))
    print(f"Route Analysis Visualization saved at {os.path.join(FIGURES_DIR, 'route_viz.png')}.")



if __name__ == "__main__":
    dem_data = gen_terrain()
    sloppy = anal_catch(dem_data)
    anal_slope(dem_data, sloppy)


