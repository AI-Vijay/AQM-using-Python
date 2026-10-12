
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA = "city_hour.csv"
df = pd.read_csv(DATA, low_memory=False)
df = df[df["City"].eq("Mumbai")].copy()
df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
df = df.dropna(subset=["Datetime", "AQI"]).sort_values("Datetime")

features = ["PM2.5","PM10","NO","NO2","NOx","NH3","CO","SO2","O3","Benzene","Toluene","Xylene"]
df["hour"] = df["Datetime"].dt.hour
df["day_of_week"] = df["Datetime"].dt.dayofweek
df["month"] = df["Datetime"].dt.month
df["day_of_year"] = df["Datetime"].dt.dayofyear
features += ["hour","day_of_week","month","day_of_year"]

X, y = df[features], df["AQI"].astype(float)
split = int(len(df) * 0.80)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

model = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("regressor", RandomForestRegressor(
        n_estimators=300, max_depth=18, min_samples_leaf=2,
        random_state=42, n_jobs=-1
    ))
])
model.fit(X_train, y_train)
pred = model.predict(X_test)

print("MAE :", mean_absolute_error(y_test, pred))
print("RMSE:", np.sqrt(mean_squared_error(y_test, pred)))
print("R2  :", r2_score(y_test, pred))

joblib.dump(model, "aqi_mumbai_model.joblib")
print("Saved: aqi_mumbai_model.joblib")
