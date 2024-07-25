<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/departures">
  <html>
  <head>
    <title>SNCB Departures </title>
    <h2 id="currentDate"></h2>
    <!--Affichage de la date sur la page HTML-->
    <script>
        function updateCurrentDate() {
          const currentDateElement = document.getElementById("currentDate");
          const currentDate = new Date();
          const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
          const formattedDate = currentDate.toLocaleDateString('en-US', options);
          currentDateElement.textContent = formattedDate;
        }

        // Mettre à jour la date lors du chargement de la page
        window.onload = updateCurrentDate;

        // Mettre à jour la date toutes les secondes (1000 millisecondes)
        setInterval(updateCurrentDate, 1000);
      </script>
    <!--Association de la page HTML au fichier css-->
    <link rel="stylesheet" type="text/css" href="style.css"/>
    <!--Actualiser la page HTML toutes les minutes-->
    <meta http-equiv="refresh" content="60;url=file:///C:/Users/admin/PycharmProjects/SNCB_Disturbances/departures.html"/>
  </head>
  <body>
    <h1>SNCB Departures</h1>
    <!--Création du table-->
    <table border="1">
      <tr>
        <!--Création des colonnes-->
        <th>Delay (min)</th>
        <th>Station</th>
        <th>Time (+2h)</th>
        <th>Vehicle</th>
        <th>Platform</th>
        <th>Canceled</th>
        <th>Left</th>
        <th>Departure Connection</th>
      </tr>
      <xsl:for-each select="departure">
        <tr>
          <!--Remplissage des colonnes avec les données de départs stockées-->
          <td><xsl:value-of select="Delay" /></td>
          <td><xsl:value-of select="Station" /></td>
          <td><xsl:value-of select="Time" /></td>
          <td><xsl:value-of select="Vehicle" /></td>
          <td><xsl:value-of select="Platform" /></td>
          <td><xsl:value-of select="Canceled" /></td>
          <td><xsl:value-of select="Left" /></td>
          <td><xsl:value-of select="Departure_Connection" /></td>
        </tr>
      </xsl:for-each>
    </table>
  </body>
  </html>
</xsl:template>

</xsl:stylesheet>
