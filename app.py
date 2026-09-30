from flask import Flask, render_template, request, jsonify, make_response
import pandas as pd
import numpy as np
import joblib
import json
import os
import database as db
from pdf_generator import generate_valuation_pdf
from train_model import train_and_save_ml_pipeline

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "house_model.pkl")
META_PATH = os.path.join(BASE_DIR, "model_metadata.json")
DATASET_PATH = os.path.join(BASE_DIR, "house_data.csv")

model_pipeline = None
metadata = None
dataset_df = None

def init_resources():
    global model_pipeline, metadata, dataset_df
    db.init_db()
    if not os.path.exists(MODEL_PATH) or not os.path.exists(META_PATH):
        print("Training ML model & generating dataset...")
        train_and_save_ml_pipeline()
        
    model_pipeline = joblib.load(MODEL_PATH)
    with open(META_PATH, "r") as f:
        metadata = json.load(f)
    if os.path.exists(DATASET_PATH):
        dataset_df = pd.read_csv(DATASET_PATH)

init_resources()

# Page Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict")
def predict_page():
    return render_template("predict.html")

@app.route("/compare")
def compare_page():
    return render_template("compare.html")

@app.route("/map")
def map_page():
    return render_template("map.html")

@app.route("/affordability")
def affordability_page():
    return render_template("affordability.html")

@app.route("/history")
def history_page():
    return render_template("history.html")

@app.route("/favorites")
def favorites_page():
    return render_template("favorites.html")

@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")

# API Endpoints
@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    return jsonify(metadata)

@app.route("/marketplace")
def marketplace_page():
    return render_template("marketplace.html")

@app.route("/api/marketplace-estimate", methods=["POST"])
def api_marketplace_estimate():
    try:
        data = request.json or {}
        mode = (data.get("mode") or "buy").lower()
        location = data.get("location")
        sqft = float(data.get("total_sqft", 0))
        bhk = int(data.get("bhk", 0))
        bath = int(data.get("bath", 0))
        age = int(data.get("age", 0))

        if not location or sqft <= 0 or bhk <= 0 or bath <= 0 or age < 0:
            return jsonify({"error": "Invalid property inputs provided."}), 400

        input_df = pd.DataFrame([{
            "location": location,
            "total_sqft": sqft,
            "bhk": bhk,
            "bath": bath,
            "age": age
        }])

        pred_lakhs = float(model_pipeline.predict(input_df)[0])
        pred_lakhs = max(5.0, round(pred_lakhs, 2))
        pred_inr = float(round(pred_lakhs * 100000.0, -2))
        price_per_sqft = round(pred_inr / sqft, 2)

        loc_info = metadata.get("location_summary", {}).get(location, {})
        loc_avg_pps = loc_info.get("avg_price_per_sqft", price_per_sqft)

        if mode == "buy":
            headline = "Estimated buy price"
            tag = "Recommended buying range"
            target = pred_lakhs
            target_label = f"₹{pred_lakhs:.2f} Lakhs"
            detail = f"This home is estimated at ₹{pred_lakhs:.2f} Lakhs in {location}."
            summary = f"Buyer value benchmark: ₹{loc_avg_pps:,.2f}/sqft in {location}."
            action = "Buy recommendation"
        elif mode == "sell":
            target = round(pred_lakhs * 0.97, 2)
            headline = "Suggested selling price"
            tag = "Seller price guidance"
            target_label = f"₹{target:.2f} Lakhs"
            detail = f"Suggested sale price in {location}: ₹{target:.2f} Lakhs."
            summary = f"Market signal is near the local benchmark of ₹{loc_avg_pps:,.2f}/sqft."
            action = "Sell recommendation"
        else:
            monthly_rent = round(pred_inr * 0.0035, 0)
            target = monthly_rent
            headline = "Estimated monthly rent"
            tag = "Rental market estimate"
            target_label = f"₹{monthly_rent:,.0f}/month"
            detail = f"Estimated monthly rent for this {bhk} BHK in {location} is ₹{monthly_rent:,.0f}."
            summary = f"Rental benchmark comparison: ₹{loc_avg_pps:,.2f}/sqft local average."
            action = "Rent recommendation"

        return jsonify({
            "mode": mode,
            "headline": headline,
            "tag": tag,
            "action": action,
            "estimated_value_lakhs": round(target, 2),
            "estimated_value_inr": round(target * 100000.0, 2) if mode in ["buy", "sell"] else round(target, 2),
            "target_label": target_label,
            "detail": detail,
            "summary": summary,
            "price_per_sqft": price_per_sqft,
            "location_avg_pps": loc_avg_pps,
            "location": location,
            "property_summary": f"{bhk} BHK • {bath} bath • {sqft:,.0f} sqft • Age {age} yrs",
            "value_indicator": f"₹{price_per_sqft:,.2f}/sqft"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        data = request.json or {}
        location = data.get("location")
        sqft = float(data.get("total_sqft", 0))
        bhk = int(data.get("bhk", 0))
        bath = int(data.get("bath", 0))
        age = int(data.get("age", 0))

        if not location or sqft <= 0 or bhk <= 0 or bath <= 0 or age < 0:
            return jsonify({"error": "Invalid property inputs provided."}), 400

        input_df = pd.DataFrame([{
            "location": location,
            "total_sqft": sqft,
            "bhk": bhk,
            "bath": bath,
            "age": age
        }])

        pred_lakhs = float(model_pipeline.predict(input_df)[0])
        pred_lakhs = max(5.0, round(pred_lakhs, 2))
        pred_inr = float(round(pred_lakhs * 100000.0, -2))
        price_per_sqft = round(pred_inr / sqft, 2)

        std_residual = metadata.get("residual_std_lakhs", 3.0)
        lower_lakhs = max(4.0, round(pred_lakhs - (1.96 * std_residual), 2))
        upper_lakhs = round(pred_lakhs + (1.96 * std_residual), 2)

        def fmt_inr(amt):
            if amt >= 10000000:
                return f"₹{amt/10000000:.2f} Cr"
            return f"₹{amt/100000:.2f} Lakh"

        loc_info = metadata.get("location_summary", {}).get(location, {})
        loc_avg_pps = loc_info.get("avg_price_per_sqft", price_per_sqft)

        diff_pct = ((price_per_sqft - loc_avg_pps) / loc_avg_pps) * 100
        if diff_pct < -4:
            valuation_badge = "Good Value (Below Locality Avg)"
            badge_color = "success"
        elif diff_pct > 7:
            valuation_badge = "Premium Property (Above Locality Avg)"
            badge_color = "warning"
        else:
            valuation_badge = "Fair Market Value"
            badge_color = "info"

        insights = [
            f"Estimated valuation for this {bhk} BHK property in {location} is {fmt_inr(pred_inr)}.",
            f"Calculated rate is ₹{price_per_sqft:,.2f}/sqft, compared to the locality average of ₹{loc_avg_pps:,.2f}/sqft.",
            f"Statistical 95% confidence valuation interval spans between ₹{lower_lakhs:.2f} Lakhs and ₹{upper_lakhs:.2f} Lakhs."
        ]
        if age <= 3:
            insights.append("Property is almost brand new (≤ 3 years), attracting a 5% to 8% new-construction market premium.")
        elif age > 15:
            insights.append(f"Property age ({age} years) incurs a minor structural depreciation deduction.")

        feat_importances = metadata.get("feature_importances", {})
        explainability = [
            {"feature": "Carpet Area (SqFt)", "importance_pct": round(feat_importances.get("total_sqft", 0.45) * 100, 1)},
            {"feature": f"Locality: {location}", "importance_pct": round(feat_importances.get(f"cat__location_{location}", 0.30) * 100, 1)},
            {"feature": "Bedrooms (BHK)", "importance_pct": round(feat_importances.get("bhk", 0.12) * 100, 1)},
            {"feature": "Bathrooms", "importance_pct": round(feat_importances.get("bath", 0.08) * 100, 1)},
            {"feature": "Property Age", "importance_pct": round(feat_importances.get("age", 0.05) * 100, 1)}
        ]

        pred_id = db.add_prediction(location, sqft, bhk, bath, age, pred_lakhs, pred_inr, price_per_sqft)

        recommendations = []
        if dataset_df is not None:
            filtered = dataset_df[
                (dataset_df["location"] == location) & 
                (dataset_df["bhk"] == bhk)
            ]
            if len(filtered) < 3:
                filtered = dataset_df[dataset_df["location"] == location]
            
            sample_recs = filtered.sample(n=min(3, len(filtered)), random_state=42)
            for _, row in sample_recs.iterrows():
                recommendations.append({
                    "location": row["location"],
                    "total_sqft": int(row["total_sqft"]),
                    "bhk": int(row["bhk"]),
                    "bath": int(row["bath"]),
                    "age": int(row["age"]),
                    "price_lakhs": float(row["price_lakhs"]),
                    "formatted_price": f"₹{row['price_lakhs']:.2f} Lakhs",
                    "price_per_sqft": float(row["price_per_sqft"])
                })

        return jsonify({
            "prediction_id": pred_id,
            "predicted_price_lakhs": pred_lakhs,
            "predicted_price_inr": pred_inr,
            "formatted_price_lakhs": f"₹{pred_lakhs:.2f} Lakhs",
            "formatted_price_inr": fmt_inr(pred_inr),
            "price_range_lakhs": f"₹{lower_lakhs:.2f} Lakhs - ₹{upper_lakhs:.2f} Lakhs",
            "price_per_sqft": price_per_sqft,
            "formatted_pps": f"₹{price_per_sqft:,.2f}/sqft",
            "loc_avg_pps": loc_avg_pps,
            "valuation_badge": valuation_badge,
            "badge_color": badge_color,
            "insights": insights,
            "explainability": explainability,
            "recommendations": recommendations,
            "property_details": {
                "location": location,
                "total_sqft": sqft,
                "bhk": bhk,
                "bath": bath,
                "age": age
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/compare", methods=["POST"])
def api_compare():
    try:
        data = request.json or {}
        prop_a = data.get("propA")
        prop_b = data.get("propB")

        if not prop_a or not prop_b:
            return jsonify({"error": "Missing Property A or Property B details."}), 400

        def evaluate_single(p, label):
            df_in = pd.DataFrame([{
                "location": p["location"],
                "total_sqft": float(p["total_sqft"]),
                "bhk": int(p["bhk"]),
                "bath": int(p["bath"]),
                "age": int(p["age"])
            }])
            pred = float(model_pipeline.predict(df_in)[0])
            pred_inr = pred * 100000.0
            pps = round(pred_inr / float(p["total_sqft"]), 2)
            return {
                "label": label,
                "name": p.get("name", label),
                "location": p["location"],
                "total_sqft": float(p["total_sqft"]),
                "bhk": int(p["bhk"]),
                "bath": int(p["bath"]),
                "age": int(p["age"]),
                "predicted_price_lakhs": round(pred, 2),
                "formatted_price": f"₹{pred:.2f} Lakhs",
                "price_per_sqft": pps
            }

        res_a = evaluate_single(prop_a, "Property A")
        res_b = evaluate_single(prop_b, "Property B")

        price_diff_lakhs = round(abs(res_a["predicted_price_lakhs"] - res_b["predicted_price_lakhs"]), 2)
        pps_diff = round(abs(res_a["price_per_sqft"] - res_b["price_per_sqft"]), 2)
        best_value = res_a if res_a["price_per_sqft"] < res_b["price_per_sqft"] else res_b

        return jsonify({
            "propertyA": res_a,
            "propertyB": res_b,
            "price_diff_lakhs": price_diff_lakhs,
            "pps_diff": pps_diff,
            "best_value_label": best_value["label"],
            "summary_recommendation": f"<b>{best_value['name']}</b> provides a better rate per square foot at <b>₹{best_value['price_per_sqft']:,.2f}/sqft</b>."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/affordability", methods=["POST"])
def api_affordability():
    try:
        data = request.json or {}
        income = float(data.get("monthly_income", 0))
        price = float(data.get("property_price", 0))
        downpayment = float(data.get("down_payment", 0))
        annual_rate = float(data.get("interest_rate", 8.5))
        tenure_years = int(data.get("tenure_years", 20))

        principal = max(0.0, price - downpayment)
        monthly_rate = (annual_rate / 100.0) / 12.0
        n_months = tenure_years * 12

        if monthly_rate > 0 and n_months > 0 and principal > 0:
            emi = principal * monthly_rate * ((1 + monthly_rate)**n_months) / (((1 + monthly_rate)**n_months) - 1)
        else:
            emi = 0.0

        total_repayment = emi * n_months
        total_interest = total_repayment - principal
        emi_income_ratio = round((emi / income * 100.0), 1) if income > 0 else 0

        affordability_status = "Affordable" if emi_income_ratio <= 40 else "High Financial Burden"
        status_color = "success" if emi_income_ratio <= 40 else "warning"

        return jsonify({
            "principal": round(principal, 2),
            "monthly_emi": round(emi, 2),
            "formatted_emi": f"₹{emi:,.2f}",
            "total_interest": round(total_interest, 2),
            "formatted_interest": f"₹{total_interest:,.2f}",
            "total_repayment": round(total_repayment, 2),
            "formatted_repayment": f"₹{total_repayment:,.2f}",
            "emi_income_ratio": emi_income_ratio,
            "affordability_status": affordability_status,
            "status_color": status_color
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history", methods=["GET", "DELETE"])
def api_history():
    if request.method == "DELETE":
        db.clear_prediction_history()
        return jsonify({"message": "History cleared successfully."})
    
    rows = db.get_recent_predictions()
    return jsonify(rows)

@app.route("/api/favorites", methods=["GET", "POST"])
def api_favorites():
    if request.method == "POST":
        data = request.json or {}
        name = data.get("name", "Saved Property")
        loc = data.get("location")
        sqft = float(data.get("total_sqft", 0))
        bhk = int(data.get("bhk", 0))
        bath = int(data.get("bath", 0))
        age = int(data.get("age", 0))
        price_lakhs = float(data.get("price_lakhs", 0))
        pps = float(data.get("price_per_sqft", 0))
        
        fav_id = db.add_favorite(name, loc, sqft, bhk, bath, age, price_lakhs, pps)
        return jsonify({"id": fav_id, "message": "Saved to favorites!"})
        
    rows = db.get_favorites()
    return jsonify(rows)

@app.route("/api/favorites/<int:fav_id>", methods=["DELETE"])
def api_delete_favorite(fav_id):
    db.delete_favorite(fav_id)
    return jsonify({"message": "Favorite deleted."})

@app.route("/api/download-pdf/<int:pred_id>", methods=["GET"])
def download_pdf(pred_id):
    row = db.get_prediction_by_id(pred_id)
    if not row:
        return jsonify({"error": "Prediction record not found"}), 404
        
    prop_details = {
        "location": row["location"],
        "total_sqft": row["total_sqft"],
        "bhk": row["bhk"],
        "bath": row["bath"],
        "age": row["age"]
    }
    
    pred_lakhs = row["predicted_price_lakhs"]
    std_residual = metadata.get("residual_std_lakhs", 3.0)
    lower_lakhs = max(4.0, round(pred_lakhs - (1.96 * std_residual), 2))
    upper_lakhs = round(pred_lakhs + (1.96 * std_residual), 2)
    
    loc_info = metadata.get("location_summary", {}).get(row["location"], {})
    loc_avg_pps = loc_info.get("avg_price_per_sqft", row["price_per_sqft"])
    
    prediction_res = {
        "formatted_price_lakhs": f"₹{pred_lakhs:.2f} Lakhs",
        "formatted_price_inr": f"₹{row['predicted_price_inr']:,.0f}",
        "price_range_lakhs": f"₹{lower_lakhs:.2f} Lakhs - ₹{upper_lakhs:.2f} Lakhs",
        "formatted_pps": f"₹{row['price_per_sqft']:,.2f}/sqft",
        "loc_avg_pps": loc_avg_pps,
        "valuation_badge": "Fair Market Valuation",
        "insights": [
            f"Property valuation calculated using Random Forest Machine Learning pipeline.",
            f"Rate per sqft is ₹{row['price_per_sqft']:,.2f}/sqft for {row['location']} locality."
        ]
    }
    
    pdf_bytes = generate_valuation_pdf(prop_details, prediction_res, metadata)
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=HomeValue_Report_{pred_id}.pdf'
    return response

if __name__ == "__main__":
    print("Starting HomeValue AI Server on http://127.0.0.1:5000...")
    app.run(host="127.0.0.1", port=5000, debug=True)