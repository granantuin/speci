# SPECI Forecasting Model

This repository contains all the necessary files and scripts to train machine learning models for forecasting the probability of issuing a SPECI report at various airports. The repository includes notebooks for training, pre-trained models, deployment scripts, and other resources.

## Table of Contents
- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Usage](#usage)
  - [Training Models](#training-models)
  - [Files Description](#files-description)
- [Deploying the Model](#deploying-the-model)

## Project Overview

This project aims to predict the likelihood of issuing a SPECI report (a special weather observation) within an hour at various airports using machine learning models. The models are trained on data from METAR observations, meteorological variables from the WRF model, and other relevant features. The prediction models are then deployed using a Streamlit application.

## Repository Structure

```bash

├── notebooks/                # Jupyter notebooks for training models (named with ICAO airport codes)
├── models/                   # Pre-trained models (.al files) named with ICAO airport codes
├── data/                     # CSV files containing coordinates of the nearest meteorological model points
├── speci_forecast.py         # Script for deploying the model using Streamlit
├── requirements.txt          # Required Python packages and dependencies
└── README.md                 # Project documentation (this file)
```

## Usage

### Training Models

The models are trained using Jupyter notebooks available in the `notebooks/` directory. Each notebook is specific to an airport, identified by its ICAO code. To train a model:

### Files Description

- **notebooks/**: Contains Jupyter notebooks for training machine learning models for different airports. The notebooks are named according to the ICAO code of the airport (e.g., `LEST.ipynb` for Santiago de Compostela Airport).

- **models/**: Contains pre-trained machine learning models saved as `.al` files. These files are also named according to the ICAO code of the airport.

- **data/**: Contains CSV files with the coordinates of the nearest meteorological model points to each airport.

- **speci_forecast.py**: The main script to deploy the model using Streamlit. This script loads the trained models and allows users to forecast the probability of issuing a SPECI report.

- **requirements.txt**: Lists all the Python packages and dependencies required to run the notebooks and the Streamlit app.


### Deploying the Model

To deploy the model and start the Streamlit app, run the following [link](https://speci-forecast.streamlit.app/)

