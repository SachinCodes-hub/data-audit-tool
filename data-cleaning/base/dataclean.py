#FILE UPLOAD CODE 1 

import streamlit as st 
import pandas as pd # cleaning


file = st.file_uploader("Upload file (csv , xlsx)" , type =["csv" , "xlsx"] , help = "only upload mention file type") # streamlit has file_uploader lets you upload <200mb and any type of file 

# user ----- CSV file as input .

#dataset cleaning , handelling unwanted errors -

#data overview - 
📌 Dataset Overview

📂 File Info
- Name
- Size

📊 Shape
- Rows
- Columns

🧾 Columns
(list)

👀 Preview
(table)

📊 Data Types
(table)

📈 Statistics
(table)

🔢 Unique Values
(table)
#file uploaded or not - confirmation

if file is not None:
    st.success("File uploaded successfully !!!")
else :
    st.failed("File is not uploaded yet!!")

    

# created pandas dataframe for analysis 
if file.name is not None:
    if file.name.endswith == ".csv":
        df = pd.read_csv(file)
    if file.name.endswith == ".xlsx":
        df = df.read_excel(file)


# dataset overview - 
st.write("#Dataset Overview -")
st.write("file info -")
st.write("uploaded file name" , file.name)
st.write("uploaded file size" , file.size)

st.write("file shape - ")
st.write("shape of dataset -" , df.shape())
st.write("Coloumns -" , df.columns)
st.write("No of rows ", len(df))

st.write("preview - ")

st.dataframe(df.head()) # first 5 rows 
st.dataframe(df.tail()) # last 5 rows 


st.write("Data types - ")
st.write("datatypes in dataset" , df.dtypes)

st.write("statistics - ")
st.write("statistical summary" , df.describe())


st.write("Memory used - ")
st.write("memory usage" , df.memory_usage())



#data overview of uploaded dataset is done. 



# Button - for analysis 

if st.button("Analyze Data Quality :"):
    




# dataset analysis - 

