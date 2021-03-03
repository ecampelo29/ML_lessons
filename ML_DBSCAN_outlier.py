#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 10:00:57 2021

@author: ecampelo
"""

# importações necessárias
import os 
import numpy as np
import pandas as pd
#import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.image as mpimg
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.cluster import DBSCAN

from sklearn.metrics import mean_squared_error, r2_score
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer

import joblib
import urllib

# settings
# Ignore useless warnings (see SciPy issue #5998)
import warnings
warnings.filterwarnings(action="ignore", message="^internal gelsd")

relatorio = os.path.join(os.path.expanduser('~'), 'Documentos', 
                                  'Machine learning', 'Resultados_DBSCAN.txt')

# capturando a imagem usada no livro para mapear os imóveis na califórnia
images_path = relatorio = os.path.join(os.path.expanduser('~'), 'Documentos', 
                                  'Machine learning')
DOWNLOAD_ROOT = "https://raw.githubusercontent.com/ageron/handson-ml2/master/"
filename = "california.png"
url = DOWNLOAD_ROOT + "images/end_to_end_project/" + filename
urllib.request.urlretrieve(url, os.path.join(images_path, filename))

# =============================================================================
# Funções
# =============================================================================
def plot_Anomalies_3D (scan, X, axes, title):
    ax = fig = []
    core_mask = np.zeros_like (scan.labels_, dtype=bool) # cria uma array de false 
    core_mask[scan.core_sample_indices_] = True # deixa como falso apenas os outliers
    anomalies_mask = scan.labels_ == -1 # marca os casos de anomalia
    non_core_mask = ~(core_mask | anomalies_mask) # marca os casos não core
    
    cores = scan.components_
    anomalies = X[anomalies_mask]
    non_cores = X[non_core_mask]
    
    # são 6 pontos e estou imprimindo apenas 3 no Axes3d
    
    axes_lim = [int(np.floor(min(cores[:, axes[0]]))), int(np.ceil(max(cores[:, axes[0]]))),
                int(np.floor(min(cores[:, axes[1]]))), int(np.ceil(max(cores[:, axes[1]]))),
                int(np.floor(min(cores[:, axes[2]]))), int(np.ceil(max(cores[:, axes[2]])))]
    
    fig = plt.figure(figsize = (7,4))
    # ax = fig.add_subplot(111, projection = '3d')
    ax = Axes3D(fig)
    ax.view_init(10, -60)
    plt.scatter(cores[:, axes[0]], cores[:, axes[1]], cores[:,axes[2]],
                c=scan.labels_[core_mask], marker='o', cmap="Paired")
    
    
    plt.scatter(cores[:, axes[0]], cores[:, axes[1]], cores[:,axes[2]], marker='*',  
                    c=scan.labels_[core_mask])
    plt.scatter(anomalies[:, axes[0]], anomalies[:,axes[1]], anomalies[:,axes[2]],
                    c="r", marker="x")
    plt.scatter(non_cores[:, axes[0]], non_cores[:, axes[1]],
                non_cores[:, axes[2]],  c='orange', marker=".")
    plt.title("eps={:.2f}, min_samples={} \n {} x {} x {}".format(
                scan.eps, scan.min_samples, title[0],title[1], title[2]), 
              fontsize=14)
    ax.set_xlim(axes_lim[0:2])
    ax.set_ylim(axes_lim[2:4])
    ax.set_zlim(axes_lim[4:6])
    
    plt.show()


def plot_Anomalies_2D (scan, X, axes, title):
    # são 6 pontos e estou imprimindo apenas 2 no scatter
    core_mask = np.zeros_like (scan.labels_, dtype=bool) # cria uma array de false 
    core_mask[scan.core_sample_indices_] = True # deixa como falso apenas os outliers
    anomalies_mask = scan.labels_ == -1 # marca os casos de anomalia
    non_core_mask = ~(core_mask | anomalies_mask) # marca os casos não core
    
    cores = scan.components_
    anomalies = X[anomalies_mask]
    non_cores = X[non_core_mask]
    
    axes_lim = [int(np.floor(min(cores[:, axes[0]]))), int(np.ceil(max(cores[:, axes[0]]))),
                int(np.floor(min(cores[:, axes[1]]))), int(np.ceil(max(cores[:, axes[1]])))]
    
    fig = plt.figure(figsize = (12,6))
    ax = fig.add_subplot(111)
    
    plt.scatter(cores[:, axes[0]], cores[:, axes[1]],
                c=scan.labels_[core_mask], marker='o', cmap="Paired")
    
    
    plt.scatter(cores[:, axes[0]], cores[:, axes[1]], marker='*',  
                    c=scan.labels_[core_mask])
    plt.scatter(anomalies[:, axes[0]], anomalies[:,axes[1]],
                    c="r", marker="x")
    plt.scatter(non_cores[:, axes[0]], non_cores[:, axes[1]],
                c='orange', marker=".")
        
    ax.set_xlim(axes_lim[0:2])
    ax.set_ylim(axes_lim[2:4])
    
    
    plt.title("eps={:.2f}, min_samples={} \n {} x {}".format(
                scan.eps, scan.min_samples, title[0],title[1]), 
              fontsize=14)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.show()
# =============================================================================
# Processando os dados
# =============================================================================        
download_files = os.path.join(os.path.expanduser('~'), 'Documentos', 
                                  'Machine learning', 'Data_files')
# lendo arquivo
housing = pd.read_csv(download_files+'/housing.csv')

# explorando arquivo
housing.info()

# existem 207 registros sem dados de total_rooms
housing.dropna(inplace=True)

# analise geral
desc = housing.describe()
# total_bedrooms/total_rooms/population aparenta ter outliers extremos
# descobrir a razão do median_income (muito baixo para salário médio)

# distribuições
housing.hist(bins=50, figsize=(30,15))
# housing_median_age -> tem um acúmulo/teto em entorno de 55
# median_house_value -> tem um acúmulo/teto em 500mil
# =============================================================================
# Como a idéia é analisar outlier no preço médio, vou tirar os valores que 
# estão no cap de 500mil que existe no arquivo
# Também serão retirados os median_age que tem cap de 52
# =============================================================================
housing = housing[(housing['median_house_value'] < 500000) & 
                  (housing['housing_median_age'] < 52)]

# separando dados para teste e treino de forma aleatória com proporção de 80/20
house_train, house_test = train_test_split(housing, test_size = 0.2, random_state=42)


num_attrib = ['total_rooms', 'total_bedrooms', 'median_income', 
             'housing_median_age', 'population', 'households', ]
cat_attrib = [ 'ocean_proximity']

num_pipe = Pipeline([
                    ('scaler', StandardScaler()),
                    ])    

house_train_prep = num_pipe.fit_transform(house_train[num_attrib])
house_test_prep = num_pipe.transform(house_test[num_attrib])

# =============================================================================
# variando eps de 0.5 a 1 há melhora na identificação de possíveis anomalia, 
# porém alguns pontos no scatter que poderiam indicar anomalias deixam de ser 
# marcados, visto que aumentamos a distância para que esse ponto possa pertencer
# ou não a um núcleo. Desta forma, temos pontos não núcleos por não terem
# a quantidade mínima para se juntar ao cluster, mais ainda sim não podem
# ser considerados como anomalia. 
# Reduzindo o min_sample diminiu a marcação, chegando a praticamente 0
# quando min_sample tende a 1, porque essa é quantidade de vizinhos que estão
# dentro da distância eps, logo menos vizinhos, menos núcleos construídos.
# =============================================================================
house_scan = DBSCAN(eps=1, min_samples=50) 

house_scan.fit(house_train_prep)

house_scan.labels_[:10]

n_clusters_ = len(set(house_scan.labels_)) - (1 if -1 in house_scan.labels_
                                                      else 0)

############
# scan = house_scan
# X = house_train_prep
columns_trained = num_attrib
axes3d = [4,5,2]
axes2d= [0, 2]

# análise de 3 pontos
plot_Anomalies_3D(house_scan, house_train_prep, axes3d,
                  [columns_trained[axes3d[0]], 
                   columns_trained[axes3d[1]],
                   columns_trained[axes3d[2]]])

# análise de 2 pontos
plot_Anomalies_2D(house_scan, house_train_prep, axes2d, 
                  [columns_trained[axes2d[0]], 
                   columns_trained[axes2d[1]]])

# mostrando os dados no mapa da california
california_img=mpimg.imread(os.path.join(images_path, filename))
ax = housing.plot(kind="scatter", x="longitude", y="latitude", figsize=(10,7),
                  c="median_house_value", cmap=plt.get_cmap("jet"),
                       colorbar=False, alpha=0.4,
                      )               
plt.imshow(california_img, extent=[-124.55, -113.80, 32.45, 42.05], alpha=0.5,
           cmap=plt.get_cmap("jet"))
plt.ylabel("Latitude", fontsize=14)
plt.xlabel("Longitude", fontsize=14)
plt.show()
                  

to do: levar a marcação de anomalias para o mapa da california
# ideia tirada deste paper: https://towardsdatascience.com/dbscan-algorithm-complete-guide-and-application-with-python-scikit-learn-d690cbae4c5d                  
                  
                  
                  
                  