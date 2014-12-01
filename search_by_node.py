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
    node_value = str(sys.argv[2])
except:
    print("Error: Node search value not specified")
    sys.exit(1)
try:
    dbh = sqlite3.connect(dbname)
except:
    print("Error: Unable to open database file")
    sys.exit(1)


cur = dbh.cursor()

matching_vips = set()

node_search_query = "SELECT node_id FROM node WHERE node_name LIKE ? OR node_ip = ?"

cur.execute(node_search_query, [ "%" + node_value + "%", node_value])
nodes = cur.fetchall()
if nodes:
    for n in nodes:
        cur.execute("SELECT pool_id FROM pool_node WHERE node_id = ?", [n[0]])
        pools = cur.fetchall()
        pools_ids = [ x[0] for x in pools ]
        if pools:
            for p in pools:
                cur.execute("SELECT virtual_id FROM virtual WHERE virtual_pool = ?", [p[0]])
                vips = cur.fetchall()
                vips_ids = [ x[0] for x in vips ]
                matching_vips.update(vips_ids)
else:
    print("No matching nodes found")
    sys.exit(0)


for vip in matching_vips:
    if vip:
        display_virtual(vip, cur)



sys.exit(0)


