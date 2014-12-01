#!/usr/bin/python
from __future__ import print_function,absolute_import
import sqlite3
import sys
from display_virtual import display_virtual

## Make Python 2 work as Python 3
try:
    input = raw_input
except NameError:
    pass

## Connect to SQLite DB
try:
    dbname = str(sys.argv[1])
except:
    print("Error: DB not specified")
    sys.exit(1)

try:
    virtual_value = str(sys.argv[2])
except:
    print("Error: Virtual search value not specified")
    sys.exit(1)
try:
    dbh = sqlite3.connect(dbname)
except:
    print("Error: Unable to open database file")
    sys.exit(1)


cur = dbh.cursor()

matching_vips = set()

virtual_search_query = "SELECT virtual_id FROM virtual WHERE virtual_name LIKE ? or virtual_destination_ip = ?"

cur.execute(virtual_search_query, [ "%" + virtual_value + "%", virtual_value])
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


