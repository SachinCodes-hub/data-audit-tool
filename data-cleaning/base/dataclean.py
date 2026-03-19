#FILE UPLOAD CODE 1 

import streamlit as st 
import pandas as pd # cleaning


file = st.file_uploader("Upload file (csv , xlsx)" , type =["csv" , "xlsx"] , help = "only upload mention file type") # streamlit has file_uploader lets you upload <200mb and any type of file 


# created pandas dataframe for analysis 
if file is not None: # when we have a file
    if file.name.endswith(".csv"): # endswith is not a variable its a method so (argument) . - at the end its a string 
        df = pd.read_csv(file)
    elif file.name.endswith(".xlsx"):  # METHOD - ENDSWITH.
        df = pd.read_excel(file)
    
    # dataset overview - 
    st.header("dataset overview")
    st.write("file info -")
    st.write("uploaded file name" , file.name)
    st.write("uploaded file size" , file.size)

    st.write("file shape - ")
    st.write("shape of dataset -" , df.shape) # shape is not a function
    st.write("Coloumns -" , df.shape[1])
    st.write("No of rows ", df.shape[0])

    st.write("preview - ")

    st.dataframe(df.head()) # first 5 rows 
    st.dataframe(df.tail()) # last 5 rows 


    st.write("Data types - ")
    st.write("datatypes in dataset" , df.dtypes)

    st.write("statistics - ")
    st.write("statistical summary" , df.describe(include ='all'))


    st.write("Memory used - ")
    st.write("memory usage" , df.memory_usage().sum()) # will not give messy info , gives columnwise count of memory.


    st.write("unique value count" , df.nunique())
#data overview of uploaded dataset is done. 





#if st.button("Analyze Data Quality :"): # lets you add the button write all the analysis inside it as user hits the button code inside will get executed . 
    
    
if st.button("Analyze Data Quality"):
    # your analysis code here
    st.write("analysing")



# dataset analysis - 

