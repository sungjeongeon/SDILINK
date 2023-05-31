import os
import datetime
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.io import loadmat
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.ensemble import IsolationForest
import pickle

import mysql.connector
from mysql.connector import Error

def main():
    # Suppress warnings
    warnings.filterwarnings("ignore")

    df = pd.read_csv('csv_data/cycles_0519_09_10_dataset.csv', infer_datetime_format=True)
    df['Datetime'] = pd.to_datetime(df['Datetime'])

    fuel_cells_df_state_1 = df[df["State"] == 1]
    fuel_cells_df = df[df["State"] == 2]

    # copy before mormalization and after datetime converson to int
    fuel_cells_df_copy = fuel_cells_df.copy()

    cols = ['Voltage-p', 'Voltage-m', 'Voltage-c',
            'Current', 'Temperature-p', 'Temperature-m', 'Capacity','Cycles']   

    mm_scaler = MinMaxScaler()

    fuel_cells_df_copy[cols] = mm_scaler.fit_transform(fuel_cells_df_copy[cols])

    contamination_value = 0.01

    # Create a copy of the original DataFrame to avoid modifying it
    fuel_cells_df_final = fuel_cells_df_copy.copy()

    # Create a variable holding the relevant columns for fitting the model and decision_function
    feature_columns = fuel_cells_df_copy.columns.difference(['BSM-p', 'BSM-m', 'BSM-c','Datetime','State', 'Capacity', 'SOC', 'SOH'])

    # Initialize the IsolationForest model with the desired contamination value
    model = IsolationForest(n_estimators=200, max_samples='auto', contamination=contamination_value, random_state=42)

    # Fit the model with the feature columns
    model.fit(fuel_cells_df_final[feature_columns])

    # Predict the anomaly scores and add them to the DataFrame
    predictions = model.predict(fuel_cells_df_copy[feature_columns])
    fuel_cells_df['anomaly_score' + '_' + str(contamination_value)] = predictions

    # Compute the decision function scores and add them to the DataFrame
    scores = model.decision_function(fuel_cells_df_copy[feature_columns])
    fuel_cells_df['scores' + '_' + str(contamination_value)] = scores

    # 데이터 프레임 합치기
    combined_df = pd.concat([fuel_cells_df, fuel_cells_df_state_1])

    # 'state'와 'cycle' 열로 정렬하기
    df_final = combined_df.sort_values(['State', 'Cycles'])

    df_final = df_final.replace({np.nan: -10})

    # pack_log 데이터 프레임 생성 및 중복 제거
    df_pack_log = df_final[['BSM-p', 'Voltage-p', 'Current', 'Temperature-p', 'State', 'Capacity', 'SOC', 'SOH', 'Cycles', 'Datetime']]
    df_pack_log = df_pack_log.drop_duplicates()

    #module_log 데이터 프레임 생성 및 중복 제거
    df_module_log = df_final[['BSM-p', 'BSM-m', 'Voltage-m', 'Temperature-m', 'Datetime']]
    df_module_log = df_module_log.drop_duplicates()
    
    # cell_log 데이터 프레임 생성 및 중복 제거
    df_cell_log = df_final[['BSM-m', 'BSM-c', 'Voltage-c', 'Datetime', 'anomaly_score_0.01' , 'scores_0.01']]
    df_cell_log = df_cell_log.drop_duplicates()

    # MySQL 접속 정보
    host = 'k8e101.p.ssafy.io'
    user = 'root'
    password = 'P@ssw0rd12'
    database = 'sdilink'

    try:
        connection = mysql.connector.connect(host=host, user=user, password=password, database=database, port=3306)
        cursor = connection.cursor()

        for index, row in df_pack_log.iterrows():
            # pack_log 테이블에 데이터 삽입
            pack_log_query = f"""
                INSERT INTO pack_log
                (car_id, pack_code, voltage_p, current, temp_p, status, capacity, soc, soh, cycle, created_at)
                SELECT 1, '{row['BSM-p']}', {row['Voltage-p']}, {row['Current']}, {row['Temperature-p']}, {row['State']},
                    {row['Capacity']}, {row['SOC']}, {row['SOH']}, {row['Cycles']}, '{row['Datetime']}'
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM pack_log
                    WHERE pack_code = '{row['BSM-p']}' AND created_at = '{row['Datetime']}'
                )
            """
            cursor.execute(pack_log_query)
            connection.commit()

        for index, row in df_module_log.iterrows():
            # module_log 테이블에 데이터 삽입
            module_log_query = f"""
                INSERT INTO module_log
                (pack_log_id, module_code, voltage_m, temp_m, created_at)
                SELECT pl.id, '{row['BSM-m']}', {row['Voltage-m']}, {row['Temperature-m']}, '{row['Datetime']}'
                FROM pack_log AS pl
                WHERE pl.pack_code = '{row['BSM-p']}' AND pl.created_at = '{row['Datetime']}' AND
                    NOT EXISTS (
                        SELECT 1
                        FROM module_log
                        WHERE pack_log_id = pl.id AND module_code = '{row['BSM-m']}' AND created_at = '{row['Datetime']}'
                    )
            """
            cursor.execute(module_log_query)
            connection.commit()

        for index, row in df_cell_log.iterrows():
            # cell_log 테이블에 데이터 삽입
            cell_log_query = f"""
                INSERT INTO cell_log
                (module_log_id, cell_code, voltage_c, is_normal, outlier, created_at)
                SELECT ml.id, '{row['BSM-c']}', {row['Voltage-c']}, {row['anomaly_score_0.01']}, {row['scores_0.01']}, '{row['Datetime']}'
                FROM module_log AS ml
                JOIN pack_log AS pl ON ml.pack_log_id = pl.id
                WHERE ml.module_code = '{row['BSM-m']}' AND ml.created_at = '{row['Datetime']}' AND
                    NOT EXISTS (
                        SELECT 1
                        FROM cell_log
                        WHERE module_log_id = ml.id AND cell_code = '{row['BSM-c']}' AND created_at = '{row['Datetime']}'
            )
            """
            cursor.execute(cell_log_query)
            connection.commit()

    except Error as e:
        print(f"The error '{e}' occurred")

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'connection' in locals() and connection is not None:
            connection.close()
            
if name == "main":
    main()