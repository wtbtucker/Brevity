import pandas as pd
from datetime import datetime
import os
from sales_processor import SalesProcessor
from inventory_processor import InventoryProcessor

def create_sku_df(filepath): #creates a df that will allow the RICS custom entries to be applied to a df
	rics_skus_df = pd.read_csv(filepath + 'FW REPORTS\\SKU FILE\\SKUFile.csv', usecols = ['SKU', 'SupplierName', 'CustomEntry', 'CustomEntry3'],\
		encoding='utf_8_sig', converters = {'SKU': str})										#imports SKUs from RICS file into a df
	deleted_skus_df = pd.read_csv(filepath + 'FW REPORTS\\SKU FILE\\a SkuDelete.csv', usecols = ['SKU', 'SupplierName', 'CustomEntry', 'CustomEntry3'],\
		converters = {'SKU': str})																#imports SKUs that were deleted from RICS into a df
	sku_df = pd.concat([rics_skus_df, deleted_skus_df])											#joins the 2 df's into 1
	sku_df.columns = ['SKU','VENDOR','ITEM','SEX']												#renames the columns
	return sku_df

base_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '\\'
sku_df = create_sku_df(base_path)

sales_processor = SalesProcessor(base_path)
sales_df = sales_processor.pull_sales(sku_df)

inventory_processor = InventoryProcessor(base_path)
inventory_df = inventory_processor.pull_inventory(sku_df)