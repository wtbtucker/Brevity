import pandas as pd

class ModelStockGenerator:
    def __init__(self, base_path):
        self.base_path = base_path

    def create_models(self, sales_df):
        id_df = self.create_item_db()							 										#CALLS FUNCTION - creates df of only preselected stores & sizes
        sale_df = sales_df.loc[:,['ID','YEAR SALES','MAX WK SALES']]														#filters inv df to only relevant columns
        store_df = pd.read_csv(self.base_path + 'Brevity Stuff\\STORES.csv', converters={'STORE':str})																#CALLS FUNCTION - creates a df w/ store name, #, & pull order
        store_df = store_df.loc[:,['STORE', 'LONG','RANK']]										#imports wh inventory
        mod_stock_df = pd.merge(id_df, sale_df, on = 'ID', how = 'left')					#combines all the df's
        mod_stock_df = pd.merge(mod_stock_df, store_df, on = 'STORE', how = 'left') 				#combines all the df's
        mod_stock_df.update(mod_stock_df[['YEAR SALES','MAX WK SALES']].fillna(0))		#fills missing data with a zero
        mod_stock_df['TURN'] = mod_stock_df['YEAR SALES']/6											#sets turn rate to 5 in the stores
        mod_stock_df['MODEL'] = 1																	#
        mod_stock_df['MODEL'][(mod_stock_df['TURN'] > 1)] = mod_stock_df['TURN'].round(0).astype(int)
        mod_stock_df['MODEL'][(mod_stock_df['TURN'] > 1) & (mod_stock_df['MAX WK SALES'] < mod_stock_df['TURN'])] = mod_stock_df['MAX WK SALES'] + 1
        mod_stock_df['MODEL'][(mod_stock_df['TURN'] > 1) & (mod_stock_df['MAX WK SALES'] + 1 < mod_stock_df['TURN'])] = mod_stock_df['MAX WK SALES'] + 1
        # mod_stock_df.to_csv(filepath + 'Brevity Stuff\\z-MasterOpt.csv', index=False)								#							
        return mod_stock_df        
    
    def create_item_db(self):
        itemdb_df = pd.read_csv(self.base_path + 'Brevity Stuff\\ItemDB.csv', converters = {'STORE': str})				#creates df based on item db
        size_df = pd.read_csv(self.base_path + 'Brevity Stuff\\Size_Run.csv', converters = {'SIZE': str})				#creates df based on size run db
        item_df = pd.merge(itemdb_df, size_df, on = 'SIZE RUN', how = 'outer')						#merges the df's thus applying size run to each item 
        item_df['PULL ID'] = (item_df['SEX'].astype(str) + '-' + item_df['ITEM'].astype(str)\
            + '-' + item_df['SIZE'].astype(str))													#creates pull id
        item_df['ID'] = (item_df['STORE'].astype(str) + '-' + item_df['PULL ID'].astype(str))		#creates id
        return item_df        