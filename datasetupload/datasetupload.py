#FILE UPLOAD CODE 1 

import streamlit as st # For file upload
import pandas as pd 

file = st.file_uploader("Upload file (csv , xlsx)" , type =["csv" , "xlsx"] , help = "only upload mention file type") # streamlit has file_uploader lets you upload <200mb and any type of file 

# user ----- CSV file as input . 

#FILE UPLOAD ENDED 

#add when can handle multiple dataset . 
#Multiple files upload - multifile = st.file_uploader("upload CSV , XLSX" , type = ["csv" , "xlsx"] , accept_multiple_files = True )