#!/usr/bin/env python
# coding: utf-8

# In[20]:


import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="DEFIS Pharma", layout="wide")

# =========================
# Chargement des données
# =========================
df = pd.read_csv(
    "/Users/hamidi/Desktop/DEFISpharma_data_solutions/Compact_DATA_DEFIS_CIP_officielle.csv",
    sep="\t",
    engine="python"
    )
df1=pd.read_csv(
    "/Users/hamidi/Desktop/DEFISpharma_data_solutions/COMPACT10_DATA_DEFIS_CIP_officielle.csv",
    sep="\t",
    engine="python"
    )

df=df.drop_duplicates(subset=['Code CIS','CIP13'],keep="first")
df1.head()


# In[29]:


# =========================
# PAGE 1 : Recherche par médicament
# =========================
st.title("💊 Recherche par médicament")

option = st.radio(
    "Choisir le type de recherche :",
    ["Code CIS", "CIP13", "Dénomination"]
)

if option == "Code CIS":
    values = sorted(df["Code CIS"].dropna().unique())
elif option == "CIP13":
    values = sorted(df["CIP13"].dropna().unique())
else:
    values = sorted(df["Dénomination du médicament"].dropna().unique())

search_value = st.selectbox("Choisir un médicament :", values)

# Filtrer le df
if option == "Code CIS":
    med_df = df[df["Code CIS"] == search_value]
elif option == "CIP13":
    med_df = df[df["CIP13"] == search_value]
else:
    med_df = df[df["Dénomination du médicament"] == search_value]

st.subheader("Informations du médicament")
st.dataframe(med_df, use_container_width=True)

# =========================
# PAGE 2 : Analyse laboratoire (SMR + ASMR)
# =========================
st.title("🏭 Analyse laboratoire")

labs = sorted(df["Titulaire(s)"].dropna().unique())
lab_name = st.selectbox("Choisir un laboratoire :", labs)

lab_df = df[df["Titulaire(s)"] == lab_name]

st.subheader("Médicaments du laboratoire")
st.dataframe(lab_df, use_container_width=True)

# Fonction pour générer camembert avec cas spéciaux
def plot_pie_with_special(df_lab, col_valeur, col_libelle, title, official_vals):
    """
    Camembert pour SMR ou ASMR avec gestion des cas spéciaux.
    
    df_lab : dataframe filtrée pour le labo
    col_valeur : nom de la colonne Valeur du SMR ou ASMR
    col_libelle : nom de la colonne Libellé correspondant
    title : titre du graphique
    official_vals : liste des valeurs officielles (SMR ou ASMR)
    """
    df_copy = df_lab.copy()
    
    # Colonne pour le camembert
    def label_pie(val):
        if val in official_vals:
            return val
        elif pd.notna(val):
            return "**"  # cas spécial
        else:
            return None

    df_copy["pie_label"] = df_copy[col_valeur].apply(label_pie)
    
    # Comptage pour le camembert
    pie_counts = df_copy[df_copy["pie_label"].notna()]["pie_label"].value_counts().reset_index()
    pie_counts.columns = ["Valeur", "count"]
    
    # Ordre des catégories
    order_vals = official_vals + ["**"]
    pie_counts["Valeur"] = pd.Categorical(pie_counts["Valeur"], categories=order_vals, ordered=True)
    pie_counts = pie_counts.sort_values("Valeur")
    
    # Création du camembert
    fig = px.pie(pie_counts, names="Valeur", values="count", title=title)
    st.plotly_chart(fig, use_container_width=True)
    
    # Affichage des détails cas spéciaux
    special_mask = df_copy["pie_label"] == "**"
    if special_mask.any():
        st.subheader(f"📝 Détails des cas spéciaux pour {title}")
        for idx, row in df_copy[special_mask].iterrows():
            st.write(f"- {row['Dénomination du médicament']}: {row[col_libelle]}")


# Pour SMR
st.subheader("📊 Répartition SMR")
plot_pie_with_special(
    lab_df, 
    col_valeur="Valeur du SMR", 
    col_libelle="Libellé du SMR", 
    title="Répartition SMR",
    official_vals=["Insuffisant", "Faible", "Modéré", "Important"]
)

# Pour ASMR
st.subheader("📊 Répartition ASMR")
plot_pie_with_special(
    lab_df, 
    col_valeur="Valeur de l’ASMR", 
    col_libelle="Libellé de l’ASMR", 
    title="Répartition ASMR",
    official_vals=["I", "II", "III", "IV", "V"]
)


# =========================
# PAGE 3 : Analyse du CA
# =========================
st.title("💰 Analyse du chiffre d’affaires")

labs_ca = sorted(df1["Titulaire(s)"].dropna().unique())
lab_name_ca = st.selectbox("Choisir un laboratoire pour la ventilation du CA :", labs_ca)

lab_ca_df = df1[df1["Titulaire(s)"] == lab_name_ca]

# CA_groupe pour limiter l'axe Y
ca_groupe_max = lab_ca_df["CA_groupe"].max()

# Histogramme CA par médicament
fig_ca = px.bar(
    lab_ca_df,
    x="Dénomination du médicament",
    y="Revenue_USD",
    title="Ventilation du chiffre d'affaires par médicament",
    labels={"Revenue_USD": "Chiffre d'affaires (USD)"}
)
fig_ca.update_yaxes(range=[0, ca_groupe_max], tickformat=",.0f")
st.plotly_chart(fig_ca, use_container_width=True)

# Camembert poids des médicaments dans le portefeuille
st.subheader("📊 Poids des médicaments dans le portefeuille")
fig_portfolio = px.pie(
    lab_ca_df,
    names="Dénomination du médicament",
    values="Revenue_USD",
    title="Répartition du chiffre d'affaires par médicament"
)
st.plotly_chart(fig_portfolio, use_container_width=True)

# Optionnel : afficher tableau SMR/ASMR pour ces médicaments
st.subheader("📋 Détails SMR et ASMR pour les médicaments du portefeuille")
st.dataframe(
    lab_ca_df[["Dénomination du médicament", "Valeur du SMR", "Libellé du SMR", "Valeur de l’ASMR", "Libellé de l’ASMR"]],
    use_container_width=True
)


# In[2]:





# In[ ]:





# In[ ]:





# In[7]:





# In[ ]:




