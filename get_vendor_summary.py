import sqlite3
import pandas as pd
import logging
from ingestion_db import ingest_db
import os
os.makedirs("logs", exist_ok=True)

import logging

logger = logging.getLogger("vendor_summary")
logger.setLevel(logging.DEBUG)

# Create file handler
fh = logging.FileHandler("logs/get_vendor_summary.log")
fh.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
fh.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(fh)

def create_vendor_summary(conn):
    '''This function will merge the differnet tables to get the overall vendor summary and adding new columns in the resultant data'''
    Vendor_sales_summary=pd.read_sql_query(""" WITH FreightSummary AS (
        SELECT 
            VendorNumber,
            SUM(Freight) AS FreightCost
            From vendor_invoice
            Group BY VendorNumber),
    
    PurchaseSummary AS (
        SELECT
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.Description,
            p.PurchasePrice,
            pp.Price as ActualPrice,
            pp.Volume,
            SUM(p.Quantity) AS TotalPurchaseQuantity,
            SUM(p.Dollars) AS TotalPurchaseDollars
    
        From purchases p
        Join purchase_prices pp
        ON p.Brand=pp.Brand
        Where p.PurchasePrice > 0
        Group BY p.VendorNumber, p.VendorName, p.Brand,p.Description,p.PurchasePrice, pp.Price, pp.Volume),
    
    SalesSummary AS (
        SELECT 
            VendorNo,
            Brand,
            SUM(SalesDollars) AS TotalSalesDollars,
            SUM(SalesQuantity) AS TotalSalesQuantity,
            SUM(SalesPrice) AS TotalSalesPrice,
            SUM(ExciseTax) AS TotalExciseTax
        From sales
        Group BY VendorNo, Brand
    )
    
    SELECT 
        ps.VendorNumber,
        ps.VendorName,
        ps.Description,
        ps.PurchasePrice,
        ps.ActualPrice,
        ps.Brand,
        ps.Volume,
        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,
        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,
        fs.FreightCost
    From PurchaseSummary ps
    LEFT JOIN SalesSummary ss
        ON ps.VendorNumber=ss.VendorNo
        AND ps.Brand=ss.Brand
    LEFT JOIN FreightSummary fs
        ON ps.VendorNumber = fs.VendorNumber
    ORDER BY ps.TotalPurchaseDollars DESC""",conn)

    return Vendor_sales_summary
def clean_data(df):
    #cleaning the data 
    df["Volume"]=df["Volume"].astype(float)
    df.fillna(0, inplace=True)
    df["VendorName"]=df["VendorName"].str.strip()
    df["Description"]=df["Description"].str.strip()
    # creating new features from the existing data
    df["GrossProfit"] = df["TotalSalesDollars"] - df["TotalPurchaseDollars"]
    df["ProfitMargin"] = (df["GrossProfit"] / df["TotalSalesDollars"]) * 100
    df["StockTurnover"] = df["TotalSalesQuantity"] / df["TotalPurchaseQuantity"]
    df["SalesToPurchaseRatio"] = df["TotalSalesDollars"] / df["TotalPurchaseDollars"]
    return df
    

if __name__=='__main__':
    #creating database connection
    conn=sqlite3.connect("inventory.db")
    logger.info('Creating Vendor Summary Table')
    summary_df=create_vendor_summary(conn)
    logger.info(summary_df.head())

    logger.info('Cleaning Data')
    clean_df=clean_data(summary_df)
    logger.info(clean_df.head())

    logger.info("Ingesting data........")
    ingest_db(clean_df, 'vendor_sales_summary',conn)
    logger.info("Completed")
    
    