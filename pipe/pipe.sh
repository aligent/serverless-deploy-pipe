#!/usr/bin/env bash

set -e

source "$(dirname "$0")/common.sh"

inject_aws_creds() {
     mkdir -p ~/.aws
     echo "[bitbucket-deployer]" >> ~/.aws/credentials 
     echo "aws_access_key_id=$AWS_ACCESS_KEY_ID"  >> ~/.aws/credentials 
     echo "aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"  >> ~/.aws/credentials 
}

install_dependencies() {
     npm ci
}

deploy() {
     /serverless/node_modules/serverless/bin/serverless.js deploy --stage $stage --aws-profile bitbucket-deployer --conceal
}

inject_aws_creds
install_dependencies
deploy
