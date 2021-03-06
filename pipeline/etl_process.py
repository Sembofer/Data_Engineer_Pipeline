import requests
import pandas as pd
from sqlalchemy import create_engine
import numpy as np



class Stackoverflow:

    def __init__(self, URL):
        """Extrae los datos abiertos de las ubicaciones
        y alcaldias del sistema de metrobus de la Ciudad de México.


        Args:
            URL (dict): diccionario que contiene las dos URL correspondientes
        """
        for clave in URL:
            self.URL = URL[clave]
            self.response = requests.get(self.URL)
            self.data = self.response.json()
            if clave == 'URL_UBICACIONES':
                self.ubicaciones_df = pd.DataFrame(self.data['result']['records'])
            elif clave == 'URL_ALCALDIAS':
                self.alcaldia_df = pd.DataFrame(self.data['result']['records'])

        #Se ordenan de forma ascendente los DataFrames "self.alcaldia_df" y "self.ubicaciones_df", mdeiante los campos "id" en ambos
        self.alcaldia_df = self.alcaldia_df.sort_values('id')
        self.ubicaciones_df = self.ubicaciones_df.sort_values('id')

        #Lista de las columnas a las que se les cambiará el tipo de dato
        self.positions = ['position_latitude', 'position_longitude']
        #Cambio de tipo de dato de str a float
        self.alcaldia_df[self.positions] = self.alcaldia_df.geo_point_2d.str.split(',', expand=True)
        self.alcaldia_df[self.positions] = self.alcaldia_df[self.positions].astype('float64')

        #Loop para rellenar una lista que contiene el nombre de la alcaldia
        #considerando la distancia mínima de la ubicación de metrobus con la alcaldía
        self.alcaldia_id_list =[]
        for i in self.ubicaciones_df.index:
            self.dist = []      # Lista de las distancias de dada ubicacion con cada una de las alcaldias
            self.x = self.ubicaciones_df.position_latitude[i]   # latitud de la ubicacion
            self.y = self.ubicaciones_df.position_longitude[i]  # longitud de la ubicacion
            self.totalAlcaldias = len(self.alcaldia_df.id) -1
            for index in range(self.totalAlcaldias):
                self.alcaldia_x = self.alcaldia_df.position_latitude[index] # latitud de la alcaldia
                self.alcaldia_y =self.alcaldia_df.position_longitude[index] # longitud de la alcaldia

                #Se calculan las distancias
                self.distan = (self.x - self.alcaldia_x)**2 + (self.y - self.alcaldia_y)**2
                self.dist.append(self.distan)

            # Seleccionar la minima distancia y busca dicha alcaldia mediante el indice
            self.minimaDistancia = min(self.dist) # toma la minima distancia de las 16
            self.indiceMinimaDistancia = self.dist.index(self.minimaDistancia) # toma el indice
            self.id_alcaldia_i = self.alcaldia_df.iloc[self.indiceMinimaDistancia, 1]   #guarda el id de esa minima distancia

            #Guarda el id de la alcaldia en la lista
            self.alcaldia_id_list.append(self.id_alcaldia_i)

        #Se agrega la columna "alcaldia_id" de acuerdo a cada ubicación
        self.ubicaciones_df = self.ubicaciones_df.assign(alcaldia_id = self.alcaldia_id_list)


    def load_data(self, ENGINE):
        """Guarda los dataframes en la base de datos como tablas

        Args:
            ENGINE (str): Credencial para el motor de la base de datos
        """
        self.engine = create_engine(ENGINE)
        self.alcaldia_df.to_sql('alcaldias', con = self.engine, if_exists= 'replace')
        self.ubicaciones_df.to_sql('ubicaciones', con = self.engine, if_exists = 'replace')