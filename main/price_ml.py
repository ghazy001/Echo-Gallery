import os, joblib, numpy as np, pandas as pd

ARTIFACT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "art_price_ecom_pipeline.joblib"
)

_bundle = joblib.load(ARTIFACT)
_pipe = _bundle["pipeline"]
_log_target = _bundle["meta"]["log_target"]

def _from_log(y): return np.expm1(y)

CM_PER_INCH = 2.54
def _parse_size(size):
    if size is None: return np.nan, np.nan
    s = str(size).lower()
    units = "cm" if "cm" in s else ("in" if "in" in s or "inch" in s else "cm")
    s = s.replace("inches","").replace("inch","").replace("in","")
    s = s.replace("centimeters","").replace("centimeter","").replace("cm","")
    s = s.replace(" ", "")
    parts = s.split("x")
    if len(parts) != 2: return np.nan, np.nan
    try:
        h = float(parts[0]); w = float(parts[1])
        if units == "in": h*=CM_PER_INCH; w*=CM_PER_INCH
        return h, w
    except:
        return np.nan, np.nan

def predict_price(sample: dict) -> float:
    row = {
        "Name of Painter":           sample.get("artist", ""),
        "Subject of Painting":       sample.get("subject", ""),
        "Style":                     sample.get("style", ""),
        "Medium":                    sample.get("medium", ""),
        "Frame":                     sample.get("frame", ""),
        "Location":                  sample.get("location", ""),
        "Shipment":                  sample.get("shipment", ""),
        "Color Palette":             sample.get("color_palette", ""),
        "Copy or Original":          sample.get("copy_or_original", ""),
        "Print or Real":             sample.get("print_or_real", ""),
        "Recommended Environment":   sample.get("environment", ""),
        "Mood/Atmosphere":           sample.get("mood", ""),
        "Theme/Lighting Requirements": sample.get("lighting", ""),
        "Reproduction Type":         sample.get("reproduction_type", ""),
        "Target Audience":           sample.get("audience", ""),
        "Delivery (days)":           sample.get("delivery_days", np.nan),
    }
    if "height_cm" in sample and "width_cm" in sample:
        h, w = sample["height_cm"], sample["width_cm"]
    else:
        h, w = _parse_size(sample.get("size"))
    row["height_cm"] = h
    row["width_cm"]  = w
    row["area_cm2"] = h * w if (h==h and w==w) else np.nan
    row["aspect_ratio"] = (h / w) if (h==h and w==w and w!=0) else np.nan
    row["artist_popularity"] = np.nan  # unknown at inference time

    X = pd.DataFrame([row])
    pred_log = _pipe.predict(X)[0]
    return float(_from_log(pred_log) if _log_target else pred_log)
