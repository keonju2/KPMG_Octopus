import streamlit as st
import pandas as pd
st.set_page_config(page_title="๊ธฐ์ ๋น๊ต", page_icon="๐")


st.button('SK ์ผ๋ฏธ์นผ ESG Score')

st.title('SK ์ผ๋ฏธ์นผ')

st.title('Our ESG Score')
data=pd.read_excel('kpmg/skchem.xlsx',index_col=0)
st.table(data)

st.title('ESG ํ๊ฐ์ ์ ์')
data=pd.read_excel('kpmg/skchem2.xlsx',index_col=0)
st.table(data)


