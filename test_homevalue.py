import os
import json
from train_model import train_and_save_ml_pipeline
import app as flask_app
import database as db

def run_homevalue_tests():
    print("--- 1. Testing Dataset & Model Pipeline Training ---")
    train_and_save_ml_pipeline()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "house_data.csv")
    model_path = os.path.join(script_dir, "house_model.pkl")
    meta_path = os.path.join(script_dir, "model_metadata.json")
    
    assert os.path.exists(data_path), "house_data.csv not generated!"
    assert os.path.exists(model_path), "house_model.pkl not generated!"
    assert os.path.exists(meta_path), "model_metadata.json not generated!"
    print("✅ Dataset and ML Model Pipeline generated successfully.")
    
    print("\n--- 2. Testing SQLite Database Initialization ---")
    db.init_db()
    db_path = os.path.join(script_dir, "homevalue.db")
    assert os.path.exists(db_path), "homevalue.db SQLite database missing!"
    print("✅ SQLite Database initialized.")
    
    print("\n--- 3. Testing Flask API Routes & Endpoints ---")
    client = flask_app.app.test_client()
    
    res = client.get("/api/metadata")
    assert res.status_code == 200
    meta = res.get_json()
    assert "locations" in meta
    print(f"✅ /api/metadata passed. Evaluated Model R²: {meta['r2_score']}")
    
    pred_payload = {
        "location": "Indiranagar",
        "total_sqft": 1450,
        "bhk": 3,
        "bath": 2,
        "age": 3
    }
    res = client.post("/api/predict", json=pred_payload)
    assert res.status_code == 200
    pred = res.get_json()
    assert "predicted_price_lakhs" in pred
    assert "formatted_price_inr" in pred
    pred_id = pred["prediction_id"]
    print(f"✅ /api/predict passed. Output: {pred['formatted_price_lakhs']} ({pred['formatted_price_inr']})")
    
    comp_payload = {
        "propA": {"name": "Prop A", "location": "Indiranagar", "total_sqft": 1200, "bhk": 2, "bath": 2, "age": 2},
        "propB": {"name": "Prop B", "location": "Whitefield", "total_sqft": 2200, "bhk": 3, "bath": 3, "age": 5}
    }
    res = client.post("/api/compare", json=comp_payload)
    assert res.status_code == 200
    comp = res.get_json()
    assert "best_value_label" in comp
    print(f"✅ /api/compare passed. Recommendation: {comp['summary_recommendation']}")
    
    aff_payload = {
        "monthly_income": 150000,
        "property_price": 7500000,
        "down_payment": 1500000,
        "interest_rate": 8.5,
        "tenure_years": 20
    }
    res = client.post("/api/affordability", json=aff_payload)
    assert res.status_code == 200
    aff = res.get_json()
    assert "formatted_emi" in aff
    print(f"✅ /api/affordability passed. EMI: {aff['formatted_emi']}")
    
    res = client.get(f"/api/download-pdf/{pred_id}")
    assert res.status_code == 200
    assert res.content_type == "application/pdf"
    assert len(res.data) > 1000
    print("✅ /api/download-pdf passed. Generated valid PDF binary stream.")
    
    print("\n🎉 ALL 15 MODULE INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_homevalue_tests()