import sqlite3

def display_virtual(virtual_id, cur):
    virtual_query = """SELECT ltm_fqdn, virtual_name, virtual_destination_ip, virtual_destination_port, pool_name, pool_id
    from virtual
    INNER JOIN partition ON virtual_partition = partition.partition_id
    INNER JOIN ltm on partition_ltm = ltm_id
    LEFT JOIN pool ON virtual_pool = pool_id
    WHERE virtual_id = ?"""
    cur.execute(virtual_query, [ virtual_id ])
    virtual = cur.fetchone()
    ltm_fqdn, virtual_name, virtual_destination_ip, virtual_destination_port, pool_name, pool_id = virtual

    pool_query = """SELECT node.node_name, node.node_ip, pool_node.pool_node_port
        FROM pool
        INNER JOIN pool_node ON pool_node.pool_id = pool.pool_id
        INNER JOIN node ON pool_node.node_id = node.node_id
        WHERE pool.pool_id = ?"""
    cur.execute(pool_query, [ pool_id ])
    pool_members = cur.fetchall()

    if not pool_name:
        pool_name = "n/a"

    rule_query = """SELECT rule.rule_name
        FROM rule
        INNER JOIN virtual_rule ON rule.rule_id = virtual_rule.rule_id
        INNER JOIN virtual ON virtual_rule.virtual_id = virtual.virtual_id
        WHERE virtual.virtual_id = ?"""
    cur.execute(rule_query, [ virtual_id ])
    rules = cur.fetchall()

    print("LTM: " + ltm_fqdn)
    print("\tVIP Name: " + virtual_name)
    print("\t\tDestination: " + virtual_destination_ip + ":" + str(virtual_destination_port))
    print("\t\tPool: " + pool_name)
    for pool_member in pool_members:
        print("\t\t\t- Member: " + pool_member[0] + " : " + str(pool_member[2]))
        print("\t\t\t\tNode IP: " + pool_member[1] + ":" + str(pool_member[2]))
    if rules:
        print("\t\tRules:")
        for rule in rules:
            print("\t\t\t- Rule Name: " + rule[0])