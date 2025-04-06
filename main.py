import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def load_and_preprocess(filepath):
    df = pd.read_csv(filepath)

    # Filtrace extrémních cen
    df = df[(df['price'] > 100) & (df['price'] < 5000)]

    # Explicitní konverze kategoriálních sloupců na string
    categorical_cols = ['type', 'material', 'suspension_type']
    for col in categorical_cols:
        df[col] = df[col].fillna('missing').astype(str)  # Přidáno ošetření chybějících hodnot

    # Oprava kategorií
    df['condition'] = df['condition'].clip(1, 5)

    # Feature engineering
    df['suspension_type'] = np.where(df['rear_travel'].fillna(0) > 0, 'full', 'hardtail')  # Ošetření NaN
    df['year'] = df['title'].str.extract(r'(\d{4})').astype(float)
    df['age'] = 2025 - df['year'].fillna(2020)  # Imputace chybějících let

    # Extrakce číselných hodnot z wheel_size
    df['wheel_size'] = df['wheel_size'].astype(str).apply(
        lambda x: re.findall(r'\d+\.?\d*', x)[0] if re.findall(r'\d+\.?\d*', x) else np.nan
    ).astype(float)
    df['wheel_size'] = df['wheel_size'].fillna(df['wheel_size'].median())  # Imputace mediánem

    return df.drop(['title', 'url', 'year'], axis=1).dropna(subset=['frame_size', 'wheel_size'])


# Načtení a příprava dat
df = load_and_preprocess('spoj_updated.csv')  # Přidáno volání funkce

# Definice preprocessingu
numeric_features = ['condition', 'frame_size', 'wheel_size', 'front_travel', 'rear_travel', 'age']
categorical_features = ['type', 'material', 'suspension_type']

numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),  # Změna strategie
    ('onehot', OneHotEncoder(handle_unknown='ignore', min_frequency=10))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# Kontrola kategorií
print("\nKontrola kategorií:")
for col in categorical_features:
    print(f"\n{col}:")
    print(df[col].value_counts(dropna=False))
