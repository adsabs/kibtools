[![Build Status](https://travis-ci.org/adsabs/kibtools.svg?branch=master)](https://travis-ci.org/adsabs/kibtools)
[![Coverage Status](https://coveralls.io/repos/adsabs/kibtools/badge.svg?branch=master&service=github)](https://coveralls.io/github/adsabs/kibtools?branch=master)
[![Code Climate](https://codeclimate.com/github/adsabs/kibtools/badges/gpa.svg)](https://codeclimate.com/github/adsabs/kibtools)
# Kib[ana]tools
A small tool to extract dashboards, visualizations, and searches from kibana,
that are stored in the elasticsearch index.

# Usage
To see how to use it, simple run the script:
```
python dashboard.py
```
The script will only work if you run it on a node that is running elasticsearch.


# Amazon S3
It is assumed you are using a VPC for the AWS, and as such, no keys are
being passed when communicating with AWS S3. Instead, you must create the
relevant IAM for the instance that you run this script on. For more details see
the extensive Amazon S3 documentation:

http://docs.aws.amazon.com/AmazonS3/latest/dev/using-iam-policies.html
