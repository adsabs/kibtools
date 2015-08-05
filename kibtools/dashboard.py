#!/usr/bin/env python

"""
Modified from https://github.com/jim-davis/kibana-helper-scripts
"""

import json
import requests

def get_objects(get_type, cluster):
    """

    :param get_type: the type to GET: search, visualization, dashboard
    :param cluster: cluster details

    :return: dictionary
    """

    url = 'http://{ip_address}:{port}/{index}/{type}/_search'.format(
        ip_address=cluster['ip_address'],
        port=cluster['port'],
        index=cluster['index'],
        type=get_type,
    )

    print url

    response = requests.get(url)

    return response.json().get('hits', {}).get('hits', {})
