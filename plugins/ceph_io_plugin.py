#!/usr/bin/env python
#
# vim: tabstop=4 shiftwidth=4

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# Authors:
#   Ricardo Rocha <ricardo@catalyst.net.nz>
#
# About this plugin:
#   This plugin collects information regarding Ceph pools.
#
# collectd:
#   http://collectd.org
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml
# ceph pools:
#   http://ceph.com/docs/master/rados/operations/pools/
#

import collectd
import json
import traceback
import subprocess

import base

class CephIOPlugin(base.Base):

    def __init__(self):
        base.Base.__init__(self)
        self.prefix = 'ceph'

    def get_stats(self):
        """Retrieves stats from ceph pools"""

        ceph_cluster = "%s-%s" % (self.prefix, self.cluster)

        data = { ceph_cluster: {} }

        stats_output = None
        try:
            stats_output = subprocess.check_output('ceph osd pool stats -f json', shell=True)
        except Exception as exc:
            collectd.error("ceph-io: failed to ceph pool stats :: %s :: %s"
                    % (exc, traceback.format_exc()))
            return

        if stats_output is None:
            collectd.error('ceph-io: failed to ceph osd pool stats :: output was None')

        json_stats_data = json.loads(stats_output)

        # push osd pool stats results
        for pool in json_stats_data:
            pool_key = "pool-%s" % pool['pool_name']
            data[ceph_cluster][pool_key] = {}
            pool_data = data[ceph_cluster][pool_key] 
            for stat in ('read_bytes_sec', 'write_bytes_sec', 'op_per_sec'):
                pool_data[stat] = pool['client_io_rate'][stat] if pool['client_io_rate'].has_key(stat) else 0

        return data

try:
    plugin = CephIOPlugin()
except Exception as exc:
    collectd.error("ceph-io: failed to initialize ceph pool plugin :: %s :: %s"
            % (exc, traceback.format_exc()))

def read_callback():
    """Callback triggerred by collectd on read"""
    plugin.read_callback()

def configure_callback(conf):
    """Received configuration information"""
    plugin.config_callback(conf)
    collectd.register_read(read_callback, plugin.interval)

collectd.register_config(configure_callback)