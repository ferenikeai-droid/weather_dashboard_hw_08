
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# 1. Az alkalmazás alapbeállításai
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="⛅",
    layout="centered"
)

# 2. API-végpontok
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


# 3. Városkereső függvény
def find_city(city_name):
    params = {
        "name": city_name,
        "count": 1,
        "language": "hu"
    }

    try:
        response = requests.get(
            GEOCODING_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

    except (requests.exceptions.RequestException, ValueError):
        st.warning("Nem sikerült lekérni a város adatait.")
        return None

    results = data.get("results", [])

    if not results:
        st.warning("Nem található ilyen város.")
        return None

    return results[0]


# 4. Időjárás-lekérő függvény

def fetch_weather(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "hourly": "temperature_2m,relative_humidity_2m",
        "forecast_hours": 24,
        "timezone": "auto"
    }

    try:
        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        return data

    except (requests.exceptions.RequestException, ValueError):
        st.warning("Nem sikerült lekérni az időjárásadatokat.")
        return None


# 5. A kiválasztott város megőrzése
if "city" not in st.session_state:
    st.session_state.city = "Győr"


# 6. Cím és városkereső
st.title("⛅ Weather Dashboard")
st.caption("Interaktív időjárás-alkalmazás")

with st.form("city_form"):
    city_input = st.text_input(
        "Melyik város időjárása érdekel?",
        value=st.session_state.city
    )

    submitted = st.form_submit_button("Keresés")

if submitted:
    if city_input.strip():
        st.session_state.city = city_input.strip()
    else:
        st.warning("Kérlek, adj meg egy városnevet!")
        st.stop()


# 7. Város adatainak lekérése
location = find_city(st.session_state.city)

if location:
    city_name = location["name"]
    country = location.get("country", "Ismeretlen ország")
    latitude = location["latitude"]
    longitude = location["longitude"]

    st.header(f"📍 {city_name}, {country}")

    st.write(f"Szélességi fok: {latitude:.4f}")
    st.write(f"Hosszúsági fok: {longitude:.4f}")

    # 8. Időjárásadatok lekérése
    weather = fetch_weather(latitude, longitude)



    if weather:
        current = weather["current"]

        st.subheader("Aktuális időjárás")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Hőmérséklet",
                f"{current['temperature_2m']} °C"
            )

        with col2:
            st.metric(
                "Páratartalom",
                f"{current['relative_humidity_2m']} %"
            )

        with col3:
            st.metric(
                "Szélsebesség",
                f"{current['wind_speed_10m']} km/h"
            )

        # Óránkénti adatok feldolgozása
        hourly = weather.get("hourly")

        if hourly and hourly.get("time"):
            df = pd.DataFrame(hourly)

            df["time"] = pd.to_datetime(df["time"])

            st.subheader("24 órás előrejelzés")

            tab1, tab2 = st.tabs([
                "🌡️ Hőmérséklet",
                "💧 Páratartalom"
            ])

            with tab1:
                fig_temp = px.line(
                    df,
                    x="time",
                    y="temperature_2m",
                    title="Hőmérséklet alakulása",
                    labels={
                        "time": "Időpont",
                        "temperature_2m": "Hőmérséklet (°C)"
                    },
                    markers=True
                )

                st.plotly_chart(
                    fig_temp,
                    width="stretch"
                )

            with tab2:
                fig_humidity = px.line(
                    df,
                    x="time",
                    y="relative_humidity_2m",
                    title="Páratartalom alakulása",
                    labels={
                        "time": "Időpont",
                        "relative_humidity_2m": "Páratartalom (%)"
                    },
                    markers=True
                )

                st.plotly_chart(
                    fig_humidity,
                    width="stretch"
                )

            st.caption(
                f"Az előrejelzés {len(df)} órás adatpontot tartalmaz."
            )

        else:
            st.warning("Nem érkeztek óránkénti adatok.")

        st.caption("Időjárásadatok: Open-Meteo")
