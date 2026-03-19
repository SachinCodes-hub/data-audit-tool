#required libraries - stream lit , pandas
import streamlit as st
import pandas as pd
import numpy as np 
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


# data set overview ENDED -------------









########################################################################################################################################################################################################












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






# clean dataset - raw --- clean

# ready for operations 


# dataset cleaning - balanced dataset

# clean dataset - raw --- clean

# ready for operations 
if st.button("Clean Dataset"):
    st.header("Cleaned Dataset -")
    
    import re
    df_cleaned = df.copy()

    
    df_cleaned.columns = (
        df_cleaned.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9_]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )

    df_cleaned = df_cleaned.dropna(how="all").reset_index(drop=True)

    for col in df_cleaned.select_dtypes("object").columns:
        converted = pd.to_numeric(df_cleaned[col], errors="coerce")
        if converted.notnull().mean() > 0.95:
            df_cleaned[col] = converted

    
    placeholders = {"n/a","na","none","null","nil","-","--","?",
                    "unknown","undefined","missing","tbd","tbc","#n/a"}

    for col in df_cleaned.select_dtypes("object").columns:
        df_cleaned[col] = df_cleaned[col].apply(
            lambda x: np.nan if str(x).strip().lower() in placeholders else x)

    df_cleaned = df_cleaned.dropna(thresh=int(0.3 * len(df_cleaned)), axis=1)

    for col in df_cleaned.select_dtypes("number").columns:
        df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())

    for col in df_cleaned.select_dtypes("object").columns:
        df_cleaned[col] = df_cleaned[col].fillna(
            df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else "unknown")

   
    df_cleaned = df_cleaned.drop_duplicates(keep="first").reset_index(drop=True)

    constant_cols = [c for c in df_cleaned.columns if df_cleaned[c].nunique(dropna=True) <= 1]
    df_cleaned = df_cleaned.drop(columns=constant_cols)

    seen = {}
    dup_to_drop = []
    for col in df_cleaned.columns:
        key = tuple(df_cleaned[col].values)
        if key in seen:
            dup_to_drop.append(col)
        else:
            seen[key] = col
    df_cleaned = df_cleaned.drop(columns=dup_to_drop)

    
    for col in df_cleaned.select_dtypes("object").columns:
        df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.lower()

    for col in df_cleaned.select_dtypes("object").columns:
        converted = pd.to_numeric(df_cleaned[col], errors="coerce")
        if converted.notnull().mean() > 0.95:
            df_cleaned[col] = converted

    for col in df_cleaned.select_dtypes("object").columns:
        try:
            parsed = pd.to_datetime(df_cleaned[col], infer_datetime_format=True, errors="coerce")
            if parsed.notnull().mean() > 0.7:
                df_cleaned[col] = parsed.dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    
    for col in df_cleaned.select_dtypes("number").columns:
        Q1, Q3 = df_cleaned[col].quantile(0.25), df_cleaned[col].quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            df_cleaned[col] = df_cleaned[col].clip(lower=Q1 - 3*IQR, upper=Q3 + 3*IQR)

    for col in df_cleaned.select_dtypes("number").columns:
        c = col.lower()
        if any(k in c for k in ["age", "years"]):
            df_cleaned[col] = df_cleaned[col].clip(0, 120)
        if any(k in c for k in ["price", "salary", "cost", "amount"]):
            df_cleaned[col] = df_cleaned[col].clip(lower=0)
        if any(k in c for k in ["percent", "pct", "rate"]):
            df_cleaned[col] = df_cleaned[col].clip(0, 100)

    
    for col in df_cleaned.select_dtypes("number").columns:
        sk = df_cleaned[col].skew()
        if abs(sk) > 2.0 and df_cleaned[col].min() >= 0:
            df_cleaned[col] = np.log1p(df_cleaned[col])

    
    redundant = []
    num_df = df_cleaned.select_dtypes("number")
    if num_df.shape[1] >= 2:
        corr = num_df.corr().abs()
        cols = list(corr.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                if corr.iloc[i, j] > 0.999:
                    redundant.append(cols[j])
    df_cleaned = df_cleaned.drop(columns=list(set(redundant)))

    #difference between the datasets before and after 
    st.subheader("Before vs After Cleaning")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rows before",    df.shape[0])
        st.metric("Columns before", df.shape[1])
        st.metric("Missing before", int(df.isnull().sum().sum()))

    with col2:
        st.metric("Rows after",    df_cleaned.shape[0])
        st.metric("Columns after", df_cleaned.shape[1])
        st.metric("Missing after", int(df_cleaned.isnull().sum().sum()))

    st.subheader("Cleaned Dataset Preview")
    st.dataframe(df_cleaned.head(), use_container_width=True)


    placeholders2 = {"n/a","na","none","null","nil","-","--","?",
                     "unknown","undefined","missing","tbd","tbc","#n/a"}

    null_count2 = df_cleaned.isnull().sum().sum()
    empty_str2 = placeholder_count2 = whitespace_count2 = 0
    for col in df_cleaned.select_dtypes("object").columns:
        vals = df_cleaned[col].dropna().astype(str)
        empty_str2        += (vals.str.strip() == "").sum()
        whitespace_count2 += vals.str.strip().eq("").sum() - (vals == "").sum()
        placeholder_count2 += vals.str.strip().str.lower().isin(placeholders2).sum()
    total_missing2 = null_count2 + empty_str2 + whitespace_count2 + placeholder_count2
    missing_rate2  = total_missing2 / (df_cleaned.shape[0] * df_cleaned.shape[1])
    score_d1_clean = max(0, 100 - missing_rate2 * 100 * 1.5)

    dupe_rate2     = df_cleaned.duplicated().sum() / len(df_cleaned)
    score_d2_clean = max(0, 100 - dupe_rate2 * 100 * 2)

    mixed2 = case2 = enc2 = 0
    for col in df_cleaned.select_dtypes("object").columns:
        vals = df_cleaned[col].dropna()
        if len(vals) == 0:
            continue
        numeric2 = pd.to_numeric(vals, errors="coerce").notnull().sum()
        strings2 = vals.astype(str).str.match(r"^[A-Za-z]").sum()
        if 0 < numeric2 < len(vals) and strings2 > 0:
            mixed2 += 1
        if df_cleaned[col].nunique() <= 100:
            if vals.astype(str).str.strip().str.lower().nunique() < vals.astype(str).str.strip().nunique():
                case2 += 1
        if vals.astype(str).str.contains(r"[^\x00-\x7F]|â€|Ã©|Ã¨", regex=True, na=False).sum() > 0:
            enc2 += 1
    score_d3_clean = max(0, 100 - ((mixed2 + case2 + enc2) / df_cleaned.shape[1]) * 100 * 1.8)

    outlier2 = []
    impossible2 = []
    for col in df_cleaned.select_dtypes("number").columns:
        data2 = df_cleaned[col].dropna()
        if len(data2) < 4:
            continue
        Q1b, Q3b = data2.quantile(0.25), data2.quantile(0.75)
        IQRb = Q3b - Q1b
        if IQRb > 0:
            n_out2 = ((data2 < Q1b - 3*IQRb) | (data2 > Q3b + 3*IQRb)).sum()
            if n_out2 > 0:
                outlier2.append(n_out2)
        c2 = col.lower()
        if any(k in c2 for k in ["age","years"]) and ((data2 < 0) | (data2 > 150)).sum():
            impossible2.append(col)
        if any(k in c2 for k in ["price","salary","cost","amount"]) and (data2 < 0).sum():
            impossible2.append(col)
        if any(k in c2 for k in ["percent","pct","rate"]) and ((data2 < 0) | (data2 > 100)).sum():
            impossible2.append(col)
    total_num2    = sum(df_cleaned[c].dropna().shape[0] for c in df_cleaned.select_dtypes("number").columns)
    outlier_rate2 = sum(outlier2) / max(1, total_num2)
    impossible_rate2 = len(impossible2) / max(1, len(df_cleaned))
    score_d4_clean = max(0, 100 - outlier_rate2 * 60 - impossible_rate2 * 100)

    skewed2 = []
    imbalanced2 = []
    for col in df_cleaned.select_dtypes("number").columns:
        sk2 = df_cleaned[col].skew()
        if abs(sk2) > 2.0:
            skewed2.append(abs(sk2))
    for col in df_cleaned.select_dtypes("object").columns:
        vc2 = df_cleaned[col].value_counts(normalize=True)
        if len(vc2) >= 2 and float(vc2.iloc[0]) > 0.85:
            imbalanced2.append(col)
    skew_pen2   = sum(min(s/20, 0.05) for s in skewed2)
    cat_cols2   = df_cleaned.select_dtypes("object").shape[1]
    imbal_pen2  = (len(imbalanced2) / cat_cols2 * 20) if cat_cols2 > 0 else 0
    score_d5_clean = max(0, 100 - skew_pen2 * 100 - imbal_pen2)

    bad2 = []
    wrong2 = []
    for col in df_cleaned.columns:
        s2 = str(col)
        if s2.strip() == "" or re.match(r"^Unnamed", s2) or re.search(r"[^a-zA-Z0-9_ ]", s2):
            bad2.append(col)
    for col in df_cleaned.select_dtypes("object").columns:
        if pd.to_numeric(df_cleaned[col], errors="coerce").notnull().mean() > 0.95:
            wrong2.append(col)
    row_col_ratio2 = df_cleaned.shape[0] / df_cleaned.shape[1]
    ratio_pen2     = 10 if row_col_ratio2 < 5 else 0
    struct_pen2    = (len(bad2) + len(wrong2)) / df_cleaned.shape[1] * 30
    score_d6_clean = max(0, 100 - struct_pen2 - ratio_pen2)

    high_corr2 = []
    num_df2 = df_cleaned.select_dtypes("number").dropna(axis=1, how="all")
    if num_df2.shape[1] >= 2:
        corr2 = num_df2.corr().abs()
        c2    = corr2.columns
        for i in range(len(c2)):
            for j in range(i + 1, len(c2)):
                if float(corr2.iloc[i, j]) > 0.95:
                    high_corr2.append(1)
    score_d7_clean = max(0, 100 - len(high_corr2) * 3)

    WEIGHTS = {
        "completeness": 0.28, "uniqueness": 0.18, "consistency": 0.16,
        "validity":     0.16, "accuracy":   0.10, "structure":   0.07,
        "correlation":  0.05,
    }
    scores_clean = {
        "completeness": score_d1_clean, "uniqueness": score_d2_clean,
        "consistency":  score_d3_clean, "validity":   score_d4_clean,
        "accuracy":     score_d5_clean, "structure":  score_d6_clean,
        "correlation":  score_d7_clean,
    }
    raw_clean       = sum(WEIGHTS[k] * scores_clean[k] for k in WEIGHTS)
    size_fac_clean  = max(0.5, min(1.0, np.log10(len(df_cleaned) + 1) / 4.0))
    div_bon_clean   = min(1.05, 1 + (df_cleaned.dtypes.nunique() - 1) * 0.01)
    DQS_clean       = round(min(100, max(0, raw_clean * size_fac_clean * div_bon_clean)), 2)

    st.subheader("Dataset Quality Score — After Cleaning")
    st.metric("DQS (Cleaned)", f"{DQS_clean} / 100")

    # file generation clean dataset
    cleaned_csv = df_cleaned.to_csv(index=False).encode("utf-8")
    st.download_button(
        label     = "Download Cleaned Dataset",
        data      = cleaned_csv,
        file_name = "cleaned_dataset.csv",
        mime      = "text/csv"
    )
    
    
    
    
# balanced dataset file generated