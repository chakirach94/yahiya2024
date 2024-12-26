import streamlit as st
import ee
from datetime import datetime
import geopandas as gpd
import pandas as pd
import json
# Initialize Earth Engine
def initialize_earth_engine():
    try:
        ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize()
# Function to get commune geometry and center coordinates
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



def generate_timelapse_multiple_indices(region, start_date, end_date, indices, dimensions=215):
    """
    Generate timelapse GIFs for multiple vegetation indices.

    Args:
        region (ee.Geometry): The region for the timelapse.
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.
        indices (list): A list of vegetation indices (e.g., ['NDVI', 'EVI']).
        dimensions (int): The maximum dimensions (width or height) of the GIF (default: 512).

    Returns:
        dict: A dictionary with vegetation indices as keys and GIF URLs as values.
    """
    def calculate_image_index(image, index):
        if index == 'NDVI':
            return image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        elif index == 'RVI':
            return image.expression('B4 / B8', {'B4': image.select('B4'), 'B8': image.select('B8')}).rename('RVI')
        elif index == 'DVI':
            return image.expression('B8 - B4', {'B4': image.select('B4'), 'B8': image.select('B8')}).rename('DVI')
        elif index == 'SAVI':
            L = 0.5
            return image.expression('((B8 - B4) / (B8 + B4 + L)) * (1 + L)', {'B4': image.select('B4'), 'B8': image.select('B8'), 'L': L}).rename('SAVI')
        elif index == 'EVI':
            return image.expression('2.5 * ((B8 - B4) / (B8 + 6 * B4 - 7.5 * B2 + 1))', {'B4': image.select('B4'), 'B8': image.select('B8'), 'B2': image.select('B2')}).rename('EVI')
        elif index == 'GNDVI':
            return image.normalizedDifference(['B8', 'B3']).rename('GNDVI')
        elif index == 'IPVI':
            return image.expression('B8 / (B8 + B4)', {'B4': image.select('B4'), 'B8': image.select('B8')}).rename('IPVI')
        elif index == 'NDWI':
            return image.normalizedDifference(['B3', 'B8']).rename('NDWI')
        elif index == 'MSAVI':
            return image.expression('(2 * B8 + 1 - sqrt((2 * B8 + 1) ** 2 - 8 * (B8 - B4))) / 2', {'B4': image.select('B4'), 'B8': image.select('B8')}).rename('MSAVI')
        elif index == 'TSAVI':
            a = 1.339198  # Adjust slope for TSAVI
            b = 0.006262  # Adjust intercept for TSAVI
            return image.expression(
                'a * (B8 - a * B4 - b) / (B8 + B4 - a * b + 0.08 * (1 + a**2))',
                {'B4': image.select('B4'), 'B8': image.select('B8'), 'a': a, 'b': b}
            ).rename('TSAVI')
        else:
            raise ValueError(f"Unsupported index: {index}")

    gif_urls = {}
    for index in indices:
        # Load the image collection
        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start_date, end_date)
            .map(lambda img: calculate_image_index(img, index))
        )

        # Clip the collection to the region
        collection = collection.map(lambda img: img.clip(region))

        # Compute dynamic min and max
        
            # Define ranges and palettes for each index
        index_ranges = {
            "NDVI": {"min": -1.0, "max": 1.0, "palette": ["blue", "green", "yellow", "red"]},
            "RVI": {"min": 0, "max": 10, "palette": ["white", "blue", "green"]},
            "DVI": {"min": 0, "max": 1.0, "palette": ["purple", "green", "yellow"]},
            "SAVI": {"min": -1.0, "max": 1.0, "palette": ["blue", "green", "yellow", "red"]},
            "EVI": {"min": -1.0, "max": 2.0, "palette": ["blue", "green", "yellow", "red"]},
            "GNDVI": {"min": -1.0, "max": 1.0, "palette": ["blue", "green", "yellow"]},
            "IPVI": {"min": 0, "max": 1.0, "palette": ["green", "yellow", "red"]},
            "NDWI": {"min": -1.0, "max": 1.0, "palette": ["cyan", "blue", "green"]},
            "MSAVI": {"min": -1.0, "max": 1.0, "palette": ["blue", "green", "yellow"]},
            "TSAVI": {"min": 0, "max": 1.0, "palette": ["yellow", "orange", "red"]},
        }

        # Get the dynamic range and palette for the index
        vis_params = index_ranges.get(index, {"min": -1.0, "max": 1.0, "palette": ["green", "yellow", "red"]})

        # Add visualization and overlay dates
        def add_date(img):
            """
            Annotates an image with its acquisition date.

            Args:
                img (ee.Image): The image to annotate.

            Returns:
                ee.Image: Annotated image.
            """
            # Check if 'system:time_start' exists and retrieve the date
            date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
            
            # Ensure the date is not null
            date = ee.Algorithms.If(img.propertyNames().contains('system:time_start'), date, 'No Date')

            # Create a feature with the date as a property
            date_feature = ee.Feature(region.centroid(), {'label': date})
            
            # Create an image layer from the feature
            text_layer = ee.Image().paint(date_feature.geometry(), 1, 300)  # Adjust size and thickness
            
            # Visualize the text
            text_visualized = text_layer.visualize(palette=['black'])
            
            # Blend the text layer with the visualized image
            return img.visualize(**vis_params).blend(text_visualized)


        collection = collection.map(add_date)

        # Export the GIF with reduced dimensions
        gif_params = {
            'dimensions': dimensions,  # Reduce dimensions to reduce pixel count
            'region': region.getInfo()['coordinates'],
            'framesPerSecond': 2,
            'crs': 'EPSG:4326',
        }

        gif_urls[index] = collection.getVideoThumbURL(gif_params)

    return gif_urls



# Disposition principale de l'application
st.title("Timelapse de l'Indice de Végétation")

with st.form("timelapse_form"):
    st.markdown("### Paramètres d'entrée")
    
    # Saisie de la date de début
    start_date = st.date_input("Sélectionnez une date de début :", datetime(2021, 1, 1), min_value=datetime(2000, 1, 1))
    
    # Saisie de la date de fin
    end_date = st.date_input("Sélectionnez une date de fin :", datetime(2021, 12, 31), min_value=datetime(2000, 1, 1))
    
    # Liste déroulante pour la sélection des indices de végétation
    indices = st.multiselect(
        "Sélectionnez les indices de végétation :",
        ["NDVI", "EVI", "RVI", "DVI", "SAVI", "GNDVI", "IPVI", "NDWI", "MSAVI", "TSAVI"],
        default=["NDVI"]
    )
    # Liste déroulante pour la sélection de la commune
    # Remplacez cette liste par des noms réels de communes
    selected_commune = st.selectbox("Sélectionnez une commune", communes['commune'].unique())

    # Bouton de soumission
    submitted = st.form_submit_button("Générer le timelapse")

if submitted:
    try:
        # Valider que la date de début est antérieure à la date de fin
        if start_date >= end_date:
            st.error("La date de fin doit être postérieure à la date de début.")
        else:
            # Définir une région de test (remplacer par une géométrie réelle basée sur la commune)
            # Exemple : Région plus petite pour les tests
            # Obtenir l'ID et la géométrie de la commune sélectionnée
            commune_id = communes[communes['commune'] == selected_commune]['id_commune'].values[0]
            commune_geometry, geometry_info, center = get_commune_geometry(geojson_data, commune_id)

        with st.spinner("Génération des timelapses en cours..."):
            gif_urls = generate_timelapse_multiple_indices(
                commune_geometry,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                indices
            )
            time_series = generate_timelapse_multiple_indices(
                region=commune_geometry,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                indices=indices
            )
    
        for index, gif_url in gif_urls.items():
            st.success(f"Timelapse {index} généré avec succès !")
            st.image(gif_url, caption=f"Évolution de {index}", use_column_width=True)
            st.markdown(f"[Télécharger le timelapse GIF de {index}]({gif_url})")
            # Afficher les données sous forme de tableau pour chaque indice

    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
