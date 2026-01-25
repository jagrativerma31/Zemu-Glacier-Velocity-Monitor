import xarray as xr
import rioxarray
import numpy as np
import os
from autoRIFT import autoRIFT
from scipy.interpolate import interpn
import pystac_client
import stackstac
import geopandas as gpd
from shapely.geometry import shape
import argparse
import warnings

warnings.filterwarnings("ignore")

def download_s2(img1_name, img2_name, bbox):
    URL = "https://earth-search.aws.element84.com/v1"
    catalog = pystac_client.Client.open(URL)

    def get_img(name):
        search = catalog.search(collections=["sentinel-2-l2a"], query=[f's2:product_uri={name}'])
        items = search.item_collection()
        stack = stackstac.stack(items)
        aoi = gpd.GeoDataFrame({'geometry':[shape(bbox)]})
        return stack.rio.clip_box(*aoi.total_bounds, crs=4326).to_dataset(dim='band')

    return get_img(img1_name), get_img(img2_name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("img1_product_name")
    parser.add_argument("img2_product_name")
    args = parser.parse_args()

    # Zemu Coordinates
    bbox = {"type": "Polygon", "coordinates": [[[88.165, 27.802], [88.165, 27.669], [88.404, 27.669], [88.404, 27.802], [88.165, 27.802]]]}

    img1_ds, img2_ds = download_s2(args.img1_product_name, args.img2_product_name, bbox)
    
    obj = autoRIFT()
    obj.I1 = img1_ds.nir.squeeze().values
    obj.I2 = img2_ds.nir.squeeze().values
    
    # Auto-scale search limit
    days = (img2_ds.time.isel(time=0) - img1_ds.time.isel(time=0)).dt.days.item()
    limit = round((days * 100) / 365.25)
    
    obj.SkipSampleX = obj.SkipSampleY = 3
    obj.ChipSizeMinX = 16
    obj.ChipSizeMaxX = 64
    obj.SearchLimitX = obj.SearchLimitY = np.full((1,1), limit) # Simplified for cloud run

    obj.preprocess_filt_lap()
    obj.uniform_data_type()
    obj.runAutorift()

    # Save output
    velocity = xr.DataArray(obj.Dx * 10, coords=img1_ds.nir.squeeze().coords, dims=img1_ds.nir.squeeze().dims)
    velocity.rio.to_raster(f'S2_{args.img1_product_name[11:19]}_{args.img2_product_name[11:19]}_horizontal_velocity.tif')

if __name__ == "__main__":
    main()
