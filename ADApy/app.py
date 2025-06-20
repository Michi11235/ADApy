import streamlit as st
import requests

st.title("Cardano ADA Kurs")

url = "https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=eur"
response = requests.get(url)
data = response.json()

price = data["cardano"]["eur"]
st.write(f"Aktueller ADA-Preis: {price} EUR")
