import pandas as pd
import os

# Need color information included
# Just use SKUs?
class InventoryProcessor:
    def __init__(self, base_path):
        self.base_path = base_path

    def pull_inventory(self, sku_df):
        '''
        Create snapshot df of inventory at the stores, warehouse and in transit
        '''
        inv_df = self.clean_inventory(sku_df)																		
        temp_inv_df = inv_df.groupby(['ID', 'PULL ID', 'STORE', 'UPC'])									
        temp_inv_df = temp_inv_df.sum()																#creates inventory by ID (not by SKU)
        temp_inv_df = temp_inv_df.reset_index()														#un-filters the df into a normal df setup
        mask = ((temp_inv_df['STORE'] == '8')&(temp_inv_df['INV'] > 0))								#creates a filter of all ITEMS the wh has on-hand
        wh_df = temp_inv_df[mask]																	#applies the filter
        wh_df = wh_df.loc[:,['PULL ID', 'UPC', 'INV']]														#shrinks the df to only pull id & units for later merger by pull id
        wh_df.columns = ['PULL ID', 'UPC', 'WH']															#renames columns for later merger so wh has it's own column
        # wh_df.to_csv(filepath + 'Brevity Stuff\\z-WH_INV.csv', index=False)										#saves the wh_df to a file
        temp_inv_df = temp_inv_df.loc[:,['ID', 'PULL ID', 'UPC', 'INV']]									#shrinks the inv to only relevant columns
        #inv_df.to_csv(filepath + 'Z-Inv2.csv', index=False)										#saves inv_df to a file
        return temp_inv_df

    def clean_inventory(self, sku_df):
        ss_df = pd.read_csv(self.base_path + 'FW REPORTS\\STOCK STATUS\\StockStatus.csv', usecols=['StoreCode', 'SKU', 'COL', 'OnHand'], encoding='utf_8_sig',\
            converters={'StoreCode':str, 'SKU':str, 'COL':str})										#creates SS (stock status inventory) df
        rit_df = self.pull_in_transit()																		#CALLS FUNCTION - creates in RIT (RICS in-transit inventory) df 
        ss_df.columns = ['STORE', 'SKU', 'SIZE', 'INV']												#renames the columns of the stock status df
        inv_df = pd.concat([ss_df, rit_df])																#CALLS FUNCTION - creates a df of sku info from a RICS file
        inv_df = pd.merge(inv_df, sku_df, on = 'SKU', how = 'outer')								#adds custom entries to the inventory df
        inv_df = inv_df.dropna(subset = ['INV'])													#shrinks the df to only SKU's that have on-hand inventory
        inv_df['PULL ID'] = (inv_df['SEX'].astype(str) + '-' + inv_df['ITEM'].astype(str) + '-' + \
            inv_df['SIZE'].astype(str))																#creates the pull id
        inv_df['ID'] = (inv_df['STORE'].astype(str) + '-' + inv_df['PULL ID'].astype(str))	
        full_df = self.add_upc(inv_df)
        return full_df
    
    def add_upc(self, inv_df):
        upc_df = pd.read_csv(self.base_path + 'FW Reports\\UPC List\\UPCList.csv', usecols=['SKU', 'UPC', 'COL'], encoding='utf_8_sig', dtype=str)
        upc_df.drop_duplicates(subset=['UPC'], inplace=True)
        full_df = pd.merge(upc_df, inv_df, how='right', left_on=['SKU', 'COL'], right_on=['SKU', 'SIZE']) 
        return full_df

    def pull_in_transit(self):
        raw_rit_df = pd.read_csv(self.base_path + 'FW REPORTS\\STOCK STATUS\\in-transit.csv', usecols=['Sku', 'GridColumn', 'InventoryType', 'Qty', 'Comment'],\
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
            store_df = pd.read_csv(self.base_path + 'Brevity Stuff\\STORES.csv', converters={'STORE':str})																#CALLS FUNCTION - creates a df w/ store name AND #
            rit_df['SHORT'] = rit_df['Comment'].str[7:11]												#finds the store name from the TO#
            rit_df = pd.merge(rit_df, store_df, on = 'SHORT', how = 'inner')							#merges df's thus adding store # to the RIT df
            rit_df = rit_df.loc[:,['STORE', 'Sku', 'GridColumn', 'Qty']]									#drops all irrelevant columns
            rit_df.columns = ['STORE', 'SKU', 'SIZE', 'INV']											#renames the columns
            rit_df['INV'] = rit_df['INV'] * -1															#makes the negative inv positive
        return rit_df

