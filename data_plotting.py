from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import ast


#open the file to read
parent_dir = Path.cwd()  
meta_data_dir = parent_dir.parent / "scenario_data" / "metadata"
meta_data_file = f"{meta_data_dir}/Scenario_1.csv"
df=pd.read_csv(meta_data_file)

#create the list of lats and longs for the sams in order to plot them
df['sam_locations']=df['sam_locations'].apply(ast.literal_eval)
sam_lats=[]
for coord in df['sam_locations']:
    sam_lats.append(coord[0][0])
sam_lons=[]
for coord in df['sam_locations']:
    sam_lons.append(coord[1][1])

#create the map projection
fig, ax=plt.subplots(figsize=(10, 5), subplot_kw={'projection':ccrs.PlateCarree()})
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS)
ax.set_global()

#plot the sam sites
ax.scatter(sam_lons, sam_lats, color='red', marker='o', s=10, transform=ccrs.PlateCarree())

plt.title("Visualization of Scenarios")
plt.show()
