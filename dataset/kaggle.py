# Install dependencies: pip install kagglehub[pandas-datasets] python-dotenv
import os
import pandas as pd
import kagglehub
from kagglehub.auth import set_kaggle_credentials

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system env vars only

# Get Kaggle credentials from environment variables
kaggle_username = os.getenv("KAGGLE_USERNAME")
kaggle_key = os.getenv("KAGGLE_KEY")

if not kaggle_username or not kaggle_key:
    raise ValueError(
        "Kaggle credentials not found. Please set KAGGLE_USERNAME and KAGGLE_KEY "
        "environment variables or add them to a .env file:\n"
        "KAGGLE_USERNAME=your-username\n"
        "KAGGLE_KEY=your-api-key"
    )

# Set Kaggle credentials
set_kaggle_credentials(username=kaggle_username, api_key=kaggle_key)

# Configure dataset storage location
# For production: Set KAGGLEHUB_CACHE env var to a shared/project location
# Example: export KAGGLEHUB_CACHE=/app/data/kaggle_datasets (Linux) or C:\app\data\kaggle_datasets (Windows)
# For development: Uses default user cache, or set to project-relative path
dataset_cache = os.getenv("KAGGLEHUB_CACHE")
if not dataset_cache:
    # Default to project-relative location for production readiness
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_cache = os.path.join(project_root, "data", "kaggle_datasets")
    os.makedirs(dataset_cache, exist_ok=True)
    os.environ["KAGGLEHUB_CACHE"] = dataset_cache

# Download dataset (will use KAGGLEHUB_CACHE location)
dataset_path = kagglehub.dataset_download("mohdshahnawazaadil/restaurant-dataset")

# Find and load CSV file from original location
csv_path = None
for root, dirs, files in os.walk(dataset_path):
    for file in files:
        if file.endswith('.csv'):
            csv_path = os.path.join(root, file)
            break
    if csv_path:
        break
else:
    raise FileNotFoundError(f"No CSV files found in {dataset_path}")

# Load from original kagglehub cache location
df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} rows from {os.path.basename(csv_path)}")
print(f"Dataset path: {csv_path}")
print("\nFirst 5 records:")
print(df.head())