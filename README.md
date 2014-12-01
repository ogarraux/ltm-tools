## Overview
This set of scripts connect to F5 devices using the SOAP iControl API to extract and store information about the virtual servers, pools, nodes, and iRules.
## Requirements
This requires Python 2.6. I don’t think the bigsuds library is compatible with Python 3.x.  It also requires SQLite 3. That works with Python out of the box on RHEL 6 based distros for me.

The F5 **bigsuds** library is available [here](https://devcentral.f5.com/d/bigsuds-python-icontrol-library).  After downloading and extracting that, you can run "python setup.py install" to install the module.

On the F5 side, this should work with 11.x F5’s.  Interacting with version 10 requires using different methods in bigsuds.  There’s no reason it couldn’t be modified to work with 10.x, but I don’t use 10.x devices enough myself for it to be worthwhile.
## Usage
	./load_ltm_data.py <db_filename>
	./search_by_node.py <db_filename> 	
	./search_by_vip.py <db_filename>
	./list_all.py <db_filename>
	
The ltm_list variable in *load_ltm_data.py* will need to be modified to include the FQDN's or IP addresses of the F5's you are wanting to scan.  For example:
	
	ltm_list = [ "10.1.1.1", "myf5.example.com", "myf5-2.eample.com"]
	
When the load_ltm_data.py script is ran, it prompts for credentials, and then connects to each of the F5’s specified in the ltm_list array. By default, the admin user account is able to connect via iControl.  The root account is not.

The *load_ltm_data* script rebuilds the database, and stores all of the partitions / virtuals / pools / etc that it finds. The *search_by** scripts search the specified database and display each of the VIP’s that match, along with the related pools / etc. *search_by_node.py* will display all of the VIP’s that the specified node is a part of. Here is an example output from one of the search scripts:

	LTM: 192.168.16.31
	        VIP Name: /Common/READINGLIST-DEV
	                Destination: 192.168.81.3:443
	                Pool: /Common/VOYAGER-INTERNAL
	                        - Member: /Common/VOYAGER-INTERNAL : 443
	                                Node IP: 192.168.17.17:443
	                Rules:
	                        - Rule Name: /Common/READINGLIST-DEV-IRULE
	                        - Rule Name: /Common/TEST2

You can search by either the full IP address, or a partial name (for instance "eading" would match the READINGLIST-DEV VIP in the output above).

*list_all.py* displays output similar to the output above, but for all objects in the database.