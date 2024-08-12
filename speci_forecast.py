# -*- coding: utf-8 -*-
"""speci_forecast.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1uXXiN8QN0ayu2HFn9gb8kdjVpYJqw54_
"""

#!pip install lightgbm==3.1.1

#@title Operational
OACI = "LEVX" #@param ["LEST", "LECO","LEVX"]
print(OACI, "AIRPORT")

#!pip install -r "/content/drive/MyDrive/Colab Notebooks/LEVX_1km/requirements.txt"
import os
import sys
sys.path.append('/content/drive/MyDrive/Colab Notebooks/airport_ml')
import numpy as np
import pandas as pd
from datetime import timedelta
from io import BytesIO
import base64
import pickle
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score
from sklearn.metrics import mean_absolute_error
from IPython.display import display

def Hss(cm):
     """
     obtain de Heidke skill score from a 3x3 confusion matrix (margins=on)

     Returns: Heidke skill score
     """
     if cm.shape == (3,3):
          a = cm.values[0,0]
          b = cm.values[1,0]
          c = cm.values[0,1]
          d = cm.values[1,1]
          HSS = round(2*(a*d-b*c)/((a+c)*(c+d)+(a+b)*(b+d)),2)
     else:
          HSS = 0
     return HSS


def get_metar(oaci,control):
     """
     get metar from IOWA university database

     in: OACI airport code
     Returns
      -------
     dataframe with raw metar.
     """
     #today metar control =True
     if control:
       today = pd.to_datetime("today")+timedelta(1)
       yes = today-timedelta(1)
     else:
        today = pd.to_datetime("today")+timedelta(1)
        yes = today-timedelta(2)

     #url string
     s1="https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station="
     s2="&data=all"
     s3="&year1="+yes.strftime("%Y")+"&month1="+yes.strftime("%m")+"&day1="+yes.strftime("%d")
     s4="&year2="+today.strftime("%Y")+"&month2="+today.strftime("%m")+"&day2="+today.strftime("%d")
     s5="&tz=Etc%2FUTC&format=onlycomma&latlon=no&missing=M&trace=T&direct=no&report_type=1&report_type=2"
     url=s1+oaci+s2+s3+s4+s5
     df_metar_global=pd.read_csv(url,parse_dates=["valid"],).rename({"valid":"time"},axis=1)
     df_metar = df_metar_global[["time",'tmpf', 'dwpf','drct', 'sknt', 'alti','vsby',
                                 'gust', 'skyc1', 'skyc2', 'skyl1', 'skyl2','wxcodes',
                                 "metar"]].set_index("time")

     #temperature dry a dew point to celsius
     df_metar["temp_o"] = ((df_metar.tmpf - 32)*5/9)+273.16
     df_metar["tempd_o"] = ((df_metar.dwpf - 32)*5/9)+273.16

     #QNH to mb
     df_metar["mslp_o"] = np.rint(df_metar.alti*33.8638)

     #visibility SM to meters
     df_metar["visibility_o"] =np.rint(df_metar.vsby/0.00062137)

     #wind direction, intensity and gust
     df_metar["spd_o"] = df_metar["sknt"]*0.514444
     df_metar["dir_o"] = df_metar["drct"]
     df_metar['gust_o'] = df_metar['gust']

     #Add suffix cloud cover and cloud height, present weather, and metar
     df_metar['skyc1_o'] = df_metar['skyc1']
     df_metar["skyl1_o"] = df_metar["skyl1"]
     df_metar['skyc2_o'] = df_metar['skyc2']
     df_metar["skyl2_o"] = df_metar["skyl2"]
     df_metar["wxcodes_o"] = df_metar["wxcodes"]
     df_metar["metar_o"] = df_metar["metar"]

     # Select all columns that do not start with "_o"
     columns_to_keep = [col for col in df_metar.columns if col.endswith("_o")]
     df_metar = df_metar[columns_to_keep]

     return df_metar

def get_meteogalicia_model_4Km(coorde):
    """
    get meteogalicia model (4Km)from algo coordenates
    Returns
    -------
    dataframe with meteeorological variables forecasted.
    """

    #defining url to get model from Meteogalicia server
    var1 = "var=dir&var=mod&var=wind_gust&var=mslp&var=temp&var=rh&var=visibility&var=lhflx"
    var2 = "&var=lwflx&var=conv_prec&var=prec&var=swflx&var=shflx&var=cape&var=cin&var=cfh&var=T850"
    var3 = "&var=cfl&var=cfm&var=cft&var=HGT500&var=HGT850&var=T500&var=snow_prec&var=snowlevel"
    var = var1+var2+var3
    head1="https://mandeo.meteogalicia.es/thredds/ncss/modelos/WRF_HIST/d03"


    #url12="http://mandeo.meteogalicia.es/thredds/ncss/modelos/WRF_HIST/d02/2016/09/wrf_arw_det_history_d02_20160927_0000.nc4?var=mod&disableLLSubset=on&dis
    try:

      today = pd.to_datetime("today")
      head2 = today.strftime("/%Y/%m/wrf_arw_det_history_d03")
      head3 = today.strftime("_%Y%m%d_0000.nc4?")
      head = head1+head2+head3

      f_day=(today+timedelta(days=2)).strftime("%Y-%m-%d")
      tail="&time_start="+today.strftime("%Y-%m-%d")+"T01%3A00%3A00Z&time_end="+f_day+"T23%3A00%3A00Z&accept=csv"

      dffinal=pd.DataFrame()
      for coor in list(zip(coorde.lat.tolist(),coorde.lon.tolist(),np.arange(0,len(coorde.lat.tolist())).astype(str))):
          dffinal=pd.concat([dffinal,pd.read_csv(head+var+"&latitude="+str(coor[0])+"&longitude="+str(coor[1])+tail,).add_suffix(str(coor[2]))],axis=1)

      #filter all columns with lat lon and date
      dffinal=dffinal.filter(regex='^(?!(lat|lon|date).*?)')

      #remove column string between brakets
      new_col=[c.split("[")[0]+c.split("]")[-1] for c in dffinal.columns]
      for col in zip(dffinal.columns,new_col):
          dffinal=dffinal.rename(columns = {col[0]:col[1]})

      dffinal=dffinal.set_index(pd.date_range(start=today.strftime("%Y-%m-%d"), end=(today+timedelta(days=3)).strftime("%Y-%m-%d"), freq="H")[1:-1])
      control = True

    except:

      today = pd.to_datetime("today")-timedelta(1)
      head2 = today.strftime("/%Y/%m/wrf_arw_det_history_d03")
      head3 = today.strftime("_%Y%m%d_0000.nc4?")
      head = head1+head2+head3

      f_day=(today+timedelta(days=2)).strftime("%Y-%m-%d")
      tail="&time_start="+today.strftime("%Y-%m-%d")+"T01%3A00%3A00Z&time_end="+f_day+"T23%3A00%3A00Z&accept=csv"

      dffinal=pd.DataFrame()
      for coor in list(zip(coorde.lat.tolist(),coorde.lon.tolist(),np.arange(0,len(coorde.lat.tolist())).astype(str))):
          dffinal=pd.concat([dffinal,pd.read_csv(head+var+"&latitude="+str(coor[0])+"&longitude="+str(coor[1])+tail,).add_suffix(str(coor[2]))],axis=1)


      #filter all columns with lat lon and date
      dffinal=dffinal.filter(regex='^(?!(lat|lon|date).*?)')

      #remove column string between brakets
      new_col=[c.split("[")[0]+c.split("]")[-1] for c in dffinal.columns]
      for col in zip(dffinal.columns,new_col):
          dffinal=dffinal.rename(columns = {col[0]:col[1]})

      dffinal=dffinal.set_index(pd.date_range(start=today.strftime("%Y-%m-%d"), end=(today+timedelta(days=3)).strftime("%Y-%m-%d"), freq="H")[1:-1])
      control= False


    return dffinal , control

def get_meteogalicia_model_12Km(coorde):
    """
    get meteogalicia model (12Km)from algo coordenates
    Returns
    -------
    dataframe with meteeorological variables forecasted.
    """

    #defining url to get model from Meteogalicia server
    var1 = "var=dir&var=mod&var=wind_gust&var=mslp&var=temp&var=rh&var=visibility&var=lhflx"
    var2 = "&var=lwflx&var=conv_prec&var=prec&var=swflx&var=shflx&var=cape&var=cin&var=cfh&var=T850"
    var3 = "&var=cfl&var=cfm&var=cft&var=HGT500&var=HGT850&var=T500&var=snow_prec&var=snowlevel"
    var = var1+var2+var3
    head1="https://mandeo.meteogalicia.es/thredds/ncss/modelos/WRF_HIST/d02"


    #url12="http://mandeo.meteogalicia.es/thredds/ncss/modelos/WRF_HIST/d02/2016/09/wrf_arw_det_history_d02_20160927_0000.nc4?var=mod&disableLLSubset=on&dis
    try:

      today = pd.to_datetime("today")
      head2 = today.strftime("/%Y/%m/wrf_arw_det_history_d02")
      head3 = today.strftime("_%Y%m%d_0000.nc4?")
      head = head1+head2+head3

      f_day=(today+timedelta(days=2)).strftime("%Y-%m-%d")
      tail="&time_start="+today.strftime("%Y-%m-%d")+"T01%3A00%3A00Z&time_end="+f_day+"T23%3A00%3A00Z&accept=csv"

      dffinal=pd.DataFrame()
      for coor in list(zip(coorde.lat.tolist(),coorde.lon.tolist(),np.arange(0,len(coorde.lat.tolist())).astype(str))):
          dffinal=pd.concat([dffinal,pd.read_csv(head+var+"&latitude="+str(coor[0])+"&longitude="+str(coor[1])+tail,).add_suffix(str(coor[2]))],axis=1)

      #filter all columns with lat lon and date
      dffinal=dffinal.filter(regex='^(?!(lat|lon|date).*?)')

      #remove column string between brakets
      new_col=[c.split("[")[0]+c.split("]")[-1] for c in dffinal.columns]
      for col in zip(dffinal.columns,new_col):
          dffinal=dffinal.rename(columns = {col[0]:col[1]})

      dffinal=dffinal.set_index(pd.date_range(start=today.strftime("%Y-%m-%d"), end=(today+timedelta(days=3)).strftime("%Y-%m-%d"), freq="H")[1:-1])
      control = True

    except:

      today = pd.to_datetime("today")-timedelta(1)
      head2 = today.strftime("/%Y/%m/wrf_arw_det_history_d02")
      head3 = today.strftime("_%Y%m%d_0000.nc4?")
      head = head1+head2+head3

      f_day=(today+timedelta(days=2)).strftime("%Y-%m-%d")
      tail="&time_start="+today.strftime("%Y-%m-%d")+"T01%3A00%3A00Z&time_end="+f_day+"T23%3A00%3A00Z&accept=csv"

      dffinal=pd.DataFrame()
      for coor in list(zip(coorde.lat.tolist(),coorde.lon.tolist(),np.arange(0,len(coorde.lat.tolist())).astype(str))):
          dffinal=pd.concat([dffinal,pd.read_csv(head+var+"&latitude="+str(coor[0])+"&longitude="+str(coor[1])+tail,).add_suffix(str(coor[2]))],axis=1)


      #filter all columns with lat lon and date
      dffinal=dffinal.filter(regex='^(?!(lat|lon|date).*?)')

      #remove column string between brakets
      new_col=[c.split("[")[0]+c.split("]")[-1] for c in dffinal.columns]
      for col in zip(dffinal.columns,new_col):
          dffinal=dffinal.rename(columns = {col[0]:col[1]})

      dffinal=dffinal.set_index(pd.date_range(start=today.strftime("%Y-%m-%d"), end=(today+timedelta(days=3)).strftime("%Y-%m-%d"), freq="H")[1:-1])
      control= False


    return dffinal , control


warnings.filterwarnings("ignore")



#score machine learning versus WRF


# Set the directory you want to list algorithms filenames from
algo_dir = "/content/drive/MyDrive/Colab Notebooks/airport_ml/"+OACI+"/algorithms/"

#grid type
k4 = ["LECO","LEST"]
k12 = ["LEBL","LEPP"]

if OACI in k4:
    meteo_model,con = get_meteogalicia_model_4Km(pickle.load(open(algo_dir+os.listdir(algo_dir)[0],"rb"))["coor"])
else:
    meteo_model,con = get_meteogalicia_model_12Km(pickle.load(open(algo_dir+os.listdir(algo_dir)[0],"rb"))["coor"])

#get meteorological model from algorithm file. Select "coor" key to get coordinates. Pick up first algorithm all same coordinates
#meteo_model,con = get_meteogalicia_model_4Km(pickle.load(open(algo_dir+"dir_"+OACI+"_d0.al","rb"))["coor"])

#print(algo_dir+os.listdir(algo_dir)[0])

#add time variables
meteo_model["hour"] = meteo_model.index.hour
meteo_model["month"] = meteo_model.index.month
meteo_model["dayofyear"] = meteo_model.index.dayofyear
meteo_model["weekofyear"] = meteo_model.index.isocalendar().week.astype(int)

#print("meteorological model info")
#print(meteo_model.info())

metars = get_metar(OACI,con)
#print(" ### **Metars**")
#display(metars["metar_o"])


#@title speci direction


#open algorithm dir d0 d1
alg = pickle.load(open(algo_dir+"speci_"+OACI+"_d0.al","rb"))
#alg1 = pickle.load(open(algo_dir+"speci_"+OACI+"_d1.al","rb"))

#select model variables
# ['temp_o', 'tempd_o', 'spd_o', 'visibility_o', 'visibility1', 'cft1', 'prec1',
# 'dir1', 'mod1', 'rh1', 'cfl1', 'wind_gust1', 'hour', 'month',
# 'dayofyear', 'weekofyear']
ml_x_var = pd.concat([meteo_model[:24],metars],axis=1).dropna()
model_x_var = ml_x_var[alg["x_var"]]
#model_x_var1 = meteo_model[24:48][alg1["x_var"]]

# forecat spd from ml
speci_ml = alg["pipe"].predict(model_x_var)
prob_speci_ml = alg["pipe"].predict_proba(model_x_var)
#prob_speci_ml1 = alg1["pipe"].predict_proba(model_x_var1)
#speci_ml1 = alg1["pipe"].predict(model_x_var1)

#set up dataframe forecast machine learning and WRF
df_for = pd.DataFrame({"time":ml_x_var.index,
                       "speci_prob":prob_speci_ml[:, 1]})
df_for = df_for.set_index("time")
df_for['speci_prob'] = df_for['speci_prob'].apply(lambda x: f"{x:.0%}" if pd.notnull(x) else x)
pd.concat([df_for,metars["metar_o"]],axis=1)