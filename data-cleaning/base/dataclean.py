#FILE UPLOAD CODE 1 

import streamlit as st 
import pandas as pd # cleaning


file = st.file_uploader("Upload file (csv , xlsx)" , type =["csv" , "xlsx"] , help = "only upload mention file type") # streamlit has file_uploader lets you upload <200mb and any type of file 

# user ----- CSV file as input .

#dataset cleaning , handellingm unwanted errors -


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


# show user dataset- preview

st.dataframe(df.head()) # first 5 rows of dataset
st.dataframe(df.tail()) # last 5 rows 

# show user some basic infomation - 
st.write("uploaded file name" , file.name)
st.write("uploaded file size" , file.size)
st.write("shape of dataset -" , df.shape())
st.write("Coloumns -" , df.columns)

st.write("No of rows ", len(df))
# we have pandas dataframe till now 