import pickle
import re
from pathlib import Path

__version__ = "0.1.0"

BASE_DIR = Path(__file__).resolve(strict=True).parent

# Load pickle model
with open(f"{BASE_DIR}/isolation_forest_model-{__version__}.pkl", "rb") as f:
    model = pickle.load(f)

def predict_pipline(bms_data):

    contamination_value = 0.01

    # Create a variable holding the relevant columns for fitting the model and decision_function
    feature_columns = bms_data.columns.difference(['flag','time','datetime'])

    # Use the loaded model for prediction and scoring
    predictions = loaded_model.predict(bms_data[feature_columns])
    scores = loaded_model.decision_function(bms_data[feature_columns])

    # Attach to bms_data dataframe
    bms_data['anomaly_score' + '_' + str(contamination_value)] = predictions
    bms_data['scores' + '_' + str(contamination_value)] = scores

    return bms_data