import time
from pprint import pprint

from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.types import State, Provider
from libcloud.loadbalancer.providers import get_driver

from config import config

import libcloud.security
libcloud.security.CA_CERTS_PATH.append('/app/cacert.pem')

driver = get_driver(Provider.RACKSPACE_US)(config['rackspace_user'], config['rackspace_api_key'])

name = config['lb_name']
print 'Creating load balancer'
lbs = driver.list_balancers()
lb = [ lb for lb in lbs if lb.name == name ][0]
print lb
members = lb.list_members()
pprint(members)

new_member = Member(ip=None, port=None)
