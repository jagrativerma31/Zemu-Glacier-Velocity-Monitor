import xarray as xr
import rioxarray
from glob import glob
import seaborn as sns
import matplotlib.pyplot as plt

def main():
    # Look for files in the current directory
    tif_list = glob('*.tif')
    datasets = []
    
    for tif_path in tif_list:
        src = rioxarray.open_rasterio(tif_path, masked=True)
        src.name = "velocity"
        datasets.append(src)
    
    if not datasets:
        print("No velocity maps found.")
        return

    ds = xr.concat(datasets, dim="dates")
    median_vel = ds.median(dim="dates").squeeze()

    sns.set_theme()
    fig, ax = plt.subplots(figsize=(10, 6))
    median_vel.plot(ax=ax, cmap='inferno', vmin=0, vmax=500)
    ax.set_title("Zemu Glacier Median Horizontal Velocity (m/yr)")
    
    # Save directly to root
    plt.savefig('velocity_summary_statistics.png', dpi=300)

if __name__ == "__main__":
    main()
