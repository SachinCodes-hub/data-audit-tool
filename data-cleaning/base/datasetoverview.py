#required libraries - stream lit , pandas
import streamlit as st
import pandas as pd

# File upload - type - csv / xlsx - max size - 1000 mb
file = st.file_uploader(
    "Upload file (CSV / XLSX)",
    type=["csv", "xlsx"],
    help="Only upload mentioned file types"
)

# ── Main (perform only when file is uploaded )
if file is not None: # after upload file is not none 

    try:             # execute this if any error occur , except will get executed 
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.name.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            st.error("Unsupported file format. Please upload CSV or XLSX.")
            st.stop()  # stops execution , file format incorrect

        st.success("File uploaded and read successfully!") 

# FILE upload done - layer 1 

    except pd.errors.EmptyDataError: # no data in file #EmptyDataError
        st.error("The uploaded file is empty. Please upload a file with data.") # st.error shows error if encountered 
        st.stop()

    except pd.errors.ParserError: # could not open file - corrupted file . 
        st.error("Could not parse the file. It may be corrupted or badly formatted.")
        st.stop()

    except Exception as e: # unknown / unexpected error occured 
        st.error(f"Unexpected error while reading file: {e}")
        st.stop() # if error is encounterd no point in executing other code 

    #  Dataset Overview (if FILE UPLOADED) 
    st.header("Dataset Overview")

    st.subheader("File Info") # section 1 
    st.write("File name :", file.name)
    st.write("File size :", file.size, "bytes")

    st.subheader("Shape") # section 2 
    st.write("Full shape :", df.shape)
    st.write("Rows       :", df.shape[0])
    st.write("Columns    :", df.shape[1])

    st.subheader("Preview") # section 3 
    st.write("First 5 rows")
    st.dataframe(df.head())
    st.write("Last 5 rows")
    st.dataframe(df.tail())

    st.subheader("Data Types") # seciton 4
    st.dataframe(df.dtypes.rename("dtype").reset_index())

    st.subheader("Statistical Summary") # section 5
    st.dataframe(df.describe(include="all"))

    st.subheader("Memory Usage") # sectin 6
    st.write(f"{df.memory_usage(deep=True).sum():,} bytes")

    st.subheader("Unique Value Count per Column") # section 7 
    st.dataframe(df.nunique().rename("unique_count").reset_index())


# data set overview ENDED 

