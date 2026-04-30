#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 00:41:37 2026

@author: hamidi
"""


"""
data.py — Chargement et constantes
TPI · Analyse Financière (Dash)
"""

import os
import requests
import pandas as pd
from functools import lru_cache


# ── CHEMINS ───────────────────────────────────────────────────────────────────
BASE_DIR           = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR          = '/Users/hamidi/Desktop/tpi_dash'
GITHUB_RELEASE_URL = "https://github.com/Ihssane-Hamidi/DEFIS_Analyse/releases/download/v1.0/"
FILES = {
    'mq_metriques': 'mq2_metriques.parquet',
    'mq_prix':      'mq2_prix_journaliers.parquet',
    'act_metriques':'act_metriques.parquet',
    'act_prix':     'act_prix_journaliers.parquet',
}

# ── CONSTANTES ────────────────────────────────────────────────────────────────
PERIODS_LABELS = {
    '2023':      '2023',
    '2024':      '2024',
    '2025':      '2025',
    '2023_2025': '2023–2025',
}

QUINTILE_COLORS = {
    'Q1': '#ef4444',
    'Q2': '#f97316',
    'Q3': '#a3a3a3',
    'Q4': '#86efac',
    'Q5': '#16a34a',
}

PLOTLY_LAYOUT = dict(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, t=30, b=0),
)

# ── TÉLÉCHARGEMENT ────────────────────────────────────────────────────────────
def get_parquet(key):
    filename = FILES[key]

    # 1. Local Mac
    local = os.path.join(LOCAL_DIR, filename)
    if os.path.exists(local):
        return local

    # 2. Dossier data/ dans le repo (Render)
    project_data = os.path.join(BASE_DIR, 'data', filename)
    if os.path.exists(project_data):
        return project_data

    # 3. /tmp déjà téléchargé
    tmp_path = os.path.join('/tmp', filename)
    if os.path.exists(tmp_path):
        return tmp_path

    # 4. Téléchargement → /tmp
    url = GITHUB_RELEASE_URL + filename
    print(f"Téléchargement {filename}...")
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    with open(tmp_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)
    return tmp_path

# ── CHARGEMENT (mis en cache) ─────────────────────────────────────────────────
@lru_cache(maxsize=None)
def load_mq():
    return pd.read_parquet(get_parquet('mq_metriques'))

@lru_cache(maxsize=None)
def load_mq_prix():
    df = pd.read_parquet(get_parquet('mq_prix'))
    df.index = pd.to_datetime(df.index)
    return df

@lru_cache(maxsize=None)
def load_act():
    return pd.read_parquet(get_parquet('act_metriques'))

@lru_cache(maxsize=None)
def load_act_prix():
    df = pd.read_parquet(get_parquet('act_prix'))
    df.index = pd.to_datetime(df.index)
    return df

@lru_cache(maxsize=None)
def load_brent():
    filename = 'brent.parquet'
    # Ajoute brent dans FILES et dans GITHUB_RELEASE_URL
    local = os.path.join(LOCAL_DIR, filename)
    if os.path.exists(local):
        df = pd.read_parquet(local)
    else:
        project_data = os.path.join(BASE_DIR, 'data', filename)
        if os.path.exists(project_data):
            df = pd.read_parquet(project_data)
        else:
            url = GITHUB_RELEASE_URL + filename
            print(f"Téléchargement {filename} depuis GitHub...")
            r = requests.get(url, timeout=60)
            r.raise_for_status()  # ← lève une exception si 404 !
            tmp_path = os.path.join('/tmp', filename)
            with open(tmp_path, 'wb') as f:
                f.write(r.content)
            df = pd.read_parquet(tmp_path)

    # Vérifie que la colonne 'Close' existe
    if 'Close' not in df.columns:
        print(f"ERREUR : colonnes disponibles dans brent.parquet : {df.columns.tolist()}")
        raise ValueError("Colonne 'Close' introuvable dans brent.parquet")
    
    series = df['Close'].dropna()
    series.index = pd.to_datetime(series.index)
    return series
    
# ── PRÉPARATION DES DATAFRAMES ────────────────────────────────────────────────
def prepare_valid_mq(df_mq):
    """Filtre et renomme le DataFrame MQ."""
    valid = df_mq[
        df_mq['ticker'].notna() &
        (df_mq['ticker'] != 'None') &
        df_mq['Rendement_2023_2025'].notna()
    ].copy()
    if 'Company Name' not in valid.columns:
        valid = valid.rename(columns={valid.columns[0]: 'Company Name'})
    return valid

def prepare_valid_act(df_act):
    """Filtre et renomme le DataFrame ACT."""
    col_nom = df_act.columns[0]
    valid = df_act[
        df_act['ticker'].notna() &
        (df_act['ticker'] != 'None') &
        df_act['Rendement_2023_2025'].notna()
    ].copy()
    valid = valid.rename(columns={col_nom: 'Company Name'})
    return valid
