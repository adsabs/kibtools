import json

all_dashboards = {
    "_shards": {
        "failed": 0,
        "successful": 1,
        "total": 1
    },
    "hits": {
        "hits": [
            {
                "_id": "GETDash",
                "_index": ".kibana",
                "_score": 1.0,
                "_source": {
                    "description": "",
                    "hits": 0,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"filter\":[{\"query\":{\"query_string\":{\"query\":\"*\",\"analyze_wildcard\":true}}}]}"
                    },
                    "panelsJSON": "[{\"id\":\"GETViz\",\"type\":\"visualization\",\"size_x\":3,\"size_y\":2,\"col\":1,\"row\":1}]",
                    "title": "GETDash",
                    "version": 1
                },
                "_type": "dashboard"
            },
            {
                "_id": "GETDash2",
                "_index": ".kibana",
                "_score": 1.0,
                "_source": {
                    "description": "",
                    "hits": 0,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"filter\":[{\"query\":{\"query_string\":{\"query\":\"*\",\"analyze_wildcard\":true}}}]}"
                    },
                    "panelsJSON": "[{\"id\":\"GETViz\",\"type\":\"visualization\",\"size_x\":3,\"size_y\":2,\"col\":1,\"row\":1}]",
                    "title": "GETDash2",
                    "version": 1
                },
                "_type": "dashboard"
            }
        ],
        "max_score": 1.0,
        "total": 2
    },
    "timed_out": False,
    "took": 1
}

all_visualizations = {
    "_shards": {
        "failed": 0,
        "successful": 1,
        "total": 1
    },
    "hits": {
        "hits": [
            {
                "_id": "GETViz",
                "_index": ".kibana",
                "_score": 1.0,
                "_source": {
                    "description": "",
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"filter\":[]}"
                    },
                    "savedSearchId": "GET",
                    "title": "GETViz",
                    "version": 1,
                    "visState": "{\"aggs\":[{\"id\":\"1\",\"params\":{},\"schema\":\"metric\",\"type\":\"count\"},{\"id\":\"2\",\"params\":{\"extended_bounds\":{},\"field\":\"@timestamp\",\"interval\":\"auto\",\"min_doc_count\":1},\"schema\":\"segment\",\"type\":\"date_histogram\"}],\"listeners\":{},\"params\":{\"addLegend\":true,\"addTooltip\":true,\"defaultYExtents\":false,\"mode\":\"stacked\",\"shareYAxis\":true},\"type\":\"area\"}"
                },
                "_type": "visualization"
            }
        ],
        "max_score": 1.0,
        "total": 1
    },
    "timed_out": False,
    "took": 1
}

all_searches = {
    "_shards": {
        "failed": 0,
        "successful": 1,
        "total": 1
    },
    "hits": {
        "hits": [
            {
                "_id": "GET",
                "_index": ".kibana",
                "_score": 1.0,
                "_source": {
                    "columns": [
                        "_source"
                    ],
                    "description": "",
                    "hits": 0,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"index\":\"[logstash-]YYYY.MM.DD\",\"highlight\":{\"pre_tags\":[\"@kibana-highlighted-field@\"],\"post_tags\":[\"@/kibana-highlighted-field@\"],\"fields\":{\"*\":{}}},\"filter\":[],\"query\":{\"query_string\":{\"query\":\"GET\",\"analyze_wildcard\":true}}}"
                    },
                    "sort": [
                        "@timestamp",
                        "desc"
                    ],
                    "title": "GET",
                    "version": 1
                },
                "_type": "search"
            }
        ],
        "max_score": 1.0,
        "total": 1
    },
    "timed_out": False,
    "took": 1
}

stub_data = {
    '_search/dashboard': all_dashboards,
    '_search/visualization': all_visualizations,
    '_search/search': all_searches,
}
