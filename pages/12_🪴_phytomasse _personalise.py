import streamlit as st
import geemap.foliumap as geemap
from streamlit_folium import st_folium
import folium
import ee
import geopandas as gpd
import pandas as pd
import json
from datetime import datetime, timedelta
def get_commune_geometry(geojson_data):
    """
    Extracts the geometry from the uploaded GeoJSON file.

    Args:
        geojson_data (dict): Parsed GeoJSON data.

    Returns:
        tuple: Geometry (as ee.Geometry), raw GeoJSON geometry, and center coordinates.
    """
    try:
        # Assuming the first feature is used for calculations
        feature = geojson_data['features'][0]
        coords = feature['geometry']['coordinates']
        
        # Determine geometry type
        if feature['geometry']['type'] == 'Polygon':
            geometry = ee.Geometry.Polygon(coords[0])
        elif feature['geometry']['type'] == 'MultiPolygon':
            geometry = ee.Geometry.MultiPolygon(coords)
        else:
            raise ValueError("Unsupported geometry type. Only Polygon and MultiPolygon are supported.")
        
        # Calculate center of the geometry
        center = geometry.centroid().getInfo()['coordinates']
        
        return geometry, feature['geometry'], center
    except Exception as e:
        st.error(f"Erreur lors de l'extraction de la géométrie : {e}")
        return None, None, None


def load_geojson(file):
    """
    Load and parse a GeoJSON file.

    Args:
        file: The uploaded file object from Streamlit.

    Returns:
        dict: Parsed GeoJSON data.
    """
    try:
        geojson_data = json.load(file)
        return geojson_data
    except Exception as e:
        st.error("Erreur lors du chargement du fichier GeoJSON. Veuillez vérifier le format.")
        return None


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




# Initialize Earth Engine
def initialize_earth_engine():
    try:
        ee.Initialize()
    except Exception as e:
        ee.Authenticate()
        ee.Initialize()
    return ee

def get_download_link(image, region, scale=10, filename='output'):
    """
    Generate a link to download the image as a GeoTIFF.

    Args:
        image (ee.Image): The image to download (e.g., index or phytomass).
        region (ee.Geometry): The region to clip the image.
        scale (int): The spatial resolution in meters (default is 10 for Sentinel-2).
        filename (str): The desired filename for the downloaded GeoTIFF.

    Returns:
        str: A URL to download the GeoTIFF.
    """
    # Clip the image to the region
    image = image.clip(region)

    # Prepare the download URL
    url = image.getDownloadURL({
        'scale': scale,
        'region': region,  # Pass region directly
        'format': 'GeoTIFF',
        'name': filename
    })
    return url


def calculate_sum(image, region, scale=10):
    """
    Calculate the sum of pixel values over the specified region.

    Args:
        image (ee.Image): The image (e.g., index or phytomass) for which the sum will be calculated.
        region (ee.Geometry): The region over which the sum will be calculated.
        scale (int): The spatial resolution in meters (default is 10 for Sentinel-2).

    Returns:
        float: The sum of the pixel values within the region.
    """
    sum_result = image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=region,
        scale=scale,
        maxPixels=1e9
    ).getInfo()
    return sum_result

def calculate_mean(image, region, scale=10):
    """
    Calculate the sum of pixel values over the specified region.

    Args:
        image (ee.Image): The image (e.g., index or phytomass) for which the sum will be calculated.
        region (ee.Geometry): The region over which the sum will be calculated.
        scale (int): The spatial resolution in meters (default is 10 for Sentinel-2).

    Returns:
        float: The sum of the pixel values within the region.
    """
    sum_result = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e9
    ).getInfo()
    return sum_result

def get_download_link(image, region, scale=10, filename='output'):
    """
    Generate a link to download the image as a GeoTIFF.

    Args:
        image (ee.Image): The image to download (e.g., index or phytomass).
        region (ee.Geometry): The region to clip the image.
        scale (int): The spatial resolution in meters (default is 10 for Sentinel-2).
        filename (str): The desired filename for the downloaded GeoTIFF.

    Returns:
        str: A URL to download the GeoTIFF.
    """
    # Clip the image to the region
    image = image.clip(region)

    # Prepare the download URL
    url = image.getDownloadURL({
        'scale': scale,
        'region': region,  # Pass region directly
        'format': 'GeoTIFF',
        'name': filename
    })
    return url



# Function to calculate the selected vegetation index
def calculate_index(region, date, index, mask_clouds=True, scale_factor=1):
    """
    Calculate a vegetation index over the specified geometry and date range.

    Args:
        region (ee.Geometry): The geometry for which the index will be calculated.
        date (str): The end date in "YYYY-MM-DD" format.
        index (str): The name of the vegetation index to calculate (e.g., "NDVI", "RVI", "DVI", etc.).
        mask_clouds (bool): Whether to apply cloud masking (default: True).
        scale_factor (float): Factor to scale the index values (default: 1).

    Returns:
        ee.Image: The calculated vegetation index image clipped to the provided region.
    """
    # Define date range
    end_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=30)  # 1 month of data

    # Load Sentinel-2 collection
    s2_sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(region) \
        .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

    # Apply cloud masking if enabled
    if mask_clouds:
        def mask_clouds_function(image):
            cloud_mask = image.select('QA60').lt(1)
            return image.updateMask(cloud_mask)
        s2_sr = s2_sr.map(mask_clouds_function)

    # Define the index calculation
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
            a = 1.339198  # Slope for 2020 (adjust as needed)
            b = 0.006262  # Intercept for 2020 (adjust as needed)
            return image.expression(
                'a * (B8 - a * B4 - b) / (B8 + B4 - a * b + 0.08 * (1 + a**2))',
                {
                    'B4': image.select('B4'),
                    'B8': image.select('B8'),
                    'a': a,
                    'b': b
                }
            ).rename('TSAVI')
        else:
            raise ValueError(f"Unsupported index: {index}")


    # Apply the index calculation
    index_image = s2_sr.map(lambda img: calculate_image_index(img, index)).median()

    # Scale the index if a scale factor is provided
    if scale_factor != 1:
        index_image = index_image.multiply(scale_factor)

    # Clip the image to the region
    index_image = index_image.clip(region)

    return index_image



# Function to calculate phytomass
# Function to calculate phytomass
def calculate_phytomass(index_image, formula_type, custom_formula=None, custom_variables=None):
    """
    Calculate phytomass using a custom formula or a predefined type.

    Args:
        index_image (ee.Image): The vegetation index image.
        formula_type (str): The type of formula ('Custom' or predefined).
        custom_formula (str, optional): The custom formula to calculate phytomass.
        custom_variables (dict, optional): A dictionary mapping variables in the custom formula to bands in index_image.

    Returns:
        tuple: A tuple containing the phytomass image and the fixed R² value (0.8).
    """
    r_squared = 0.8  # Fixed R² value for consistency

    # Handle custom formulas
    if formula_type == 'Custom':
        if not custom_formula or not custom_variables:
            raise ValueError("Custom formula and variables must be provided for 'Custom' formula_type.")
        
        # Evaluate the custom formula using the provided variables
        phytomass = index_image.expression(custom_formula, custom_variables).rename('Phytomass')
    
    else:
        raise ValueError(f"Unsupported formula_type: {formula_type}")

    return phytomass, r_squared

# Initialize Earth Engine
ee = initialize_earth_engine()

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
# Initialize session state for map configuration
if "map_center" not in st.session_state:
    st.session_state.map_center = [31.5, -7.0]  # Default center (Morocco)
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 6  # Default zoom level
if "map_layers" not in st.session_state:
    st.session_state.map_layers = []  # Store added layers

# Sidebar customization

# Streamlit app layout
st.title("Formule personnalisée de la Phytomasse par Commune")
with st.form("index_form"):
    # Commune selection
    uploaded_file = st.file_uploader(
        "Glissez-déposez un fichier GeoJSON ici ou cliquez pour le télécharger.",
        type=["geojson"],
        key="geojson_file"
    )

    if uploaded_file:
        # Parse GeoJSON
        geojson_data = load_geojson(uploaded_file)

        # Display the parsed GeoJSON if valid
        if geojson_data:
            st.success("Fichier GeoJSON chargé avec succès !")
        else:
            geojson_data = None
    # Date input
    selected_date = st.date_input(
        "Sélectionnez une date :",
        datetime.today(),
        min_value=datetime(2000, 1, 1),
        max_value=datetime.today()
    )

    # Index selection
    selected_index = st.selectbox(
        "Sélectionnez un index de végétation pour la formule personnalisée",
        ['NDVI', 'RVI', 'DVI', 'SAVI', 'MSAVI', 'TSAVI', 'IPVI']
    )

    # Explanation for custom formula
    st.markdown(f"""
        ### Définissez une formule personnalisée
        Entrez une formule en utilisant l'index sélectionné : **{selected_index}**.
        
        - L'index sélectionné représente la valeur de végétation pour vos calculs.
        - Exemple de formule : `35 + 100 * {selected_index} - 50 * ({selected_index} ** 2)`
        
        Assurez-vous que votre formule utilise correctement cet index.
    """)

    # Custom formula input
    custom_formula = st.text_input(
        "Entrez votre formule personnalisée ici :",
        value=f"35 + 100 * {selected_index} - 50 * ({selected_index} ** 2)"
    )

    # Submit button
    calculate_button = st.form_submit_button("Calculer")

    # Handle form submission
    if calculate_button:
        if custom_formula:
            st.write("Index sélectionné :", selected_index)
            st.write("Formule personnalisée définie :")
            st.latex(custom_formula)
        else:
            st.error("Veuillez entrer une formule valide.")


# Check if the button was clicked and calculate the results
if calculate_button:
    try:
        # Determine corresponding index
        index = selected_index  # Directly use the selected index
        date = selected_date.strftime('%Y-%m-%d')  # Convert the selected date to string format

        # Get the selected commune's ID and geometry
        commune_geometry, geometry_info, center = get_commune_geometry(geojson_data)

        # Update session state with the map's center and zoom
        st.session_state.map_center = [center[1], center[0]]
        st.session_state.map_zoom = 12

        # Calculate vegetation index
        index_image = calculate_index(commune_geometry, date, index)
        custom_variables = {index: index_image.select(index)}

        # Calculate phytomass
        phytomass_image, r_squared = calculate_phytomass(index_image, 'Custom', custom_formula, custom_variables)

        # Calculate the mean value of the index and the sum of the phytomass
        index_mean = calculate_mean(index_image, commune_geometry).get(index)
        phytomass_sum = calculate_sum(phytomass_image, commune_geometry).get('Phytomass')
        # Calculate the area in square meters
        area_sq_meters = commune_geometry.area().getInfo()

        # Convert the area to hectares
        area_hectares = area_sq_meters / 10000

        # Streamlit App

        # Store the results in session state
        st.session_state['results'] = {
            'index_mean': index_mean,
            'phytomass_sum': phytomass_sum,
            'r_squared': r_squared,
            'area_hectares' :area_hectares
        }

        # Prepare layers for the map
        st.session_state.map_layers = []  # Reset layers
        index_params = {
            'min': index_image.reduceRegion(ee.Reducer.min(), commune_geometry).getInfo()[index],
            'max': index_image.reduceRegion(ee.Reducer.max(), commune_geometry).getInfo()[index],
            'palette': ['blue', 'green', 'yellow']
        }
        st.session_state.map_layers.append(geemap.ee_tile_layer(index_image, index_params, 'Vegetation Index'))

        phytomass_params = {
            'min': phytomass_image.reduceRegion(ee.Reducer.min(), commune_geometry).getInfo()['Phytomass'],
            'max': phytomass_image.reduceRegion(ee.Reducer.max(), commune_geometry).getInfo()['Phytomass'],
            'palette': ['yellow', 'orange', 'red']
        }
        st.session_state.map_layers.append(geemap.ee_tile_layer(phytomass_image, phytomass_params, 'Phytomass'))

        st.session_state.map_layers.append(
            folium.GeoJson(
                geometry_info,
                name="Commune Boundary",
                style_function=lambda x: {'color': 'red', 'weight': 2, 'fillOpacity': 0}
            )
        )

        # Generate download links and store in session state
        phytomass_download_link = get_download_link(phytomass_image, commune_geometry, scale=10, filename='phytomass_map')
        index_download_link = get_download_link(index_image, commune_geometry, scale=10, filename='index_map')
        st.session_state['download_links'] = {
            'phytomass': phytomass_download_link,
            'index': index_download_link
        }

    except ValueError as e:
        st.error(f"Error: {e}")

# Display results in a stylish way
# Afficher les résultats de manière élégante
if 'results' in st.session_state:
    results = st.session_state['results']
    index_mean = round(results['index_mean'], 2)  # Arrondi à 2 décimales
    phytomass_sum = round(results['phytomass_sum'], 2)  # Arrondi à 2 décimales
    area_hectares=round(results['area_hectares'], 2)
    # Créer un conteneur pour les résultats
    st.markdown("### Résumé du processus")
    st.markdown(f"""
    2. **Date de l'analyse** : {selected_date.strftime('%Y-%m-%d')}
    4. **Résultats obtenus** :
    - Valeur moyenne de l'indice de végétation sur la commune : **{index_mean} (sans unité)**.
    - Phytomasse totale dans la commune : **{phytomass_sum/10} UF**.
    - Phytomasse/hectare dans la commune : **{round(phytomass_sum/(area_hectares*10), 2)} UF/ha**.

    5. **Visualisation** : Des cartes pour l'indice de végétation et la phytomasse ont été générées.
    6. **Liens de téléchargement** : Les cartes générées peuvent être téléchargées au format GeoTIFF.
    """)
# Afficher les liens de téléchargement de manière claire et élégante
if 'download_links' in st.session_state:
    download_links = st.session_state['download_links']
    
    # Créer un conteneur pour les liens de téléchargement
    st.markdown("### Liens de téléchargement")
    st.markdown(f"- 🌿 [Télécharger la carte de phytomasse]({download_links['phytomass']})")
    st.markdown(f"- 📈 [Télécharger la carte de l'indice de végétation]({download_links['index']})")

# Create or update the map
Map = geemap.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)

# Add all layers stored in session state
for layer in st.session_state.map_layers:
    Map.add_child(layer)

# Add layer control for toggling visibility
folium.LayerControl().add_to(Map)

# Display the map
st_folium(Map, width=700, height=500, key="main_map")
