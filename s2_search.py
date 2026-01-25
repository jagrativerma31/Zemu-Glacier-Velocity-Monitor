import xarray as xr
import os
import pystac
import pystac_client
import stackstac
import json
import pandas as pd
import argparse

def get_parser():
    parser = argparse.ArgumentParser(description="Search for Sentinel-2 images")
    parser.add_argument("cloud_cover", type=str, help="percent cloud cover allowed (0-100)")
    parser.add_argument("start_month", type=str, help="first month to search")
    parser.add_argument("stop_month", type=str, help="last month to search")
    parser.add_argument("npairs", type=str, help="number of pairs per image")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    # Updated coordinates for Zemu Glacier, Sikkim
    bbox = {
      "type": "Polygon",
      "coordinates": [[
        [88.16586825695424, 27.802206593163703],
        [88.16586825695424, 27.66958139154667],
        [88.4049690127207, 27.66958139154667],
        [88.4049690127207, 27.802206593163703],
        [88.16586825695424, 27.802206593163703]
      ]]
    }
    
    URL = "https://earth-search.aws.element84.com/v1"
    catalog = pystac_client.Client.open(URL)
    
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        intersects=bbox,
        query={"eo:cloud_cover": {"lt": float(args.cloud_cover)}}
    )
    
    items = search.item_collection()
    sentinel2_stack = stackstac.stack(items)
    
    # Filter by user-defined month range
    stack_filtered = sentinel2_stack.where(
        (sentinel2_stack.time.dt.month >= int(args.start_month)) & 
        (sentinel2_stack.time.dt.month <= int(args.stop_month)), 
        drop=True
    )
    
    period_index = pd.PeriodIndex(stack_filtered['time'].values, freq='M')
    stack_filtered.coords['year_month'] = ('time', period_index)
    first_image_indices = stack_filtered.groupby('year_month').apply(lambda x: x.isel(time=0))
    
    product_names = first_image_indices['s2:product_uri'].values.tolist()
    
    pairs = []
    for r in range(len(product_names) - int(args.npairs)):
        for s in range(1, int(args.npairs) + 1 ):
            img1 = product_names[r]
            img2 = product_names[r+s]
            shortname = f'{img1[11:19]}_{img2[11:19]}'
            pairs.append({'img1_product_name': img1, 'img2_product_name': img2, 'name':shortname})
            
    matrixJSON = f'{{"include":{json.dumps(pairs)}}}'
    
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        print(f'MATRIX_PARAMS_COMBINATIONS={matrixJSON}', file=f)

if __name__ == "__main__":
   main()
