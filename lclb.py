from pprint import pprint
import libcloud.security
libcloud.security.CA_CERTS_PATH.append('/app/cacert.pem')

from libcloud.loadbalancer.base import Member, Algorithm
from libcloud.loadbalancer.types import State, Provider
from libcloud.loadbalancer.providers import get_driver
import time
import json
import sys
import os
from urlparse import urlsplit
import requests

from config import config

driver = get_driver(Provider.RACKSPACE_US)(config['rackspace_user'], config['rackspace_api_key'])

ETCD_WATCH_VALUE=os.environ['ETCD_WATCH_VALUE']
ETCD_WATCH_KEY=os.environ['ETCD_WATCH_KEY']
ETCD_WATCH_MODIFIED_INDEX=os.environ['ETCD_WATCH_MODIFIED_INDEX']

def acquire_lock(ttl=5):
  r = requests.post('http://172.17.42.1:4001/mod/v2/lock/update_lb?ttl=%s' % ttl)
  if r.status_code != 200:
    print 'unable to get a good lock, exiting: %s %s' % (r.status_code, r.text)
    sys.exit(1)
  return int(r.text)

def release_lock():
  r = requests.delete('http://172.17.42.1:4001/mod/v2/lock/update_lb/%d' % (lock_id))
  if r.status_code != 200:
    print 'unable to delete lock, glad we have ttls? %s %s' % (r.status_code, r.text)
    sys.exit(1)
# get a lock
lock_id = acquire_lock()

etcd_state = set([])
print ETCD_WATCH_VALUE
if ETCD_WATCH_VALUE != '':
  data = json.loads(ETCD_WATCH_VALUE)
  for k in data:
    try:
      uri = data[k]['sockets'].pop()
    except IndexError:
      # no values
      continue
    host = urlsplit(uri)
    member = host.hostname, host.port
    etcd_state.add(member)

name = config['lb_name']
lbs = driver.list_balancers()
lb = [ lb for lb in lbs if lb.name == name ][0]
members = lb.list_members()
lb_state = set([])
member_lookup = {}
for m in members:
  member = m.ip, m.port
  lb_state.add(member)
  member_lookup[member] = m

def run_until_success(func, lb, member, max_retry=10):
  success = False
  attempt = 0
  while not success:
    try:
      func(lb, member)
    except Exception:
      print "sleeping...", Exception
      time.sleep(5)
      max_retry -= 1
      if max_retry <= 0:
         print 'hit max retrys, bailing...'
         raise Exception
      continue
    success = True

# members that need to be added
m_add = etcd_state - lb_state
for m in m_add:
  new_member = Member(id=None, ip=m[0], port=m[1])
  print "adding:", new_member
  run_until_success(driver.balancer_attach_member, lb, new_member)

# members that need to be deleted
m_delete = lb_state - etcd_state
for m in m_delete:
  member = member_lookup[m]
  print "removing:", member
  run_until_success(driver.balancer_detach_member, lb, member)

