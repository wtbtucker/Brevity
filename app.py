import pandas as pd
import os
from sales_processor import SalesProcessor
from inventory_processor import InventoryProcessor
from model_stock_generator import ModelStockGenerator
from inventory_processor import Inventory

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

# Load current inventory levels using stock status and in-transit reports
inventory_processor = InventoryProcessor(base_path)
inventory_processor.load_inventory()
inventory_processor.add_keyword(sku_df)
inventory_processor.add_upc()
inventory = inventory_processor.clean_inventory()

colors = inventory.get_colors("M-GT-2000-11", 1)
print(colors)
print(inventory.get_total_quantity("M-GT-2000-11", 1))

# test inventory functions
inventory.decrement_quantity('197298379045', 1)
print(inventory.get_total_quantity("M-GT-2000-11", 1))

inventory.decrement_quantity('197298379045', 1)
print(inventory.get_total_quantity("M-GT-2000-11", 1))
colors = inventory.get_colors("M-GT-2000-11", 1)
print(colors)

# Use RICS inventory detail report to create manageable dataframe of sales
sales_processor = SalesProcessor(base_path)
sales_df = sales_processor.pull_sales(sku_df)
print(sales_df.head(5))

# Use those sales to set ideal inventory levels for each store (model stocks)
model_stock_generator = ModelStockGenerator(base_path)
models_df = model_stock_generator.create_models(sales_df)
print(models_df.columns)

# ALLOCATE
# compare model stocks with current inventory levels at the product ID level
  # Determine quantity to transfer if warehouse had unlimited inventory
# Run through rankings to allocate based on WH inventory at product ID level
 # allocate half model stock to each store until out of WH inventory or all models filled
 # at this stage check what UPCs are available in store and UPCs in WH
