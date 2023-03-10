import pandas as pd
import joblib
import streamlit as st
import sys
from transformers import pipeline
from annotated_text import annotated_text

import re, html
from bs4 import BeautifulSoup as BS, NavigableString, SoupStrainer
from html_table_parser import parser_functions
import itertools
import os

import pdfminer
from pdfminer.high_level import extract_text

st.set_page_config(page_title="ESG λΆλ₯", page_icon="π")


# https://huggingface.co/models pre trained models of huggling face ( models)

#https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets ( Streamlit Documentation)

st.title('ESG λΆλ₯ λͺ¨λΈ') #title

# defining variables used as input
nlp_sa = pipeline('text-classification',model='keonju/kobert_ESG')

upload_file = st.file_uploader(label='νμΌμ μλ‘λν΄μ£ΌμΈμ')

def pdf_to_txt(filename):
    text = extract_text(filename)
    return text.split('.')
def save_chap(data_xml, type='μ¬μκ°μ'):  # μ¬μμ κ°μμ

    parser_d0350 = SoupStrainer("section-1")
    if type == 'μ¬μκ°μ':
        section2_pattern = re.compile(
            r"<SECTION-1((?!<SECTION-1)[\S\s\n])*?(D-0-2-0-0)[\S\s\n]*?</SECTION-1>")  # chap4 -> 0400, #cha3 0300
    else:
        section2_pattern = re.compile(r"<SECTION-1((?!<SECTION-1)[\S\s\n])*?(D-0-4-0-0)[\S\s\n]*?</SECTION-1>")
    find_company = re.compile(r'<COMPANY-NAME AREGCIK="[0-9]+">(.+)</COMPANY-NAME>')

    dsd_xml = data_xml.read()
    try:
        dsd_xml = dsd_xml.decode('utf-8')
        dsd_xml = dsd_xml.replace('&cr;', '&#13;')
        dsd_xml = re.sub('(\n|\r)?</*SPAN.*?>(\n|\r)?', '', dsd_xml)
        dsd_xml = html.unescape(dsd_xml)
        com = find_company.search(dsd_xml).group(0)
        com = re.sub('<COMPANY-NAME AREGCIK="[0-9]+">', '', com)
        com = re.sub('</COMPANY-NAME>', '', com)
        section2_section = section2_pattern.search(dsd_xml)
        section2_section = section2_section.group()
    except:
        dsd_xml = dsd_xml.decode('cp949')
        dsd_xml = dsd_xml.replace('&cr;', '&#13;')
        dsd_xml = re.sub('(\n|\r)?</*SPAN.*?>(\n|\r)?', '', dsd_xml)
        dsd_xml = html.unescape(dsd_xml)
        com = find_company.search(dsd_xml).group(0)
        com = re.sub('<COMPANY-NAME AREGCIK="[0-9]+">', '', com)
        com = re.sub('</COMPANY-NAME>', '', com)
        section2_section = section2_pattern.search(dsd_xml)
        section2_section = section2_section.group()



    if section2_section != None:
        remark_page = BS(section2_section, 'lxml', parse_only=parser_d0350).find("section-1")
        remark_page.find().text
        chap6 = [list(text.stripped_strings) for text in remark_page.find_all(recursive=False)]
        lis = list(itertools.chain.from_iterable(chap6))
    else:
        lis = None

    return com,lis

target=''
if upload_file is not None:
    type=upload_file.type

    target2=''
    if 'xml' in type:
        report = st.selectbox('λ³΄κ³ μΆμ λ³΄κ³ μλ₯Ό ν΄λ¦­ν΄μ£ΌμΈμ', ['μ¬μκ°μ', 'κ²½μμκ²¬'])
        if st.button('Run'):
            com, target = save_chap(upload_file,report)

        st.title(com)
        target2 = []
        for i in target:
            c=i.split('.')
            for z in c:
                target2.append(z)

    if 'pdf' in type:
        if st.button('Run'):

            target = pdf_to_txt(upload_file)
            target2 = target

            target2 = list(filter(None, target2))

    sentence_result=nlp_sa(target2)
    for i in range(len(target2)):
        if sentence_result[i]['label'] == 'N':
            result_text = (target2[i],'μ€λ¦½')
        elif sentence_result[i]['label'] == 'E':
            result_text = (target2[i],'νκ²½')
        elif sentence_result[i]['label'] == 'S':
            result_text = (target2[i],'μ¬ν')
        else:
            result_text = (target2[i],'μ§λ°°κ΅¬μ‘°')
        st.write(annotated_text(result_text))