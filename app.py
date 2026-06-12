import pandas as pd
import os
from sales_processor import SalesProcessor
from inventory_processor import InventoryProcessor
from model_stock_generator import ModelStockGenerator
from inventory_processor import Inventory
from collections import defaultdict
import timeit
import yaml


def main():
	start = timeit.default_timer()
	config = yaml.safe_load(open("config.yml"))
	base_path = config["data-root"]
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

	# Load store rankings
	rank_dict, rank_to_name = load_mapping(base_path)

	# Pivot and align
	pivoted = models_df.pivot_table(index="PULL ID", columns="RANK", values="MODEL", fill_value=0)
	models = pivoted.apply(lambda row: row.tolist(), axis=1).to_dict()

	# Initialize empty data structure to eventually hold pull information
	store_count = len(rank_dict.keys())
	pulls = defaultdict(lambda: [0] * store_count)

	for product in models.keys():
		num_stores = len(models[product])
		# quantity available for distribution
		wh_quantity = inventory.get_total_quantity(product, 8)
		if wh_quantity <= 0:
			continue

		deficits = compute_deficits(models, product, rank_dict, inventory)
		total_deficits = sum(deficits)

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
	output_dir = config["output-dir"]
	pull_df.to_csv(f"{output_dir}warehouse_pulls.csv", index=False)

	stop = timeit.default_timer()
	print("Time: ", stop - start)

def compute_deficits(models, product, rank_dict, inventory) -> list[int]:
	# compute deficits per store in ranking order
	num_stores = len(models[product])
	deficits = []

	for rank in range(num_stores):
		# get model stock
		model_qty = models[product][rank]
		if model_qty <= 0:
			deficits.append(0)
			continue

		# get amount onhand
		store = rank_dict[rank+1]
		curr_quantity = inventory.get_total_quantity(product, store)

		# save the deficit for allocation in the next step
		store_deficit = max(0, model_qty - curr_quantity)
		deficits.append(store_deficit)
	return deficits

# creates a df of all SKUs including those deleted from RICS
def create_sku_df(filepath): 
	rics_skus_df = pd.read_csv(filepath + 'FW REPORTS\\SKU FILE\\SKUFile.csv', usecols = ['SKU', 'SupplierName', 'CustomEntry', 'CustomEntry3'],\
		encoding='utf_8_sig', converters = {'SKU': str})										#imports SKUs from RICS file into a df
	deleted_skus_df = pd.read_csv(filepath + 'FW REPORTS\\SKU FILE\\a SkuDelete.csv', usecols = ['SKU', 'SupplierName', 'CustomEntry', 'CustomEntry3'],\
		converters = {'SKU': str})																#imports SKUs that were deleted from RICS into a df
	sku_df = pd.concat([rics_skus_df, deleted_skus_df])											#joins the 2 df's into 1
	sku_df.columns = ['SKU','VENDOR','ITEM','SEX']												#renames the columns
	return sku_df

# get mapping of store rank to name
# have to hard code rankings for the moment because of error in STORES.csv
def load_mapping(base_path: str) -> tuple[dict, dict]:

	store_df = pd.read_csv(base_path + 'Brevity Stuff\\STORES.csv', converters={'STORE':int})
	store_df = store_df.loc[:, ['STORE', 'RANK', 'LONG']]
	rank_dict = dict(zip(store_df['RANK'], store_df['STORE']))
	rank_to_name = dict(zip(store_df['RANK'], store_df['LONG']))
	return rank_dict, rank_to_name

main()