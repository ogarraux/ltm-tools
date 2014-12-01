#!/usr/bin/python
import site
import sqlite3
import sys
from display_virtual import display_virtual

## Connect to SQLite DB
try:
    dbname = str(sys.argv[1])
except:
    print("Error: DB not specified")
    sys.exit(1)

try:
    dbh = sqlite3.connect(dbname)
except:
    print("Error: Unable to open database file")
    sys.exit(1)


cur = dbh.cursor()

matching_vips = set()

list_query = "SELECT virtual_id FROM virtual"

cur.execute(list_query)
virtuals = cur.fetchall()
if virtuals:
    virtuals_ids = [ x[0] for x in virtuals ]
    matching_vips.update(virtuals_ids)
else:
    print("No matching virtuals found")
    sys.exit(0)


for vip in matching_vips:
    if vip:
        display_virtual(vip, cur)



sys.exit(0)

