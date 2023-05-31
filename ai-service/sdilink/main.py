import asyncio
import aiomysql
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from app.model.model import predict_pipeline
from app.model.model import __version__ as model_version
from datetime import datetime
from typing import List
import pandas as pd
import numpy as np
from your_script import process_dataframe  # your_script는 작성한 스크립트의 이름이라 가정합니다.

MYSQL_HOST = "aaaaaa"
MYSQL_USER = "test"
MYSQL_PASSWORD = "password"
MYSQL_DATABASE = "sdilink"

class Cell(BaseModel):
    serial: str
    voltage: float

class Module(BaseModel):
    serial: str 
    voltage: int
    temperature: int
    cells: List[Cell]

class Battery(BaseModel):
    serial: str
    voltage: int
    temperature: int
    current: int
    capacity: int
    status: int
    cycle: int
    modules: List[Module]

app = FastAPI()

# 빈 DataFrame 초기화
df = pd.DataFrame()

@app.post("/bms")
async def battery_info(battery: Battery):
    global df
    print("in post, current time : ", datetime.now())
    print(battery)
    
    # battery 데이터를 DataFrame row로 변환
    data = {
        'serial': [battery.serial],
        'voltage': [battery.voltage],
        'temperature': [battery.temperature],
        'current': [battery.current],
        'capacity': [battery.capacity],
        'status': [battery.status],
        'cycle': [battery.cycle]
        # 필요한 다른 데이터도 여기에 추가하세요
    }
    new_row = pd.DataFrame(data)
    
    # DataFrame에 새로운 row 추가
    df = pd.concat([df, new_row], ignore_index=True)

    # 현재 cycle과 이전 cycle 비교
    if len(df) > 1 and df.iloc[-2]['cycle'] != df.iloc[-1]['cycle']:
        # cycle이 바뀌었다면, 데이터 처리 및 MySQL 저장 작업 수행
        df = process_dataframe(df)
        # DataFrame 초기화
        df = pd.DataFrame()

    return {"state": "POST_OK"}

async def get_pool():
    async with aiomysql.create_pool(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DATABASE,
    ) as pool:
        yield pool

async def get_connection(pool):
    async with pool.acquire() as connection:
        yield connection

@app.get("/")
def home():
    return {"health_check": "OK", "model_version": model_version}