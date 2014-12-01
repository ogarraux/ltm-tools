#!/usr/bin/python
from __future__ import print_function,absolute_import
import bigsuds
import getpass
import sqlite3
import sys
import re
from datetime import datetime

## Make Python 2 work as Python 3
try:
    input = raw_input
except NameError:
    pass


## Settings
## Example: ltm_list = [ "10.1.1.1", "myf5.example.com", "myf5-2.eample.com"]
ltm_list = [ ] 

## Utility Functions
def build_db(cur):
    assert isinstance(cur, sqlite3.Cursor)
    cur.execute("DROP TABLE if exists ltm")
    cur.execute("""CREATE TABLE ltm  (
        ltm_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ltm_fqdn TEXT UNIQUE,
        ltm_version TEXT,
        ltm_last_probe TEXT
    );""")
    cur.execute("DROP TABLE if exists  partition")
    cur.execute("""CREATE TABLE partition (
        partition_id INTEGER PRIMARY KEY AUTOINCREMENT,
        partition_ltm INTEGER,
        partition_name TEXT,
        FOREIGN KEY(partition_ltm) REFERENCES ltm(ltm_id)
    );""")
    cur.execute("DROP TABLE if exists  pool")
    cur.execute("""CREATE TABLE pool (
        pool_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pool_name TEXT,
        pool_partition INTEGER,
        FOREIGN KEY(pool_partition) REFERENCES partition(partition_id)
    );""")
    cur.execute("DROP TABLE if exists  virtual")
    cur.execute("""CREATE TABLE virtual (
        virtual_id INTEGER PRIMARY KEY AUTOINCREMENT,
        virtual_partition INTEGER,
        virtual_destination_ip TEXT,
        virtual_destination_port INTEGER,
        virtual_pool INTEGER,
        virtual_name TEXT,
        FOREIGN KEY(virtual_partition) REFERENCES partition(partition_id),
        FOREIGN KEY(virtual_pool) REFERENCES pool(pool_id)
    );""")
    cur.execute("DROP TABLE if exists  node")
    cur.execute("""CREATE TABLE node (
        node_id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_name TEXT,
        node_ip TEXT,
        node_partition INTEGER,
        FOREIGN KEY(node_partition) REFERENCES partition(partition_id)
    );""")
    cur.execute("DROP TABLE if exists  rule")
    cur.execute("""CREATE TABLE rule (
        rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT,
        rule_partition INTEGER,
        FOREIGN KEY(rule_partition) REFERENCES partition(partition_id)
    );""")
    cur.execute("DROP TABLE if exists  pool_node")
    cur.execute("""CREATE TABLE pool_node (
        pool_node_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pool_id INTEGER,
        node_id INTEGER,
        pool_node_port INTEGER,
        FOREIGN KEY(pool_id) REFERENCES pool(pool_id),
        FOREIGN KEY(node_id) REFERENCES node(node_id)
    );""")
    cur.execute("DROP TABLE if exists  virtual_rule")
    cur.execute("""CREATE TABLE virtual_rule (
        virtual_rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
        virtual_id INTEGER,
        rule_id INTEGER,
        FOREIGN KEY(virtual_id) REFERENCES virtual(virtual_id),
        FOREIGN KEY(rule_id) REFERENCES rule(rule_id)
    );""")

def split_port(dest):
    return re.split("\:", dest)


## Connect to SQLite DB
try:
    dbname = str(sys.argv[1])
except:
    print("Error: DB not specified")
    sys.exit(0)

try:
    dbh = sqlite3.connect(dbname)
except:
    print("Error: Unable to open database file")
    sys.exit(0)

cur = dbh.cursor()



run_time = str(datetime.now())
ltm_user = input("Username: ")
ltm_password = getpass.getpass("Password: ")

build_db(cur)

for ltm in ltm_list:
    b = bigsuds.BIGIP(ltm, ltm_user, ltm_password)
    try:
        ver = b.System.SystemInfo.get_version()
    except:
        print("Error: unable to connect to " + ltm + ". Skipping")
        continue

    cur.execute("INSERT INTO ltm (ltm_fqdn,ltm_version,ltm_last_probe) VALUES (?, ?, ?)", [ltm, ver, run_time])
    ltm_id = cur.lastrowid

    if "v11" in ver:
        # V11 Logic
        b.System.Session.set_active_folder("/")
        parts = b.Management.Folder.get_list()
        for part in parts:
            cur.execute("INSERT INTO partition (partition_ltm, partition_name) VALUES (?, ?)", [ltm_id, part])
            part_id = cur.lastrowid
            b.System.Session.set_active_folder(part)

            ## Nodes
            nodes = b.LocalLB.NodeAddressV2.get_list()
            if nodes:
                nodes_ips = b.LocalLB.NodeAddressV2.get_address(nodes)
                num_nodes = len(nodes)
                part_list = [part_id] * num_nodes
                z_nodes_ips = zip(nodes, nodes_ips, part_list)
                cur.executemany("INSERT INTO node (node_name, node_ip, node_partition) values(?,?,?)", z_nodes_ips)

            ## Pools
            pools = b.LocalLB.Pool.get_list()
            if pools:
                num_pools = len(pools)
                part_list = [part_id] * num_pools
                z_pools = zip(pools, part_list)
                cur.executemany("INSERT INTO pool (pool_name, pool_partition) values(?,?)", z_pools)

                ## Pool Members
                pools_members = b.LocalLB.Pool.get_member_v2(pools)
                if pools_members:
                    for i, pool_members in enumerate(pools_members):
                        cur.execute("SELECT pool_id from pool \
                            INNER JOIN partition ON pool.pool_partition = partition.partition_id \
                            WHERE pool_name = ? AND partition_ltm = ?", [pools[i], ltm_id])
                        pool_id = cur.fetchone()[0]
                        for pool_member in pool_members:
                            cur.execute("SELECT node_id from node \
                                INNER JOIN partition ON node.node_partition = partition.partition_id \
                                WHERE node_name = ? AND partition_ltm = ?", [pool_member['address'], ltm_id ] )
                            node_id = cur.fetchone()[0]
                            cur.execute("INSERT INTO pool_node (pool_id, node_id, pool_node_port) VALUES (?, ?, ?)", [pool_id, node_id, pool_member['port']])
            ## Rules
            rules = b.LocalLB.Rule.get_list()
            if rules:
                num_rules = len(rules)
                part_list = [part_id] * num_rules
                z_rules = zip(rules, part_list)
                cur.executemany("INSERT INTO rule (rule_name, rule_partition) VALUES (?,?)", z_rules)


            ## VIP's
            vips = b.LocalLB.VirtualServer.get_list()
            if vips:
                vips_pools = b.LocalLB.VirtualServer.get_default_pool_name(vips)
                vips_pools_ids = []
                for vip_pool in vips_pools:
                    if vip_pool:
                        cur.execute("SELECT pool_id from pool \
                            INNER JOIN partition ON pool.pool_partition = partition.partition_id \
                            WHERE pool_name = ? AND partition_ltm = ?", [ vip_pool, ltm_id ] )
                        pool_id = cur.fetchone()[0]
                        vips_pools_ids.append(pool_id)
                    else:
                        vips_pools_ids.append("")

                vips_destinations = b.LocalLB.VirtualServer.get_destination(vips)
                vips_destinations_ips = [x['address'] for x in vips_destinations ]
                vips_destinations_ports = [x['port'] for x in vips_destinations ]
                num_vips = len(vips)
                part_list = [part_id] * num_vips

                z_vips = zip(vips, part_list, vips_destinations_ips, vips_destinations_ports, vips_pools_ids)
                cur.executemany("INSERT INTO virtual (virtual_name, virtual_partition, virtual_destination_ip, \
                    virtual_destination_port, virtual_pool) VALUES (?, ?, ?, ?, ?)", z_vips)

                ## VIP's Rules
                vips_rules = b.LocalLB.VirtualServer.get_rule(vips)
                if vips_rules:
                    for i, vip_rules in enumerate(vips_rules):
                        cur.execute("SELECT virtual_id from virtual \
                            INNER JOIN partition ON virtual.virtual_partition = partition.partition_id \
                            WHERE virtual_name = ? AND partition_ltm = ? ", [vips[i], ltm_id])
                        vip_id = cur.fetchone()[0]
                        for vip_rule in vip_rules:
                            cur.execute("SELECT rule_id from rule \
                                INNER JOIN partition ON rule.rule_partition = partition.partition_id \
                                WHERE rule_name = ? AND partition_ltm = ?", [vip_rule['rule_name'], ltm_id])
                            rule_id = cur.fetchone()[0]
                            cur.execute("INSERT INTO virtual_rule (virtual_id, rule_id) values (?,?)", [ vip_id, rule_id])
dbh.commit()
sys.exit(0)


