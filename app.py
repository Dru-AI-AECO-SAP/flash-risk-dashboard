import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# 1. PAGE LAYOUT
st.set_page_config(page_title="BIM-Enabled Flash Flood Alerts", layout="wide", page_icon="⛈️")
st.title("⛈️ BIM-Enabled Real-Time Flash Flood Road Alert Dashboard")
st.markdown("### AECO & SAP Operational Integration Engine | Sydney, AU & Ras Al Khaimah, UAE")

# 2. FILE UPLOADER CONNECTOR FOR REVIT CSV EXPORTS
st.sidebar.header("📁 BIM Spatial Data Input")
uploaded_file = st.sidebar.file_uploader("Upload Revit/IFC Drainage Schedule (CSV)", type=["csv"])
inject_storm = st.sidebar.checkbox("Simulate Severe Cloudburst (+35mm Rain)", value=False)

# 3. CORE WEATHER PIPELINE
def fetch_weather(lat, lon):
    try:
        url = f"https://open-meteo.com{lat}&longitude={lon}&hourly=precipitation&forecast_days=1"
        res = requests.get(url, timeout=5).json()
        return sum(res['hourly']['precipitation'][:6])
    except Exception:
        return 0.0

# 4. DATA COMPILING LOGIC
if uploaded_file is not None:
    assets_df = pd.read_csv(uploaded_file)
    st.sidebar.success("✅ BIM Schedule Loaded Successfully!")
else:
    default_data = [
        {"Asset_ID": "MOCK-01", "Location_Name": "Carrington Road (Marrickville)", "Latitude": -33.9112, "Longitude": 151.1565, "Drainage_Pipe_Diameter_mm": 300, "Culvert_Material": "Concrete"},
        {"Asset_ID": "MOCK-02", "Location_Name": "Wakehurst Parkway (Narrabeen)", "Latitude": -33.7144, "Longitude": 151.2721, "Drainage_Pipe_Diameter_mm": 450, "Culvert_Material": "Concrete"},
        {"Asset_ID": "MOCK-03", "Location_Name": "Wadi Al Bih Crossing", "Latitude": 25.8201, "Longitude": 56.0715, "Drainage_Pipe_Diameter_mm": 350, "Culvert_Material": "Concrete"}
    ]
    assets_df = pd.DataFrame(default_data)

# 5. RISK ENGINE RUNNING STRUCTURAL BIM CHECKS
processed = []
crit_count = 0

for _, row in assets_df.iterrows():
    rain = fetch_weather(row["Latitude"], row["Longitude"]) + (35.0 if inject_storm else 0.0)
    pipe_dia = row["Drainage_Pipe_Diameter_mm"]
    if pipe_dia <= 300:
        calculated_limit = 15.0
    elif pipe_dia <= 450:
        calculated_limit = 28.0
    else:
        calculated_limit = 40.0
        
    status = "CRITICAL" if rain >= calculated_limit else "NORMAL"
    if status == "CRITICAL": crit_count += 1
    
    processed.append({
        "Asset ID": row["Asset_ID"], "Location": row["Location_Name"], 
        "BIM Pipe Size": f"{pipe_dia} mm", "Material": row["Culvert_Material"],
        "Live 6-Hr Rain": f"{round(rain,1)} mm", "Calculated Limit": f"{calculated_limit} mm", 
        "Status": status, "Color": "red" if status == "CRITICAL" else "green",
        "Lat": row["Latitude"], "Lon": row["Longitude"]
    })

df_results = pd.DataFrame(processed)

# 6. UI PRESENTATION LAYER
m1, m2 = st.columns(2)
m1.metric("Monitored BIM Asset Elements", len(df_results))
m2.metric("Active Flood Warnings", crit_count)

if crit_count > 0:
    st.error(f"🚨 ALERT: {crit_count} asset corridors failing hydraulic capacity checks!")
else:
    st.success("✅ Operational status nominal. All structural drainage flows within safety parameters.")

st.markdown("### 🗺️ Integrated Infrastructure Risk Map")
m = folium.Map(location=[0.0, 100.0], zoom_start=2, tiles="CartoDB positron")
for _, r in df_results.iterrows():
    folium.Marker(
        location=[r["Lat"], r["Lon"]],
        popup=f"<b>ID: {r['Asset ID']}</b><br>Pipe: {r['BIM Pipe Size']}",
        icon=folium.Icon(color=r["Color"], icon="exclamation-sign" if r["Status"] == "CRITICAL" else "ok-sign")
    ).add_to(m)
st_folium(m, width="100%", height=400, returned_objects=[])

st.dataframe(df_results.drop(columns=["Color", "Lat", "Lon"]), use_container_width=True)
