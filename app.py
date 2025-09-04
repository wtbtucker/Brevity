import pandas as pd
import os
from sales_processor import SalesProcessor
from inventory_processor import InventoryProcessor
from model_stock_generator import ModelStockGenerator
from inventory_processor import Inventory
from collections import defaultdict

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

# Use RICS inventory detail report to create manageable dataframe of sales
sales_processor = SalesProcessor(base_path)
sales_df = sales_processor.pull_sales(sku_df)

# Use those sales to set ideal inventory levels for each store (model stocks)
# based on max weekly sales and turn
model_stock_generator = ModelStockGenerator(base_path)
models_df = model_stock_generator.create_models(sales_df)

# Pivot and align
pivoted = models_df.pivot_table(index="PULL ID", columns="RANK", values="MODEL", fill_value=0)
models = pivoted.apply(lambda row: row.tolist(), axis=1).to_dict()

store_df = pd.read_csv(base_path + 'Brevity Stuff\\STORES.csv', converters={'STORE':int})
store_df = store_df.loc[:, ['STORE', 'RANK', 'LONG']]
code_to_name = dict(zip(store_df['STORE'], store_df['LONG']))
rank_dict = {
	1: 2,
	2: 1,
	3: 3,
	4: 28,
	5: 5,
	6: 17,
	7: 4,
	8: 20,
	9: 7,
	10: 14,
	11: 6,
	12: 21,
	13: 15,
	14: 19,
	15: 10,
	16: 11,
	17: 23,
	18: 18,
	19: 25,
	20: 13,
	21: 29,
	22: 12,
	23: 16,
	24: 27,
	25: 22,
	26: 24,
	27: 26,
	28: 9
}
rank_to_name = {rank: code_to_name[code] for rank, code in rank_dict.items()}

pulls = defaultdict(lambda: [0] * 26)

# Iterate through the products that can be distributed
for product in models.keys():

	# For each product get quantity available for distribution from warehouse
	wh_quantity = inventory.get_total_quantity(product, 8)
	for rank, model in enumerate(models[product]):
		if model == 0.0:
			continue
		store = rank_dict[rank+1]
		# get quantity at each store
		curr_quantity = inventory.get_total_quantity(product, store)
		curr_colors = inventory.get_colors(product, store)
		
		# need to allocate 
		if curr_quantity < model and wh_quantity > 0:
			wh_colors = inventory.get_colors(product, 8)

			# if possible pick color not available in store
			ideal_colors = wh_colors - curr_colors
			if ideal_colors:
				item_upc = ideal_colors.pop()
			else:
				item_upc = wh_colors.pop()
			inventory.decrement_quantity(item_upc, 8)
			inventory.increment_quantity(item_upc, store)
			wh_quantity -= 1
			pulls[item_upc][rank] += 1

print(len(pulls.keys()))
pull_df = pd.DataFrame.from_dict(pulls, orient="index")
pull_df.index.name = "UPC"
pull_df.reset_index(inplace=True)
pull_df.rename(columns={int(rank-1): store for rank, store in rank_to_name.items()}, inplace=True)

print(pull_df.head(5))
pull_df.to_csv("warehouse_pulls.csv", index=False)

# If current inventory level is less than model stock
# Allocate one item from warehouse to store
# prioritize colors not available at store
# need to determine data structure for pulls
# eventually want a matrix of upc: list of stores
# could just mimic the structure of models

# will probably want to iterate through the models for a particular id multiple times
# any reason not to store model logic in a similar data structure to inventory?
# I need to look up model stock by store and ID
# no need to decrement
# want a list of models for a particular ID
# array in the order of store rankings for each ID
# iterate through each model id then stores by ranking
# does every store get 1+ model stock for every item?
# fewer rows for portland than norwell
# seems to be creating models correctly
# for each model run through the rankings
  # get inventory level and colors for the store
  # old program allocates one to zero instock first
  # then half model stock
  # then full model stock
  # Determine quantity to transfer if warehouse had unlimited inventory

# Run through rankings to allocate based on WH inventory at product ID level
 # allocate half model stock to each store until out of WH inventory or all models filled
 # at this stage check what UPCs are available in store and UPCs in WH
