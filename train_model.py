import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
import json
import os

# Geocoded locations for Karnataka districts & major localities (Leaflet.js Map)
LOCATION_COORDINATES = {
    "Bengaluru - Indiranagar": {"lat": 12.9784, "lng": 77.6408},
    "Bengaluru - Koramangala": {"lat": 12.9352, "lng": 77.6245},
    "Bengaluru - Whitefield": {"lat": 12.9698, "lng": 77.7500},
    "Bengaluru - Electronic City": {"lat": 12.8452, "lng": 77.6602},
    "Bengaluru - HSR Layout": {"lat": 12.9121, "lng": 77.6445},
    "Bengaluru - Jayanagar": {"lat": 12.9308, "lng": 77.5838},
    "Bengaluru - Hebbal": {"lat": 13.0358, "lng": 77.5970},
    "Bengaluru - Yelahanka": {"lat": 13.1007, "lng": 77.5963},
    "Mysuru - Gokulam": {"lat": 12.3218, "lng": 76.6268},
    "Mysuru - Vijayanagar": {"lat": 12.3364, "lng": 76.6135},
    "Mysuru - Kuvempunagar": {"lat": 12.2858, "lng": 76.6264},
    "Mangaluru - Kadri": {"lat": 12.8797, "lng": 74.8560},
    "Mangaluru - Bejai": {"lat": 12.8872, "lng": 74.8465},
    "Udupi - Manipal": {"lat": 13.3525, "lng": 74.7865},
    "Hubballi - Vidyanagar": {"lat": 15.3647, "lng": 75.1240},
    "Dharwad - Kalyan Nagar": {"lat": 15.4589, "lng": 75.0078},
    "Belagavi - Tilakwadi": {"lat": 15.8361, "lng": 74.5086},
    "Shivamogga - Vinoba Nagar": {"lat": 13.9380, "lng": 75.5681},
    "Tumakuru - Siddaganga Layout": {"lat": 13.3379, "lng": 77.1173},
    "Davangere - MCC B Block": {"lat": 14.4673, "lng": 75.9241},
    "Ballari - Gandhinagar": {"lat": 15.1394, "lng": 76.9214},
    "Kalaburagi - Station Road": {"lat": 17.3297, "lng": 76.8343},
    "Hassan - Kuvempu Nagar": {"lat": 13.0033, "lng": 76.1004}
}

# Base rate in ₹ per sqft per Karnataka locality
LOCALITY_BASE_RATES = {
    "Bengaluru - Indiranagar": 11500,
    "Bengaluru - Koramangala": 10800,
    "Bengaluru - Jayanagar": 9800,
    "Bengaluru - HSR Layout": 8200,
    "Bengaluru - Hebbal": 7400,
    "Bengaluru - Whitefield": 7100,
    "Bengaluru - Yelahanka": 5200,
    "Bengaluru - Electronic City": 4800,
    "Mysuru - Gokulam": 6400,
    "Mysuru - Vijayanagar": 5800,
    "Mysuru - Kuvempunagar": 5200,
    "Mangaluru - Kadri": 6800,
    "Mangaluru - Bejai": 6200,
    "Udupi - Manipal": 5600,
    "Hubballi - Vidyanagar": 4800,
    "Dharwad - Kalyan Nagar": 4200,
    "Belagavi - Tilakwadi": 4500,
    "Tumakuru - Siddaganga Layout": 4100,
    "Shivamogga - Vinoba Nagar": 3900,
    "Davangere - MCC B Block": 3800,
    "Ballari - Gandhinagar": 3600,
    "Hassan - Kuvempu Nagar": 3500,
    "Kalaburagi - Station Road": 3400
}

def generate_karnataka_dataset(n_samples=2500, random_seed=42):
    np.random.seed(random_seed)
    locations = list(LOCALITY_BASE_RATES.keys())
    
    data = []
    for _ in range(n_samples):
        loc = np.random.choice(locations)
        sqft = int(np.random.uniform(550, 4800))
        
        if sqft < 900:
            bhk = np.random.choice([1, 2], p=[0.75, 0.25])
        elif sqft < 1600:
            bhk = np.random.choice([2, 3], p=[0.6, 0.4])
        elif sqft < 2700:
            bhk = np.random.choice([3, 4], p=[0.65, 0.35])
        else:
            bhk = np.random.choice([4, 5], p=[0.7, 0.3])
            
        bath = int(np.clip(bhk - np.random.choice([0, 1], p=[0.7, 0.3]) + np.random.choice([0, 1], p=[0.85, 0.15]), 1, 6))
        age = int(np.random.uniform(0, 30))
        
        base_rate = LOCALITY_BASE_RATES[loc]
        raw_price_inr = (sqft * base_rate) + (bhk * 250000) + (bath * 180000) - (age * 35000)
        noise = np.random.normal(0, raw_price_inr * 0.045)
        final_price_inr = max(1200000, round(raw_price_inr + noise, -3))
        price_lakhs = round(final_price_inr / 100000.0, 2)
        price_per_sqft = round(final_price_inr / sqft, 2)
        
        data.append({
            "location": loc,
            "total_sqft": sqft,
            "bhk": bhk,
            "bath": bath,
            "age": age,
            "price_lakhs": price_lakhs,
            "price_inr": final_price_inr,
            "price_per_sqft": price_per_sqft
        })
        
    df = pd.DataFrame(data)
    df = df[df["total_sqft"] / df["bhk"] >= 250].reset_index(drop=True)
    return df

def train_and_save_ml_pipeline():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "house_data.csv")
    model_path = os.path.join(script_dir, "house_model.pkl")
    meta_path = os.path.join(script_dir, "model_metadata.json")
    
    print("Generating Karnataka Real Estate Dataset...")
    df = generate_karnataka_dataset()
    df.to_csv(data_path, index=False)
    print(f"Saved {len(df)} cleaned dataset records to {data_path}")
    
    X = df[["location", "total_sqft", "bhk", "bath", "age"]]
    y = df["price_lakhs"]
    
    categorical_cols = ["location"]
    numerical_cols = ["total_sqft", "bhk", "bath", "age"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols)
        ]
    )
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    lr_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression())
    ])
    lr_pipeline.fit(X_train, y_train)
    lr_pred = lr_pipeline.predict(X_test)
    lr_r2 = r2_score(y_test, lr_pred)
    lr_mae = mean_absolute_error(y_test, lr_pred)
    
    rf_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=160, max_depth=14, random_state=42))
    ])
    rf_pipeline.fit(X_train, y_train)
    rf_pred = rf_pipeline.predict(X_test)
    rf_r2 = r2_score(y_test, rf_pred)
    rf_mae = mean_absolute_error(y_test, rf_pred)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
    
    residuals = y_test - rf_pred
    residual_std = float(np.std(residuals))
    
    print("\n--- Model Evaluation Comparison ---")
    print(f"Linear Regression   -> R^2 Score: {lr_r2:.4f}, MAE: INR {lr_mae:.2f} Lakhs")
    print(f"Random Forest (Best)-> R^2 Score: {rf_r2:.4f}, MAE: INR {rf_mae:.2f} Lakhs, RMSE: INR {rf_rmse:.2f} Lakhs")
    
    joblib.dump(rf_pipeline, model_path)
    print(f"Saved trained Random Forest model to {model_path}")
    
    cat_encoder = rf_pipeline.named_steps["preprocessor"].named_transformers_["cat"]
    cat_names = cat_encoder.get_feature_names_out(categorical_cols).tolist()
    all_feature_names = numerical_cols + cat_names
    importances = rf_pipeline.named_steps["regressor"].feature_importances_.tolist()
    
    importance_map = dict(zip(all_feature_names, importances))
    
    loc_summary = {}
    for loc, group in df.groupby("location"):
        loc_summary[loc] = {
            "avg_price_lakhs": round(float(group["price_lakhs"].mean()), 2),
            "avg_price_per_sqft": round(float(group["price_per_sqft"].mean()), 2),
            "total_properties": int(len(group)),
            "lat": LOCATION_COORDINATES.get(loc, {}).get("lat", 12.9716),
            "lng": LOCATION_COORDINATES.get(loc, {}).get("lng", 77.5946)
        }
        
    metadata = {
        "models_evaluated": {
            "LinearRegression": {"r2_score": round(lr_r2, 4), "mae_lakhs": round(lr_mae, 2)},
            "RandomForestRegressor": {"r2_score": round(rf_r2, 4), "mae_lakhs": round(rf_mae, 2), "rmse_lakhs": round(rf_rmse, 2)}
        },
        "selected_model": "RandomForestRegressor",
        "r2_score": round(rf_r2, 4),
        "mae_lakhs": round(rf_mae, 2),
        "rmse_lakhs": round(rf_rmse, 2),
        "residual_std_lakhs": round(residual_std, 2),
        "locations": sorted(df["location"].unique().tolist()),
        "location_summary": loc_summary,
        "feature_importances": importance_map,
        "total_properties_in_dataset": len(df),
        "avg_dataset_price_lakhs": round(float(df["price_lakhs"].mean()), 2),
        "avg_dataset_price_per_sqft": round(float(df["price_per_sqft"].mean()), 2),
        "input_ranges": {
            "total_sqft": {"min": int(df["total_sqft"].min()), "max": int(df["total_sqft"].max()), "default": 1450},
            "bhk": {"min": int(df["bhk"].min()), "max": int(df["bhk"].max()), "default": 3},
            "bath": {"min": int(df["bath"].min()), "max": int(df["bath"].max()), "default": 2},
            "age": {"min": int(df["age"].min()), "max": int(df["age"].max()), "default": 4}
        }
    }
    
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata stats to {meta_path}")

if __name__ == "__main__":
    train_and_save_ml_pipeline()