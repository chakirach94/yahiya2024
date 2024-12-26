import streamlit as st
import ee
import json
import pandas as pd
import geopandas as gpd

# Initialize Google Earth Engine
def initialize_earth_engine():
    try:
        ee.Initialize()
    except Exception as e:
        ee.Authenticate()
        ee.Initialize()

initialize_earth_engine()


# Contenu de la barre latérale
with st.sidebar:
    # Ajouter le logo de l'IAV et le titre
    st.image("logo.png", caption="Geo - Parcours 2024", use_column_width=True)

    st.markdown(
        """
        ### Application d'Estimation de la Phytomasse
        Cette application aide la **Direction Provinciale d'Agriculture (DPA)** à estimer les indices de végétation et à calculer la phytomasse pour des provinces spécifiques.  
        Développée dans le cadre d'un **projet de fin d'études (PFE)** à l'[Institut Agronomique et Vétérinaire Hassan II (IAV)](https://iav.ac.ma/).
        """
    )

    # Navigation
    st.markdown("---")
    accueil_button = st.button("🏠 Accueil")
    analyse_button = st.button("📊 Analyse de la Phytomasse")
    contact_button = st.button("📞 Informations de Contact")

    # Informations de contact
    st.markdown("---")
    st.markdown("### Contact")
    st.markdown(
        """
        📧 **Email:** [example@iav.ac.ma](mailto:example@iav.ac.ma)  
        📞 **Téléphone:** +212-123-456-789  
        🌐 **Site web:** [IAV Hassan II](https://iav.ac.ma)
        """
    )

    # Section de support
    st.markdown("---")
    st.markdown("### Support")
    st.markdown(
        """
        Si vous avez des questions ou besoin d'assistance, n'hésitez pas à nous contacter. Nous sommes là pour vous aider !
        """
    )



   
    st.markdown("---")



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
    communes = pd.DataFrame()  # Empty fallback

# Function to get commune geometry
def get_commune_geometry(geojson, commune_id):
    for feature in geojson['features']:
        if feature['properties']['id_commune'] == commune_id:
            coords = feature['geometry']['coordinates']
            if feature['geometry']['type'] == 'Polygon':
                return ee.Geometry.Polygon(coords[0])
            elif feature['geometry']['type'] == 'MultiPolygon':
                return ee.Geometry.MultiPolygon(coords)
    raise ValueError(f"Commune with ID '{commune_id}' not found.")

# Function to calculate area
def calculate_area(geometry):
    """
    Calculate the area of a geometry in hectares using Google Earth Engine.
    """
    area = geometry.area().divide(10000).getInfo()  # Convert square meters to hectares
    return area

# Function to categorize demand/offer ratio
def categorize_ratio(ratio):
    if ratio < 0.85:
        return "Déficience élevée", "red", "Le rapport demande/offre est très bas, ce qui indique un déficit critique des ressources disponibles par rapport à la demande."
    elif 0.85 <= ratio < 0.95:
        return "Déficience", "orange", "Le rapport demande/offre montre un déficit modéré. Il peut être nécessaire d'ajuster les allocations."
    elif 0.95 <= ratio <= 1.05:
        return "Équilibre", "yellow", "Le rapport demande/offre est équilibré. Les ressources disponibles couvrent la demande actuelle."
    elif 1.05 < ratio <= 1.15:
        return "Surplus", "lightgreen", "Le rapport demande/offre indique un léger surplus. Les ressources disponibles excèdent légèrement la demande."
    elif ratio > 1.15:
        return "Surplus élevé", "darkgreen", "Le rapport demande/offre est très élevé, indiquant un surplus important des ressources disponibles."

# Application Title
st.title("Comparaison entre la Demande et l'Offre par Commune")

# Commune selection
selected_commune = st.selectbox("Sélectionnez une commune :", communes['commune'].unique())

if selected_commune:
    # Get selected commune details
    commune_id = communes[communes['commune'] == selected_commune]['id_commune'].values[0]
    commune_geometry = get_commune_geometry(geojson_data, commune_id)

    # Calculate area using GEE
    area_ha = calculate_area(commune_geometry)

    # Display commune details
    st.write(f"**Superficie de la commune sélectionnée :** {area_ha:.2f} hectares")

    # Input for Demand and Offer
    col1, col2 = st.columns(2)
    with col1:
        demand = st.text_input("Entrez la demande (en UF) :", key="demand_input")
    with col2:
        offer = st.text_input("Entrez l'offre (en UF) :", key="offer_input")

    # Calculate button
    if st.button("Calculer"):
        if demand and offer:  # Ensure inputs are not empty
            try:
                # Convert inputs to float for calculation
                demand = float(demand)
                offer = float(offer)

                if offer > 0:  # Avoid division by zero
                    # Calculate Demand/Offer ratio
                    ratio = offer/demand
                    category, color, explanation = categorize_ratio(ratio)

                    # Calculate demand per hectare
                    demand_per_hectare = demand / area_ha
                    offer_per_hectare = offer / area_ha

                    # Display results
                    st.markdown(f"### Résultats pour la commune : {selected_commune}")
                    st.write(f"- **Demande totale** : {demand} UF")
                    st.write(f"- **Offre totale** : {offer} UF")
                    st.write(f"- **Superficie** : {area_ha:.2f} hectares")
                    st.write(f"- **Demande par hectare** : {demand_per_hectare:.2f} UF/ha")
                    st.write(f"- **Offre par hectare** : {offer_per_hectare:.2f} UF/ha")

                    st.markdown(
                        f"<p style='color:{color}; font-weight:bold;'>- Catégorie : {category}</p>",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<p style='color:{color};'>{explanation}</p>",
                        unsafe_allow_html=True
                    )
                else:
                    st.error("L'offre ne peut pas être égale à zéro.")
            except ValueError:
                st.error("Veuillez entrer des nombres valides pour la demande et l'offre.")
        else:
            st.error("Veuillez remplir la demande et l'offre.")
