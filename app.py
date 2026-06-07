import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# 1. PAGE LAYOUT
st.set_page_config(page_title="Flash Flood Road Alerts", layout="wide", page_icon="⛈️")
st.title("⛈️ Real-Time Flash Flood Road Alert Dashboard")
st.markdown("### Hydrological Risk Core | Sydney, AU & Ras Al Khaimah, UAE")

# 2. CONTROL CONTROLS
st.sidebar.header("🕹️ Simulation Overrides")
inject_storm = st.sidebar.checkbox("Simulate Severe Cloudburst (+35mm Rain)", value=False)

# 3. WEATHER DATA PIPELINE
def fetch_weather(lat, lon):
    try:
        url = f"https://open-meteo.com{lat}&longitude={lon}&hourly=precipitation&forecast_days=1"
        res = requests.get(url, timeout=5).json()
        return sum(res['hourly']['precipitation'][:6])
    except Exception:
        return 0.0

# 4. FIXED ROAD DATABASE
assets = [
    {"Reg": "Sydney, AU", "Loc": "Carrington Road (Marrickville)", "Lat": -33.9112, "Lon": 151.1565, "Type": "Low-Lying Urban Basin", "Limit": 25.0},
    {"Reg": "Sydney, AU", "Loc": "Wakehurst Parkway (Narrabeen)", "Lat": -33.7144, "Lon": 151.2721, "Type": "Coastal Valley Corridor", "Limit": 30.0},
    {"Reg": "Ras Al Khaimah, UAE", "Loc": "Wadi Al Bih Crossing", "Lat": 25.8201, "Lon": 56.0715, "Type": "Arid Desert Canyon Bed", "Limit": 10.0}
]

# 5. RISK ENGINE LOOPS
processed = []
crit_count = 0
for a in assets:
    rain = fetch_weather(a["Lat"], a["Lon"]) + (35.0 if inject_storm else 0.0)
    status = "CRITICAL" if rain >= a["Limit"] else "NORMAL"
    if status == "CRITICAL": crit_count += 1
    
    processed.append({
        "Region": a["Reg"], "Location": a["Loc"], "Terrain": a["Type"], 
        "Live 6-Hr Rain": f"{round(rain,1)} mm", "Safety Limit": f"{a['Limit']} mm", 
        "Status": status, "Color": "red" if status == "CRITICAL" else "green",
        "Lat": a["Lat"], "Lon": a["Lon"]
    })

df = pd.DataFrame(processed)

# 6. UI PRESENTATION LAYER
m1, m2 = st.columns(2)
m1.metric("Monitored Corridors", len(df))
m2.metric("Active Flood Warnings", crit_count)

if crit_count > 0:
    st.error(f"🚨 ALERT: {crit_count} segments at critical flood risk! Boom gates activated.")
else:
    st.success("✅ Operational status nominal. All routes safe.")

# Visual Geographic Map
st.markdown("### 🗺️ Infrastructure Risk Map")
m = folium.Map(location=[-33.9112, 151.1565] if inject_storm else [0.0, 100.0], zoom_start=2, tiles="CartoDB positron")
for _, r in df.iterrows():
    folium.Marker(
        location=[r["Lat"], r["Lon"]],
        popup=f"<b>{r['Location']}</b><br>Rain: {r['Live 6-Hr Rain']}",
        icon=folium.Icon(color=r["Color"], icon="exclamation-sign" if r["Status"] == "CRITICAL" else "ok-sign")
    ).add_to(m)
st_folium(m, width="100%", height=400, returned_objects=[])

st.dataframe(df.drop(columns=["Color", "Lat", "Lon"]), use_container_width=True)
