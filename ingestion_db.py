import pandas as pd
import os
from sqlalchemy import create_engine
import logging
import time

logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s-%(levelname)s-%(message)s",
    filemode="a"
)
engine=create_engine("sqlite:///inventory.db")
def ingest_db(df, tablename,engine):
    ''' This function will ingest dataframe into database table '''
    df.to_sql(tablename,con=engine, if_exists='replace',index=False)
def load_raw_data():
    '''This function load the csv and ingest into db'''
    start=time.time()
    for file in os.listdir('data'):
        df=pd.read_csv("data/"+file)
        logging.info(f"Ingesting {file} in db")
        ingest_db(df, file[:-4],engine)
    end=time.time()
    total_time=(start-end)/60
    logging.info("Ingestion complete ")
    logging.info(f"Total time taken {total_time} min")
if __name__=='__main__':
    load_raw_data()