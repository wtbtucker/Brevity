###########################################################################################################
# FILENAME:		Brevity_3_0_1.py
# VERSION:		3.0.1
# UPDATE: 
#	3.0.1 -- January, 30 2024 --- Converting Brevity to function using Python 3
###########################################################################################################
import pandas as pd
import datetime
import os

# TODO:
# Add logic for sending stores a variety of colors
# custom entry is the shoe keyword
# Do I need to import extra information about the color or can I just use sku?	
# custom entry3 is gender


#>>>>>>>>>>>>>>>>>>>>>>>>>> GLOBAL FUNCTIONS & VARIABLES
pd.options.mode.chained_assignment = None  														#removes warning of filtering and replacing values
filepath = os.path.dirname(os.path.realpath(__file__)) + '\\'											#sets local file path
z = []																							#holds shoes to be pulled
def create_sku_df(): #creates a df that will allow the RICS custom entries to be applied to a df
	rics_skus_df = pd.read_csv(filepath + 'FW REPORTS\\SKU FILE\\SKUFile.csv', usecols = ['SKU', 'SupplierName', 'CustomEntry', 'CustomEntry3'],\
		encoding='utf_8_sig', converters = {'SKU': str})										#imports SKUs from RICS file into a df
	deleted_skus_df = pd.read_csv(filepath + 'FW REPORTS\\SKU FILE\\a SkuDelete.csv', usecols = ['SKU', 'SupplierName', 'CustomEntry', 'CustomEntry3'],\
		converters = {'SKU': str})																#imports SKUs that were deleted from RICS into a df
	sku_df = pd.concat([rics_skus_df, deleted_skus_df])											#joins the 2 df's into 1
	sku_df.columns = ['SKU','VENDOR','ITEM','SEX']												#renames the columns
	return sku_df

def create_store_df(): #creates a df of store #'s, store names, pull order and store abbreviations based on SD TO's the distrabution manager makes 
	store_df = pd.read_csv(filepath + 'Brevity Stuff\\STORES.csv', converters={'STORE':str})
	return store_df

#>>>>>>>>>>>>>>>>>>>>>>>>>> SALES
def pull_sales_main(): #creates a comprehensive sales df based on RICS sales data, RICS SKU data, and predetermined time frames
	sales_df = clean_sales ()																	#CALLS FUNCTION - filters sales by date & adds custom entries
	unique_df = sales_df.drop_duplicates(['ID'])												#filters all the IDs down to unique IDs
	# unique_df.to_csv(filepath + 'Testing2.csv',index=False)
	unique_df = sum(sales_df, 'LAST 8', unique_df)												#CALLS FUNCTION - finds the total sold over the last 8 weeks	
	unique_df = sum(sales_df, 'COMP 8', unique_df)												#CALLS FUNCTION - finds the total sold over the comp 8 weeks
	unique_df = sum(sales_df, 'FUT 2', unique_df)												#CALLS FUNCTION - finds the total sold over the fut 2 weeks
	unique_df = sum(sales_df, 'YEAR', unique_df)												#CALLS FUNCTION - finds the total sold over the last year
	temp_df = sales_df[sales_df['WEEK NUM'] <= 52]												#filters the sales_df to the last 52 weeks
	temp_df = temp_df.loc[:,['ID', 'WEEK NUM', 'UNITS']]											#drops all irrelevant columns
	temp_df['UNITS'] = temp_df['UNITS'] * -1													#converts neg units from RICS to positive
	temp_df2 = temp_df.groupby(['ID', 'WEEK NUM'])												#filters the df into sales by week	
	temp_df2 = temp_df2.sum()																	#finds the sum units sold in by week & by ID
	temp_df2 = temp_df2.reset_index()															#un-filters the df into a normal df setup 
	temp_df2.drop(temp_df2.columns[[1]], axis = 1, inplace=True)								#deletes the week column
	max_df = temp_df2.groupby(['ID'])															#filters by ID
	max_df = max_df.max()																		#finds the max units sold in a week
	max_df = max_df.reset_index()																#un-filters the df into a normal df setup
	max_df.columns = ['ID', 'MAX WK SALES']														#renames columns for laster df merger
	unique_df = pd.merge(unique_df, max_df, on = 'ID', how = 'outer')							#adds time frame sales onto unique IDs
	unique_df['MAX WK SALES'].fillna(0, inplace=True)											#fills missing mapped data with zero
	unique_df.drop(unique_df.columns[[2,4,5,6,7,8,9,10]], axis=1, inplace=True)					#drops irrelevant columns
	#unique_df.to_csv(filepath + 'Z-Sales2.csv', index=False)									#saves sales_df to a file
	return unique_df

def sum(sales_df,time,unique_df): #calculates the total units sold over a given time frame based on ID
	temp_df = sales_df[sales_df[time] == 1]														#sets the df to specified time frame
	temp_df = temp_df.loc[:,['ID', 'UNITS']]														#drops all irrelevant columns
	sum_df = temp_df.groupby(['ID'])															#filters the df into sales by ID
	sum_df = sum_df.sum()																		#finds the sum of the ID sold in that time frame
	sum_df = sum_df.reset_index()																#un-filters the df into a normal df setup
	sum_df.columns = ['ID', time + ' SALES']			 										#renames columns for df merger
	unique_df = pd.merge(unique_df, sum_df, on = 'ID', how = 'outer')							#adds time frame sales onto unique IDs
	unique_df[time + ' SALES'] = unique_df[time + ' SALES'].fillna(0)											#fills missing mapped data with zero
	unique_df[time + ' SALES'] = unique_df[time + ' SALES'] * -1								#converts units from negative to positive
	return unique_df		

def clean_sales(): #takes a RICS sales file and creates a useable df based on relevant dates and RICS custom entries
	sales_df = pd.read_csv(filepath + 'FW REPORTS\\INVENTORY DETAIL\\InventoryDetail.csv',usecols = ['Sku', 'InventoryStore', 'InventoryDate', \
		'GridColumn','Qty'], converters = {'Sku':str,'GridColumn':str, 'InventoryStore':str})	#imports the sales from RICS file into a sales_df
	sales_df.columns = ['SKU', 'STORE', 'DATE', 'SIZE', 'UNITS']								#rename the columns	sales_df                                		        						#creates a df of sales from a RICS file
	dates_df = pd.DataFrame(sales_df['DATE'])													#creates a df of all dates in the sales_db
	dates_df = dates_df.drop_duplicates(['DATE'])												#eliminates duplicates dates
	dates_df['DATES ISO'] = pd.to_datetime(dates_df['DATE'])									#converts column dates from a text format into a date format
	dates_df = dates_df.sort_values(['DATES ISO'], ascending=False)								#sorts dates new to old
	dates_df = dates_df.reset_index()															#resets the df's order so it stays new to old
	dates_df.drop(dates_df.columns[[0,2]], axis = 1, inplace=True)								#deletes the old index & python date format
	days_df = pd.read_csv(filepath + 'Brevity Stuff\\DATE_DB.csv')												#creates a df of relevant time tables (last 8, comp 8, ect)
	dates_df = pd.concat([dates_df, days_df], axis=1)											#maps the time tables with the correct dates
	dates_df = dates_df.dropna(subset = ['DAY NUM'])											#shrinks the df to only relevant dates	
	sales_df = pd.merge(sales_df, dates_df, on = 'DATE', how = 'outer')							#maps the time table df to the sales df
	sales_df = sales_df.dropna(subset = ['DAY NUM'])											#shrinks the df to only relevant dates
	sku_df = create_sku_df()																	#CALLS FUNCTION - creates a df of sku info from a RICS file
	sales_df = pd.merge(sales_df, sku_df, on = 'SKU', how = 'outer')							#maps the sku df to the sales df to create custom entries
	sales_df = sales_df.dropna(subset = ['UNITS'])												#shrinks the df to only custom entries that have sales data 	
	sales_df['PULL ID'] = (sales_df['SEX'].astype(str) + '-' + sales_df['ITEM'].astype(str) + '-' + \
		sales_df['SIZE'].astype(str))															#creates the pull id
	sales_df['ID'] = (sales_df['STORE'].astype(str) + '-' + sales_df['PULL ID'].astype(str))	#creates the id
	return sales_df

#>>>>>>>>>>>>>>>>>>>>>>>>>> INVENTORY 
def pull_inv_main(): #creates a comprehensive inv df based on RICS stock status file and RICS in-transit file
	inv_df = clean_inv()																		#CALLS FUNCTION - joins stock status & in-trans inv & adds custom entries
	temp_inv_df = inv_df.groupby(['ID', 'PULL ID', 'STORE'])									#filters the df by ID
	temp_inv_df = temp_inv_df.sum()																#creates inventory by ID (not by SKU)
	temp_inv_df = temp_inv_df.reset_index()														#un-filters the df into a normal df setup
	mask = ((temp_inv_df['STORE'] == '8')&(temp_inv_df['INV'] > 0))								#creates a filter of all ITEMS the wh has on-hand
	wh_df = temp_inv_df[mask]																	#applies the filter
	wh_df = wh_df.loc[:,['PULL ID', 'INV']]														#shrinks the df to only pull id & units for later merger by pull id
	wh_df.columns = ['PULL ID','WH']															#renames columns for later merger so wh has it's own column
	# wh_df.to_csv(filepath + 'Brevity Stuff\\z-WH_INV.csv', index=False)										#saves the wh_df to a file
	temp_inv_df = temp_inv_df.loc[:,['ID', 'PULL ID', 'INV']]									#shrinks the inv to only relevant columns
	#inv_df.to_csv(filepath + 'Z-Inv2.csv', index=False)										#saves inv_df to a file
	return temp_inv_df

def clean_inv(): #joins the RICS stock status file and RICS in-trans custom entries	
	ss_df = pd.read_csv(filepath + 'FW REPORTS\\STOCK STATUS\\StockStatus.csv', usecols=['StoreCode', 'SKU', 'COL', 'OnHand'], encoding='utf_8_sig',\
		converters={'StoreCode':str, 'SKU':str, 'COL':str})										#creates SS (stock status inventory) df
	rit_df = rit_create()																		#CALLS FUNCTION - creates in RIT (RICS in-transit inventory) df 
	ss_df.columns = ['STORE', 'SKU', 'SIZE', 'INV']												#renames the columns of the stock status df
	inv_df = pd.concat([ss_df, rit_df])															#appends the RIT to the SS 
	sku_df = create_sku_df()																	#CALLS FUNCTION - creates a df of sku info from a RICS file
	inv_df = pd.merge(inv_df, sku_df, on = 'SKU', how = 'outer')								#adds custom entries to the inventory df
	inv_df = inv_df.dropna(subset = ['INV'])													#shrinks the df to only SKU's that have on-hand inventory
	inv_df['PULL ID'] = (inv_df['SEX'].astype(str) + '-' + inv_df['ITEM'].astype(str) + '-' + \
		inv_df['SIZE'].astype(str))																#creates the pull id
	inv_df['ID'] = (inv_df['STORE'].astype(str) + '-' + inv_df['PULL ID'].astype(str))			#creates the id
	return inv_df
def rit_create(): #creates a df of in-transit product
	raw_rit_df = pd.read_csv(filepath + 'FW REPORTS\\STOCK STATUS\\in-transit.csv', usecols=['Sku', 'GridColumn', 'InventoryType', 'Qty', 'Comment'],\
		converters={'SKU':str, 'GridColumn':str, 'Qty':int})									#create raw RIT (RICS in transit) 
	raw_rit_df = raw_rit_df[raw_rit_df['Comment'].str.contains("SD")]							#filters RIT to only stock drops
	if(len(raw_rit_df.index))==0:
		rit_df = pd.DataFrame(columns = ['STORE','SKU','SIZE','INV'])
	else:
		temp_df = raw_rit_df[raw_rit_df['InventoryType'] == 'Transfer Out']							#sets the df to only RIT out bound transfers
		tran_out_df = temp_df.groupby(['InventoryType','Comment'])									#filters the df by TO# 
		tran_out_df = tran_out_df.sum()																#sums the out bound product by TO#
		tran_out_df = tran_out_df.reset_index()														#un-filters the df into a normal df setup	
		tran_out_df.drop(tran_out_df.columns[[0]], axis = 1, inplace=True)							#deletes old index
		rit_df = raw_rit_df.groupby(['Comment'])													#filters RIT by TO# (in AND out bound)
		rit_df = rit_df.sum()																		#sums the in AND out bound  product by TO#
		rit_df = rit_df.reset_index()																#un-filters the df into a normal df setup	
		rit_df = pd.merge(rit_df, tran_out_df, on = 'Comment', how = 'outer')						#creates a df by TO# which has trans out & (trans in - trans out )
		rit_df['ADD'] = rit_df['Qty_x'] - rit_df['Qty_y']											#creates a column which adds trans out to (trans in - trans out )
		rit_df = rit_df[rit_df['ADD'] == 0]															#filters the df down to only unreceived TO's
		rit_df = pd.merge(rit_df, raw_rit_df, on = 'Comment', how = 'inner')						#filters down the raw RIT df to only unreceived TO's
		store_df = create_store_df()																#CALLS FUNCTION - creates a df w/ store name AND #
		rit_df['SHORT'] = rit_df['Comment'].str[7:11]												#finds the store name from the TO#
		rit_df = pd.merge(rit_df, store_df, on = 'SHORT', how = 'inner')							#merges df's thus adding store # to the RIT df
		rit_df = rit_df.loc[:,['STORE', 'Sku', 'GridColumn', 'Qty']]									#drops all irrelevant columns
		rit_df.columns = ['STORE', 'SKU', 'SIZE', 'INV']											#renames the columns
		rit_df['INV'] = rit_df['INV'] * -1															#makes the negative inv positive
	return rit_df

#>>>>>>>>>>>>>>>>>>>>>>>>>> MODEL STOCK 
def create_item_db(): #creates df of only preselected stores & sizes
	itemdb_df = pd.read_csv(filepath + 'Brevity Stuff\\ItemDB.csv', converters = {'STORE': str})				#creates df based on item db
	size_df = pd.read_csv(filepath + 'Brevity Stuff\\Size_Run.csv', converters = {'SIZE': str})				#creates df based on size run db
	item_df = pd.merge(itemdb_df, size_df, on = 'SIZE RUN', how = 'outer')						#merges the df's thus applying size run to each item 
	item_df['PULL ID'] = (item_df['SEX'].astype(str) + '-' + item_df['ITEM'].astype(str)\
		+ '-' + item_df['SIZE'].astype(str))													#creates pull id
	item_df['ID'] = (item_df['STORE'].astype(str) + '-' + item_df['PULL ID'].astype(str))		#creates id
	return item_df

def model_stock(sale_df, inv_df):
	id_df = create_item_db()							 										#CALLS FUNCTION - creates df of only preselected stores & sizes
	sale_df = sales_df.loc[:,['ID','YEAR SALES','MAX WK SALES']]		 							#filters sales df to only relevant columns
	inv_df = inv_df.loc[:,['ID','INV']]															#filters inv df to only relevant columns
	store_df = create_store_df()																#CALLS FUNCTION - creates a df w/ store name, #, & pull order
	store_df = store_df.loc[:,['STORE', 'LONG','RANK']]											#filters store df to only relevant columns
	wh_df = pd.read_csv(filepath + 'Brevity Stuff\\z-WH_INV.csv')												#imports wh inventory
	mod_stock_df = pd.merge(id_df, sale_df, on = 'ID', how = 'left')							#combines all the df's
	mod_stock_df = pd.merge(mod_stock_df, inv_df, on = 'ID', how = 'left')						#combines all the df's
	mod_stock_df = pd.merge(mod_stock_df, store_df, on = 'STORE', how = 'left') 	   			#combines all the df's
	mod_stock_df = pd.merge(mod_stock_df, wh_df, on = 'PULL ID', how = 'left')					#combines all the df's
	mod_stock_df.update(mod_stock_df[['YEAR SALES','MAX WK SALES','INV','WH']].fillna(0))		#fills missing data with a zero
	mod_stock_df['TURN'] = mod_stock_df['YEAR SALES']/6											#sets turn rate to 5 in the stores
	mod_stock_df['MODEL'] = 1																	#
	mod_stock_df['MODEL'][(mod_stock_df['TURN'] > 1)] = mod_stock_df['TURN'].round(0).astype(int)
	mod_stock_df['MODEL'][(mod_stock_df['TURN'] > 1) & (mod_stock_df['MAX WK SALES'] < mod_stock_df['TURN'])] = mod_stock_df['MAX WK SALES'] + 1
	mod_stock_df['MODEL'][(mod_stock_df['TURN'] > 1) & (mod_stock_df['MAX WK SALES'] + 1 < mod_stock_df['TURN'])] = mod_stock_df['MAX WK SALES'] + 1
	mod_stock_df['PULL'] = 0																	#
	mod_stock_df['PULL'][(mod_stock_df['MODEL'] > mod_stock_df ['INV'])] = mod_stock_df['MODEL'] - mod_stock_df ['INV'] 
	# mod_stock_df.to_csv(filepath + 'Brevity Stuff\\z-MasterOpt.csv', index=False)								#
	pull_df = mod_stock_df[mod_stock_df['PULL'] > 0]											#
	pull_df = pull_df[pull_df['WH'] > 0]														#
	pull_df = pull_df.sort_values(['PULL ID','RANK'])											#sorts dates new to old
	pull_df = pull_df.reset_index()																#resets the df's order so it stays new to old
	pull_df = pull_df.loc[:,['PULL ID','RANK','LONG','INV','WH','PULL']]							#drops all irrelevant columns
	#pull_df.to_csv(filepath + 'Brevity Stuff\\Pull DF.csv',index=False)
	orderz_df = mod_stock_df.groupby(['VENDOR','SEX','ITEM','SIZE'])
	orderz_df = orderz_df.sum()																#creates inventory by ID (not by SKU)
	orderz_df = orderz_df.reset_index() #un-filters the df into a normal df setup
	orderz_df.drop(orderz_df.columns[[5,7,8,9,11]], axis = 1, inplace=True)
	orderz_df['ID'] = (orderz_df['SEX'].astype(str) + '-' + orderz_df['ITEM'].astype(str) + '-' + orderz_df['SIZE'].astype(str))
	print(orderz_df)
	orderz_df.columns = ['VENDOR','SEX','ITEM','SIZE','SALES','INV-S','MOD-S','ID']
	# orderz_df.to_csv(filepath + 'Brevity Stuff\\Orderz.csv', index=False)								
	return pull_df

#>>>>>>>>>>>>>>>>>>>>>>>>>> ALLOCATION
def allocate(pull_df):
	data = [] 																					#holds - item, store, inv, pull, pull2, wh, pull_total 
	i=0																							#counts the loop
	for row in pull_df.itertuples():															#goes row by row through the pull df
		if i == 0:																				#1st row
			data.append([row[1], row[3], row[4], row[6], 0, row[5], row[6]])					#loads the first row
			i += 1																				#adds to the count
		elif data[0][0] == row [1]: 															#checks if previous item is the same as 
			data.append([row[1], row[3], row[4], row[6], 0, 0, 0])
			data[0][6] += row[6]
			i += 1
		else:
			break_up(data,i)
			data = []
			data.append([row[1], row[3], row[4], row[6], 0, row[5], row[6]])
			i = 1
	break_up(data,i)
	almost = pd.DataFrame(z) 
	# almost.to_csv(filepath + 'Brevity Stuff\\z.csv', index=False)
	print ('The total for this pull is %d units' %int(almost[2].sum()))
	almost = almost.pivot_table(index = 0, columns = 1, values = 2)
	return almost
def break_up(data, i):
	if data[0][6] <= data[0][5]:																#is total amount to be pulled <= total in the wh
		for x in range(i):																		#if yes loop through all the items
			z.append([data[x][0],data[x][1],data[x][3]])										#update final pull to 
	else:
		for x in range(i): 	#fills zero in stock 1st
			if data[x][2] == 0 and data[0][5] > 0:
				data[x][4] = 1
				data[0][5] -= 1
				if data[0][5] == 0:
					for x in range(i):
						z.append([data[x][0],data[x][1],data[x][4]])
					return
		for x in range(i): #fills to half model_stock----------------------------------edit with data
			if int(float((data[x][2] + data[x][3])/2)) > (data[x][2] + data[x][4]):
				if (int(float((data[x][2] + data[x][3])/2)) - (data[x][2] + data[x][4])) < data[0][5]:
					data[0][5] = data[0][5] - (int(float((data[x][2] + data[x][3])/2)) - data[x][2] + data[x][4])
					data[x][4] = int(float((data[x][2] + data[x][3])/2)) - data[x][2] 
				else:
					data[x][4] = data[0][5]
					for x in range(i):
						z.append([data[x][0],data[x][1],data[x][4]])
					return
		for x in range(i): #fills to model_stock----------------------------------edit with data
			if (data[x][3] - data[x][4]) < data[0][5]:
				data[0][5] = data[0][5] - (data[x][3] - data[x][4])
				data[x][4] = data[x][3]
			else:
				data[x][4] = data[0][5] + data[x][4]
				break
		for x in range(i):
			z.append([data[x][0],data[x][1],data[x][4]])
	return
#>>>>>>>>>>>>>>>>>>>>>>>>>> MAIN
print('WORKING...')
sales_df = pull_sales_main()
inv_df = pull_inv_main()
pull_df = model_stock(sales_df, inv_df)
amost = allocate(pull_df)
tstamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
# amost.to_csv(filepath + 'Pulls ' + tstamp + '.csv')#, index=False)
print('Done')