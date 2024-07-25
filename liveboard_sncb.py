import time
import requests
from datetime import datetime
import mysql.connector
from lxml import etree
import csv
import re
import pandas as pd


# VALIDATION DE L'XML PAR LE SCHEMA XSD CONCU

# Charger le fichier xml et le preparer a la validation
departuresXml = "departures.xml"
departuresParseXml = etree.parse(departuresXml)
# Obtenir la racine du fichier XML
root = departuresParseXml.getroot()
# Controle s'il y a des departs avant de valider le fichier (A partir de 1h les trains de circulent plus)
if len(root) == 0:
    print("Aucun départ n'a été trouvé dans le fichier XML.")
else:
    # Charger le XSD à partir du fichier
    departuresXsd = "departures.xsd"
    departuresParseXsd = etree.parse(departuresXsd)
    # Schema XML à partir du XSD créé
    schema = etree.XMLSchema(departuresParseXsd)

    # Valider le XML par rapport au XSD
    if schema.validate(departuresParseXml):
        print("Le fichier XML est bien valide par rapport au XSD.")
    else:
        print("Le XML n'est pas valide par rapport au XSD.")
        for error in schema.error_log:
            print(f"Erreur de validation: {error.message} (ligne {error.line}, colonne {error.column})")


# LECTURE DES DEPARTS VIA L'API
# Choix de la station à laquelle l'on veut voir le liveboard
# Recueil de toutes les stations SNCB belges dans une liste à partir du csv

# Spécification du chemin vers le fichier CSV de recueil de toutes les stations belges
station_csv = 'stations.csv'
# Création d'une liste vide pour stocker les noms
station_names = []
# Ouverture du fichier CSV en mode lecture
with open(station_csv, mode='r', newline='') as file:
    csv_reader_stations = csv.reader(file)
    # En-têtes du CSV
    headers = next(csv_reader_stations)
    # Colonnes utiles pour la constitution de la liste des noms des stations belges
    name_column = headers.index('name')  # Colonne "Nom" uniquement
    country_column = headers.index('country-code')  # Colonne "country" uniquement

    # Parcours de chaque ligne du fichier CSV stations pour constituer la liste
    for row_station in csv_reader_stations:
        # Vérifiez si le pays correspond à 'be'
        if row_station[country_column] == 'be':
            # Ajoutez le nom de la station à la liste si la condition est bien remplie
            station_names.append(row_station[name_column])

# Fonction pour controler et recupérer le nom de la station voulue par l'utilisateur
def Station_liveboard_input():
    station_departure = input("Entrer la station dont vous voulez avoir le liveboard : ") #L'utilisateur entre la station dont il souhaite avoir le liveboard
    print("\n")
    while True: #Boucle infinie pour permettre à l'utilisateur de retester en cas d'erreur
        for station in station_names: #Parcours de la liste des noms des stations
            # Création d'un modèle de recherche en ignorant la casse, les tirets et les espaces, on tolère aussi les debuts de nom significatifs sauf bruxelles (car plusieurs stations contiennent bruxelles
            pattern = re.compile(re.escape(station), re.IGNORECASE)
            if pattern.search(re.sub(r'[-/]', '[-/]', station_departure)) or (station_departure.lower() in station.lower() and (station_departure.lower() != 'bruxelles' and station_departure.lower() != 'bruxelle')):
                return station
        station_departure = input("La station entrée n'est pas valide. Veuillez réessayer : ")

# Initialisation de la variable d'input de la station
station_departure = Station_liveboard_input()
#Date actuelle au format ddmmyy et heure actuelle HHMM requises par l'api
while True:
    ddmmyy = datetime.now()
    ddmmyy = ddmmyy.strftime("%d%m%y")
    hhmm = datetime.now()
    hhmm = hhmm.strftime("%H%M")
    # Lien de l'api iRail avec les champs renseignés, les données seront recupérées en JSON
    url = f"https://api.iRail.be/liveboard/?id=&station={station_departure}&date={ddmmyy}&time={hhmm}&arrdep=departure&lang=en&format=json&alerts=true"
    response = requests.get(url) #Requete à l'api pour avoir des données de départ de trains

    if response.status_code == 200: #Réponse favorable renvoyée par une requete http
        departures_data = response.json() #Recupération en JSON
        departures = departures_data.get("departures", {})  # Departs sous forme de dictionnaire
        departure_list = departures.get("departure", [])  # Liste des départs récupérés

        # Crée un élément racine "departures"
        root = etree.Element("departures")
        #Constitution du fichier xml avec les différents départs de la liste fournie par l'api
        for each_departure in departure_list:
            departureTree = etree.Element("departure")
            etree.SubElement(departureTree, "Delay").text = "+"+str(int(int(each_departure["delay"])/60))+"'" #Temps de retard en min et au format "+25'"
            etree.SubElement(departureTree, "Station").text = each_departure["station"]
            formated_time = datetime.utcfromtimestamp(int(each_departure["time"])).strftime("%H:%M")
            time_element = etree.SubElement(departureTree, "Time")
            time_element.text = formated_time
            etree.SubElement(departureTree, "Vehicle").text = each_departure["vehicle"]
            etree.SubElement(departureTree, "Platform").text = each_departure["platform"]
            etree.SubElement(departureTree, "Canceled").text = each_departure["canceled"]
            etree.SubElement(departureTree, "Left").text = each_departure["left"]
            etree.SubElement(departureTree, "Departure_Connection").text = each_departure["departureConnection"]
            root.append(departureTree)

        # Crée un arbre XML à partir de l'élément racine
        xml_tree = etree.ElementTree(root)

        # Enregistre l'arbre XML dans un fichier dont le contenu sera écrasé à chaque mise à jour
        with open("departures.xml", "wb") as departure_xml:
            xml_tree.write(departure_xml, pretty_print=True, xml_declaration=True, encoding="utf-8")

    else:
        print("La requête a échoué avec le code de statut :", response.status_code)

# ECRITURE DES DEPARTS DANS MYSQL
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='$@Nder12',
        database='sncb_db'
    )
    # Definition du curseur pour pointer
    cursor = connection.cursor()
    for departure in root.findall('departure'): #Parcours des différents départs obtenus
        #Recupération des différents paramètres de departs de trains au format text s'ils ne sont pas vides
        delay = departure.find('Delay')
        if delay is not None:
            delay = delay.text
        station = departure.find('Station')
        if station is not None:
            station = station.text
        time_ = departure.find('Time')
        if time_ is not None:
            time_ = time_.text
        vehicle = departure.find('Vehicle')
        if vehicle is not None:
            vehicle = vehicle.text
        platform = departure.find('Platform')
        if platform is not None:
            platform = platform.text
        canceled = departure.find('Canceled')
        if canceled is not None:
            canceled = canceled.text
        left = departure.find('Left')
        if left is not None:
            left = left.text
        departure_connection = departure.find('Departure_Connection')
        if departure_connection is not None:
            departure_connection = departure_connection.text

        # Requete pour selectioner tous les départs existants deja dans la table departures
        select_query = """
            SELECT * FROM departures 
            WHERE delay = %s AND station = %s AND station_departure = %s AND time_ = %s AND vehicle = %s AND platform = %s AND canceled = %s AND `left` = %s AND departure_connection = %s;
            """
        cursor.execute(select_query, (delay, station, station_departure, time_, vehicle, platform, canceled, left, departure_connection))#Exécution de la requete
        # Recupération de la prochaine ligne d'exécution de la requete SELECT précédente
        existing_departure = cursor.fetchone()

        # Si le départ n'existe pas, on l'insère
        if existing_departure is None:
            # Requete d'insertion des départs
            insert_query = """
                INSERT INTO departures (delay, station, station_departure, time_, vehicle, platform, canceled, `left`, departure_connection)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
            cursor.execute(insert_query, (delay, station, station_departure, time_, vehicle, platform, canceled, left, departure_connection))
    print("Données bien sauvegardées dans la base de données MYSQL")

    # Extraire les noms de stations uniques à partir de la table departure
    cursor.execute("SELECT DISTINCT station FROM departures")
    stations = [row[0] for row in cursor.fetchall()]

    # Insérer les caractéristiques des stations dans la table station
    # Rechercher les caractéristiques de la station à partir du DataFrame station_data
    df_stations = pd.read_csv('stations.csv')
    for station in stations:
        station_data = df_stations[df_stations['name'] == station]
        if not station_data.empty:
            uri = station_data['URI'].values[0]
            name = station_data['name'].values[0]
            country_code = station_data['country-code'].values[0]
            longitude = station_data['longitude'].values[0]
            latitude = station_data['latitude'].values[0]
            avg_stop_times = station_data['avg_stop_times'].values[0]
            # Requete pour selectioner tous les départs existants deja dans la table station pour éviter les doublons
            select_query = """
                        SELECT * FROM station 
                        WHERE uri = %s AND name = %s AND country_code = %s AND longitude = %s AND latitude = %s AND avg_stop_times = %s ;
                        """
            cursor.execute(select_query, (uri, name, country_code, longitude, latitude, avg_stop_times))  # Exécution de la requete
            # Recupération de la prochaine ligne d'exécution de la requete SELECT précédente
            existing_departure = cursor.fetchone()

            # Si le départ n'existe pas, on l'insère
            if existing_departure is None:
                # Requete INSERT INTO pour insérer les données dans la table station
                insert_query = "INSERT INTO station (uri, name, country_code, longitude, latitude, avg_stop_times) VALUES (%s, %s, %s, %s, %s, %s)"
                data = (uri, name, country_code, longitude, latitude, avg_stop_times)
                cursor.execute(insert_query, data)
    # Enrégistrement dans la base de données
    connection.commit()
    # Fermeture du curseur
    cursor.close()
    # Déconnexion de MYSQL
    connection.close()

# GENERATION DE LA PAGE XHTML departures.html VIA LE departures.xslt ET departures.xml
    # Charger le fichier XML
    departuresXml = "departures.xml"
    departuresParseXml = etree.parse(departuresXml)

    # Charger le fichier XSLT
    departuresXslt = "departures.xslt"
    departuresParseXslt = etree.parse(departuresXslt)
    # Création du transformateur xslt
    xslt_transformer = etree.XSLT(departuresParseXslt)

    # Appliquer la transformation sur le fichier XML (XSLT+XML)
    xmlWithXslt = xslt_transformer(departuresParseXml)

    # Enregistrer le résultat dans le fichier departures.html
    departures_html = "departures.html"
    xmlWithXslt.write(departures_html, pretty_print=True, method="html")
    print(f"La transformation a été effectuée avec succès. Le liveboard de la station {station_departure} peut etre consulté sur {departures_html}.")
    print("\n")

    # temps de mise à jour du liveboard
    time.sleep(60)
