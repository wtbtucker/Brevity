# Brevity - Bill's Version
## Instructions
Ensure there are up-to-date versions of the following reports. Some are downloaded directly from RICS while others are maintained by the buying team

SKUFile.csv
File Path: C:\Users\order\Dropbox\PURCHASING\FW Reports\SKU FILE\SKUFile.csv
Requires: SKU, SupplierName, CustomEntry, CustomEntry3
Produces: SKU, VENDOR, ITEM, SEX

a SkuDelete.csv
File Path: C:\Users\order\Dropbox\PURCHASING\FW Reports\SKU FILE\a SkuDelete.csv
Requires: SKU, SupplierName, CustomEntry, CustomEntry3
Produces: SKU, VENDOR, ITEM, SEX
Used for: SKUs that were deleted from RICS

InventoryDetail.csv
File Path: C:\Users\order\Dropbox\PURCHASING\FW Reports\INVENTORY DETAIL\InventoryDetail.csv
Requires: Sku, InventoryStore, InventoryDate, GridColumn, Qty
Used for: sales history, YEAR SALES, MAX WK SALES

StockStatus.csv
File Path: C:\Users\order\Dropbox\PURCHASING\FW Reports\STOCK STATUS\StockStatus.csv
Requires: StoreCode, SKU, COL, OnHand
Used for: current on-hand inventory

in-transit.csv
File Path: C:\Users\order\Dropbox\PURCHASING\FW Reports\STOCK STATUS\in-transit.csv
Requires: Sku, GridColumn, InventoryType, Qty, Comment
Used for: unreceived stock-drop transfers

UPCList.csv
File Path: C:\Users\order\Dropbox\PURCHASING\FW Reports\UPC LIST\UPCList.csv
Requires: SKU, UPC, COL
Used for: mapping SKU/size to UPC

STORES.csv
File Path: C:\Users\order\Dropbox\PURCHASING\Brevity Stuff\STORES.csv
Requires: STORE, SHORT, LONG, RANK
Used for: store ranking and output column names

ItemDB.csv
File Path: C:\Users\order\Dropbox\PURCHASING\Brevity Stuff\ItemDB.csv
Requires: VENDOR, SEX, ITEM, STORE, SIZE RUN
Used for: valid product/store combinations

Size_Run.csv
File Path: C:\Users\order\Dropbox\PURCHASING\Brevity Stuff\Size_Run.csv
Requires: SIZE RUN, SIZE
Used for: expanding products into sizes