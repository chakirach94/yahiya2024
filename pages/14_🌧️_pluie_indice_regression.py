import streamlit as st
import pandas as pd
import datetime
import ee
import json
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Initialize Google Earth Engine
ee.Initialize()


# Function to get commune geometry
def get_commune_geometry(geojson, commune_id):
    for feature in geojson['features']:
        if feature['properties']['id_commune'] == commune_id:
            coords = feature['geometry']['coordinates']
            if feature['geometry']['type'] == 'Polygon':
                geometry = ee.Geometry.Polygon(coords[0])
                center = geometry.centroid().getInfo()['coordinates']
                return geometry, feature['geometry'], center
            elif feature['geometry']['type'] == 'MultiPolygon':
                geometry = ee.Geometry.MultiPolygon(coords)
                center = geometry.centroid().getInfo()['coordinates']
                return geometry, feature['geometry'], center
    raise ValueError(f"Commune with ID '{commune_id}' not found.")


# Load GeoJSON and Excel data
geojson_file = "finale_communes_4326.geojson"
gdf = gpd.read_file(geojson_file)
geojson_data = json.loads(gdf.to_json())

excel_file = "Weighted_Averages_of_UF_and_KG_per_Commune.xlsx"
data = pd.read_excel(excel_file)

# Extract communes
if all(col in data.columns for col in ['id_commune', 'commune']):
    communes = data[['id_commune', 'commune']]
else:
    st.error("The Excel file must contain 'id_commune' and 'commune' columns.")

# Function to calculate monthly precipitation
def get_monthly_precipitation(geometry, start_date, end_date):
    """
    Retrieve monthly precipitation data for the given geometry.
    """
    current_date = start_date
    monthly_precipitation = []

    while current_date < end_date:
        month_start = current_date
        month_end = (current_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

        if month_end > end_date:
            month_end = end_date

        month_start_str = month_start.strftime("%Y-%m-%d")
        month_end_str = month_end.strftime("%Y-%m-%d")

        chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
            .filterBounds(geometry) \
            .filterDate(ee.Date(month_start_str), ee.Date(month_end_str)) \
            .select('precipitation')

        if chirps.size().getInfo() > 0:
            total_precipitation = chirps.sum().reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=5000,
                maxPixels=1e9
            ).get('precipitation').getInfo()
        else:
            total_precipitation = None

        monthly_precipitation.append({
            'Month': month_start.strftime("%Y-%m"),
            'Precipitation (mm)': total_precipitation if total_precipitation is not None else float('nan')
        })

        current_date = month_end

    return pd.DataFrame(monthly_precipitation)

# Function to calculate monthly vegetation index
def get_monthly_vegetation_index(geometry, start_date, end_date, index):
    """
    Retrieve monthly mean vegetation index data for the given geometry.
    """
    current_date = start_date
    monthly_index = []

    while current_date < end_date:
        month_start = current_date
        month_end = (current_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

        if month_end > end_date:
            month_end = end_date

        month_start_str = month_start.strftime("%Y-%m-%d")
        month_end_str = month_end.strftime("%Y-%m-%d")

        modis = ee.ImageCollection('MODIS/006/MOD13Q1') \
            .filterBounds(geometry) \
            .filterDate(ee.Date(month_start_str), ee.Date(month_end_str)) \
            .select(index)

        if modis.size().getInfo() > 0:
            mean_index = modis.mean().reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=500,
                maxPixels=1e9
            ).get(index).getInfo()
        else:
            mean_index = None

        monthly_index.append({
            'Month': month_start.strftime("%Y-%m"),
            f'Mean {index}': mean_index / 10000 if mean_index is not None else float('nan')
        })

        current_date = month_end

    return pd.DataFrame(monthly_index)

# Streamlit App
st.title("Analyse Mensuelle des Précipitations et de l'Indice de Végétation par Commune")

# User Inputs
with st.sidebar:
    st.header("Inputs")
    selected_commune = st.selectbox("Sélectionnez une commune", communes['commune'].unique())
    start_date = st.date_input("Select Start Date", datetime.date(2021, 1, 1), min_value=datetime.date(2000, 1, 1))
    end_date = st.date_input("Select End Date", datetime.date(2021, 12, 31), min_value=datetime.date(2000, 1, 1))
    selected_index = st.selectbox("Select Vegetation Index", ["NDVI", "EVI", "DVI", "SAVI"])

# Generate Results
if st.button("Générer les données mensuelles"):
    if start_date >= end_date:
        st.error("La date de fin doit être postérieure à la date de début.")
    else:
        with st.spinner("Calcul des données mensuelles en cours..."):
            try:
                commune_id = communes[communes['commune'] == selected_commune]['id_commune'].values[0]
                commune_geometry, geometry_info, center = get_commune_geometry(geojson_data, commune_id)
                
                precipitation_df = get_monthly_precipitation(commune_geometry, start_date, end_date)
                index_df = get_monthly_vegetation_index(commune_geometry, start_date, end_date, selected_index)

                results_df = pd.merge(precipitation_df, index_df, on='Month', how='outer')

                # Afficher les résultats dans un tableau
                st.write("### Données mensuelles")
                st.dataframe(results_df)

                # Télécharger en tant que fichier CSV
                csv = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger les données en CSV",
                    data=csv,
                    file_name=f"{selected_commune}_donnees_mensuelles.csv",
                    mime="text/csv"
                )

                # Graphique en ligne pour l'évolution
                st.write("### Évolution des données au fil du temps")
                col0_name = results_df.columns[int(0)]
                col1_name = results_df.columns[int(1)]
                col2_name = results_df.columns[int(2)]
                st.line_chart(results_df[[col0_name, col1_name]].set_index('Month'))  
                st.line_chart(results_df[[col0_name, col2_name]].set_index('Month'))  

                st.write("### Déscription des données")
                st.write(results_df.describe())
                # Afficher le résultat
                st.write("### Corrélation avec la pluie")
                # Calcul de la corrélation entre les colonnes sélectionnées
                # Calcul de la corrélation entre les colonnes sélectionnées
                correlation = results_df[col1_name].corr(results_df[col2_name])

                # Affichage des résultats
                st.write(f"Corrélation entre '{col1_name}' et '{col2_name}' : {correlation:.2f}")
                # Calcul de la corrélation

                                # Linear regression
                X = results_df[[col1_name]].values.astype(np.float64)  # Use np.float64 to fix the deprecation
                y = results_df[col2_name].values.astype(np.float64)

                # Modèle de régression
                regressor = LinearRegression()
                regressor.fit(X, y)

                # Prédiction
                y_pred = regressor.predict(X)

                # Affichage dans Streamlit
                st.title("Nuage de Points et Régression Linéaire")

                # Affichage du graphique
                fig, ax = plt.subplots()
                ax.scatter(results_df[col1_name], results_df[col2_name], label="Points de données", color="blue")
                ax.plot(results_df[col1_name], y_pred, color="red", label="Régression Linéaire")
                ax.set_xlabel(col1_name)
                ax.set_ylabel(col2_name)
                ax.legend()
                ax.set_title("Nuage de Points avec Régression Linéaire")

                # Afficher le graphique dans Streamlit
                st.pyplot(fig)

                # Afficher les coefficients de régression
                st.write("**Équation de la régression linéaire :**")
                st.write(f"y = {regressor.coef_[0]:.5f} * x + {regressor.intercept_:.2f}")
                                
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")