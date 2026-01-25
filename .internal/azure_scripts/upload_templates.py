#!/usr/bin/env python3

import argparse
import boto3
from datetime import date
from functools import partial
from io import BytesIO
from multiprocessing import Pool
from sys import argv
import utils

ALL_TEMPLATES = ['all']
AMIS_FILE = 'amis.yaml'
URL_PLACEHOLDER = '__URL__'
VERSION = date.today().strftime('%Y%m%d')
s3_client = boto3.client('s3')
log = utils.log


def update_placeholders(content, bucket_url, lambda_url):
    for k, v in {URL_PLACEHOLDER: bucket_url, '__VERSION__': VERSION,  '__LAMBDA__': lambda_url}.items():
        content = content.replace(k, v)

    return content


def upload_template(bucket, bucket_url, lambda_url, template):
    template.content = update_placeholders(template.content, bucket_url, lambda_url)
    log(f'Uploading: {template.template_name}')
    extra_args = {
        'Tagging': 'Automation=Pre_Automation',
        'ACL': 'public-read'
    }
    if template.template_name == AMIS_FILE:
        extra_args['ContentType'] = 'text/plain'

    s3_client.upload_fileobj(BytesIO(template.content.encode('utf-8')), bucket,
                             f'{template.path.replace("/BUILD","")}/{template.template_name}',
                             ExtraArgs=extra_args)


def upload_templates(templates, bucket, lambda_bucket):
    log(f'Uploading templates to: {bucket}')
    bucket_url = utils.S3_URL.format(bucket)
    lambda_url = utils.S3_URL.format(lambda_bucket)
    upload_template_partial = partial(upload_template, bucket, bucket_url, lambda_url)
    with Pool(utils.POOL_SIZE) as pool:
        pool.map(upload_template_partial, templates)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bucket', dest='bucket',
                        default=utils.DEFAULT_BUCKET,
                        help='name of s3 bucket to upload to')
    parser.add_argument('-d', '--dependencies', dest='dependencies',
                        action='store_true',
                        help='Resolve and upload template dependencies')
    parser.add_argument('-t', '--templates', dest='templates', nargs='+',
                        required=True, help='paths for templates to upload')
    parser.add_argument('-l', '--lambda-bucket', dest='lambda_bucket',
                        default=utils.DEFAULT_LAMBDA,
                        help='name of lambdas s3 bucket')
    return parser.parse_args(argv[1:])


def main():
    args = parse_args()
    if ALL_TEMPLATES == args.templates:
        templates = utils.load_all_templates()

    upload_templates(templates, args.bucket, args.lambda_bucket)
    log('\n----- Done -----\n')


if __name__ == '__main__':
    main()
