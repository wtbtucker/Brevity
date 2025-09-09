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


for product in models.keys():

	wh_quantity = inventory.get_total_quantity(product, 8)
	if wh_quantity <= 0:
		continue

	# compute deficits per store in ranking order
	num_stores = len(models[product])
	deficits = []
	total_deficits = 0

	for rank in range(num_stores):
		model_qty = models[product][rank]
		if model_qty <= 0:
			deficits.append(0)
			continue
		store = rank_dict[rank+1]
		curr_quantity = inventory.get_total_quantity(product, store)
		store_deficit = max(0, model_qty - curr_quantity)
		total_deficits += store_deficit
		deficits.append(store_deficit)

	if total_deficits <= 0:
		continue

	to_allocate = min(total_deficits, wh_quantity)
	rank = 0
	while to_allocate > 0:
		store_deficit = deficits[rank]
		store = rank_dict[rank+1]
		curr_colors = inventory.get_colors(product, store)
		
		# need to allocate 
		if store_deficit > 0:
			wh_colors = inventory.get_colors(product, 8)

			# if possible pick color not available in store
			ideal_colors = wh_colors - curr_colors
			if ideal_colors:
				item_upc = ideal_colors.pop()
			else:
				item_upc = wh_colors.pop()
			inventory.decrement_quantity(item_upc, 8)
			inventory.increment_quantity(item_upc, store)
			to_allocate -= 1
			pulls[item_upc][rank] += 1
		rank = (rank + 1) % num_stores


print(len(pulls.keys()))
pull_df = pd.DataFrame.from_dict(pulls, orient="index")
pull_df.index.name = "UPC"
pull_df.reset_index(inplace=True)
pull_df.rename(columns={int(rank-1): store for rank, store in rank_to_name.items()}, inplace=True)

print(pull_df.head(5))
pull_df.to_csv("warehouse_pulls.csv", index=False)
