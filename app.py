import streamlit as st

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





# Titre principal de l'application
st.title("Application d'Estimation de la Phytomasse")
st.header("🏠 Accueil")
# Description de l'application
st.markdown(
    """
    Cette application est développée dans le cadre d'un **projet de fin d'études (PFE)** à l'Institut Agronomique et Vétérinaire Hassan II (IAV). 
    Elle permet à la **Direction Provinciale d'Agriculture (DPA)** d'estimer les indices de végétation et de calculer la phytomasse pour une province spécifique.
    """
)

# Menu principal avec des boutons pour accéder aux différentes sections
st.markdown("---")
# Afficher le contenu basé sur le choix de l'utilisateur
st.markdown(
    """
    Bienvenue sur l'application d'estimation de la phytomasse !
    Cette plateforme utilise des images satellite pour fournir des estimations précises et utiles pour l'agriculture.
    Utilisez les boutons ci-dessus pour explorer les fonctionnalités.
    """
)
st.header("📈 Evolution")



st.markdown(
    """
    L'application offre la possibilité de visualiser l'évolution d'un indice de végétation donné sur une période sélectionnée. Elle permet également de télécharger ces visualisations sous forme d'image ou de vidéo, offrant ainsi une solution pratique pour analyser et conserver les tendances observées dans les données environnementales.
    """
)

st.image("map1.gif", caption="Geo - Parcours 2024", use_column_width=True)
st.header("🌿 Phytomasse")
st.markdown(
    """
L'application offre la possibilité de télécharger les données calculées, notamment l'indice de végétation et la phytomasse, pour une analyse approfondie. De plus, elle permet de visualiser ces informations directement sur une carte interactive, offrant une expérience utilisateur intuitive et pratique pour explorer les variations spatiales et les tendances des données environnementales.    """
)

st.image("screen.png", caption="Geo - Parcours 2024")
