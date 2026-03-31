#FILE UPLOAD CODE 1 

import streamlit as st # For file upload
import pandas as pd 
import numpy as np 


# File upload - type - csv / xlsx - max size - 1000 mb
file = st.file_uploader(
    "Upload file (CSV / XLSX)",
    type=["csv", "xlsx"],
    help="Only upload mentioned file types"
)

# ── Main (perform only when file is uploaded )cd 
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

    st.subheader("Data Types") # zeciton 4
    st.dataframe(df.dtypes.rename("dtype").reset_index())

    st.subheader("Statistical Summary") # section 5
    st.dataframe(df.describe(include="all"))

    st.subheader("Memory Usage") # sectin 6
    st.write(f"{df.memory_usage(deep=True).sum():,} bytes")

    st.subheader("Unique Value Count per Column") # section 7 
    st.dataframe(df.nunique().rename("unique_count").reset_index())


# data set overview ENDED 















# Faults in the dataset - DATA SET QUALITY SCORE 

if st.button("Analyse Faults -"):
    st.header("Faults in the dataset -")

    
    # COMPLETENESS  (W = 0.28)
    
    placeholders = {"n/a","na","none","null","nil","-","--","?",
                    "unknown","undefined","missing","tbd","tbc","#n/a"}

    null_count = df.isnull().sum().sum()

    empty_str = placeholder_count = whitespace_count = 0
    for col in df.select_dtypes("object").columns:
        vals = df[col].dropna().astype(str)
        empty_str        += (vals.str.strip() == "").sum()
        whitespace_count += vals.str.strip().eq("").sum() - (vals == "").sum()
        placeholder_count += vals.str.strip().str.lower().isin(placeholders).sum()

    total_missing = null_count + empty_str + whitespace_count + placeholder_count
    missing_rate  = total_missing / (df.shape[0] * df.shape[1])
    score_d1      = max(0, 100 - missing_rate * 100 * 1.5)

   
    #  UNIQUENESS  (W = 0.18)
    
    exact_dupes = df.duplicated().sum()
    dupe_rate   = exact_dupes / len(df)

    dup_cols = []
    cols = list(df.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if df[cols[i]].equals(df[cols[j]]):
                dup_cols.append((cols[i], cols[j]))

    constant_cols = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]

    score_d2 = max(0, 100 - dupe_rate * 100 * 2)

    
    # CONSISTENCY  (W = 0.16)

    mixed_type_cols = []
    case_issue_cols = []
    encoding_issues = []

    for col in df.select_dtypes("object").columns:
        vals = df[col].dropna()
        if len(vals) == 0:
            continue

        numeric = pd.to_numeric(vals, errors="coerce").notnull().sum()
        strings = vals.astype(str).str.match(r"^[A-Za-z]").sum()
        if 0 < numeric < len(vals) and strings > 0:
            mixed_type_cols.append(col)

        if df[col].nunique() <= 100:
            orig  = vals.astype(str).str.strip().nunique()
            lower = vals.astype(str).str.strip().str.lower().nunique()
            if lower < orig:
                case_issue_cols.append(col)

        weird = vals.astype(str).str.contains(
            r"[^\x00-\x7F]|â€|Ã©|Ã¨", regex=True, na=False).sum()
        if weird > 0:
            encoding_issues.append(col)

    total_issue_cols = len(mixed_type_cols) + len(case_issue_cols) + len(encoding_issues)
    issue_rate       = total_issue_cols / df.shape[1]
    score_d3         = max(0, 100 - issue_rate * 100 * 1.8)

   
    #  VALIDITY  (W = 0.16)
    
    outlier_cols = []
    impossible   = []

    for col in df.select_dtypes("number").columns:
        data = df[col].dropna()
        if len(data) < 4:
            continue
        Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            n_out = ((data < Q1 - 3*IQR) | (data > Q3 + 3*IQR)).sum()
            if n_out > 0:
                outlier_cols.append({"col": col, "count": int(n_out)})

        c = col.lower()
        if any(k in c for k in ["age","years"]) and ((data < 0) | (data > 150)).sum():
            impossible.append(col)
        if any(k in c for k in ["price","salary","cost","amount"]) and (data < 0).sum():
            impossible.append(col)
        if any(k in c for k in ["percent","pct","rate"]) and ((data < 0) | (data > 100)).sum():
            impossible.append(col)

    total_num_cells = sum(df[c].dropna().shape[0] for c in df.select_dtypes("number").columns)
    outlier_rate    = sum(o["count"] for o in outlier_cols) / max(1, total_num_cells)
    impossible_rate = len(impossible) / max(1, len(df))
    score_d4        = max(0, 100 - outlier_rate * 60 - impossible_rate * 100)

    
    #  ACCURACY  (W = 0.10)
    
    skewed_cols = []
    imbalanced  = []

    for col in df.select_dtypes("number").columns:
        sk = df[col].dropna().skew()
        if abs(sk) > 2.0:
            skewed_cols.append({"col": col, "skewness": round(float(sk), 3)})

    for col in df.select_dtypes("object").columns:
        vc = df[col].value_counts(normalize=True)
        if len(vc) >= 2 and float(vc.iloc[0]) > 0.85:
            imbalanced.append(col)

    skew_penalty      = sum(min(abs(s["skewness"]) / 20, 0.05) for s in skewed_cols)
    cat_cols          = df.select_dtypes("object").shape[1]
    imbalance_penalty = (len(imbalanced) / cat_cols * 20) if cat_cols > 0 else 0
    score_d5          = max(0, 100 - skew_penalty * 100 - imbalance_penalty)

    
    #  STRUCTURE  (W = 0.07)
    
    import re

    bad_col_names   = []
    wrong_type_cols = []

    for col in df.columns:
        s = str(col)
        if s.strip() == "" or re.match(r"^Unnamed", s) or re.search(r"[^a-zA-Z0-9_ ]", s):
            bad_col_names.append(col)

    for col in df.select_dtypes("object").columns:
        if pd.to_numeric(df[col], errors="coerce").notnull().mean() > 0.95:
            wrong_type_cols.append(col)

    empty_rows    = int(df.isnull().all(axis=1).sum())
    row_col_ratio = df.shape[0] / df.shape[1]
    ratio_penalty = 10 if row_col_ratio < 5 else 0

    struct_penalty = (len(bad_col_names) + len(wrong_type_cols)) / df.shape[1] * 30
    score_d6       = max(0, 100 - struct_penalty - ratio_penalty)

    
    # CORRELATION  (W = 0.05)
    
    high_corr_pairs = []
    redundant_cols  = []

    num_df = df.select_dtypes("number").dropna(axis=1, how="all")
    if num_df.shape[1] >= 2:
        corr = num_df.corr().abs()
        c    = corr.columns
        for i in range(len(c)):
            for j in range(i + 1, len(c)):
                r = float(corr.iloc[i, j])
                if r > 0.95:
                    high_corr_pairs.append({"col_a": c[i], "col_b": c[j], "r": round(r, 4)})
                if r > 0.999:
                    redundant_cols.append(c[j])

    score_d7 = max(0, 100 - len(high_corr_pairs) * 3)

    
    # FINAL — DATASET QUALITY SCORE (DQS)
    
    WEIGHTS = {
        "completeness": 0.28,
        "uniqueness":   0.18,
        "consistency":  0.16,
        "validity":     0.16,
        "accuracy":     0.10,
        "structure":    0.07,
        "correlation":  0.05,
    }

    scores = {
        "completeness": score_d1,
        "uniqueness":   score_d2,
        "consistency":  score_d3,
        "validity":     score_d4,
        "accuracy":     score_d5,
        "structure":    score_d6,
        "correlation":  score_d7,
    }

    raw_score       = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)
    size_factor     = max(0.5, min(1.0, np.log10(len(df) + 1) / 4.0))
    diversity_bonus = min(1.05, 1 + (df.dtypes.nunique() - 1) * 0.01)

    DQS = round(min(100, max(0, raw_score * size_factor * diversity_bonus)), 2)
    
    
    # evalution parameters 
    st.write(f"Completeness : {round(score_d1, 2)}")
    st.write(f" Uniqueness   : {round(score_d2, 2)}")
    st.write(f" Consistency  : {round(score_d3, 2)}")
    st.write(f" Validity     : {round(score_d4, 2)}")
    st.write(f" Accuracy     : {round(score_d5, 2)}")
    st.write(f" Structure    : {round(score_d6, 2)}")
    st.write(f" Correlation  : {round(score_d7, 2)}")
    st.write(f"Raw Score       : {round(raw_score, 2)}")
    st.write(f"Size Factor     : {size_factor}")
    st.write(f"Diversity Bonus : {diversity_bonus}")
    st.write(f"DQS             : {DQS} / 100")
    
    



# dataset analysis done ##########################################################################################################




# dataset cleaning - balanced dataset

# clean dataset - raw --- clean
