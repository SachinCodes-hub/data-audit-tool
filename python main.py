import pandas as pd
import numpy as np

# ==============================
# STEP 1: DATA PROFILER
# ==============================

def profile_data(df):
    profile = {}

    for col in df.columns:
        col_data = df[col]
        info = {}

        # Type detection
        if pd.api.types.is_numeric_dtype(col_data):
            info["type"] = "numerical"
        else:
            info["type"] = "categorical"
        if col.lower() == "id":
            info["type"] = "identifier"

        # Missing %
        missing_percent = col_data.isnull().mean() * 100
        info["missing_percent"] = round(missing_percent, 2)

        # Unique values
        info["unique_values"] = col_data.nunique()

        # Numerical analysis
        if info["type"] == "numerical":
            clean_data = col_data.dropna()

            if len(clean_data) > 0:
                # ✅ Using pandas instead of scipy
                info["skewness"] = round(clean_data.skew(), 2)

                # Outlier detection (IQR)
                Q1 = clean_data.quantile(0.25)
                Q3 = clean_data.quantile(0.75)
                IQR = Q3 - Q1

                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR

                outliers = clean_data[(clean_data < lower) | (clean_data > upper)]
                info["outlier_percent"] = round(len(outliers) / len(clean_data) * 100, 2)
            else:
                info["skewness"] = None
                info["outlier_percent"] = 0

        else:
            info["skewness"] = None
            info["outlier_percent"] = None

        profile[col] = info

    return profile


# ==============================
# STEP 2: DECISION ENGINE
# ==============================

def generate_decisions(profile):
    decisions = {}

    for col, info in profile.items():

        # ✅ Skip identifier columns safely
        if info["type"] == "identifier":
            decisions[col] = []
            continue

        col_decisions = []

        missing = info["missing_percent"]

        # Missing value handling
        if missing > 0:
            if missing < 5:
                col_decisions.append("drop_rows")
            elif missing > 40:
                col_decisions.append("drop_column")
            else:
                if info["type"] == "numerical":
                    if info["skewness"] is not None and abs(info["skewness"]) > 1:
                        col_decisions.append("fill_median")
                    else:
                        col_decisions.append("fill_mean")
                else:
                    col_decisions.append("fill_mode")

        # Outlier handling
        if info["type"] == "numerical":
            if info["outlier_percent"] is not None and info["outlier_percent"] > 5:
                col_decisions.append("handle_outliers")

        # High cardinality
        if info["type"] == "categorical":
            if info["unique_values"] > 50:
                col_decisions.append("high_cardinality")

        decisions[col] = col_decisions

    return decisions


# ==============================
# TEST / RUN
# ==============================

if __name__ == "__main__":
    # Load your dataset
    df = pd.read_csv("test.csv")   # 🔁 change to your file name later

    print("\n=== ORIGINAL DATA ===")
    print(df.head())

    # Step 1: Profile
    profile = profile_data(df)

    print("\n=== PROFILE OUTPUT ===")
    for col, info in profile.items():
        print(f"\nColumn: {col}")
        for key, value in info.items():
            print(f"{key}: {value}")

    # Step 2: Decisions
    decisions = generate_decisions(profile)

    print("\n=== DECISIONS ===")
    for col, dec in decisions.items():
        print(f"{col}: {dec}")