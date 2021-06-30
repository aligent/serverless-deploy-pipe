#!/usr/bin/env bash

set -e

source "/common.sh"

inject_aws_creds() {
     mkdir -p ~/.aws
     echo "[bitbucket-deployer]" >> ~/.aws/credentials 
     echo "aws_access_key_id=$AWS_ACCESS_KEY_ID"  >> ~/.aws/credentials 
     echo "aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"  >> ~/.aws/credentials 
}

install_dependencies() {
     npm config set user 0
     npm config set unsafe-perm true
     npm ci
}

deploy() {
     [[ "$BITBUCKET_BRANCH" == "production" ]] && stage="production" || stage="staging"
     /serverless/node_modules/serverless/bin/serverless.js deploy --stage $stage --aws-profile bitbucket-deployer --conceal
}

inject_aws_creds
install_dependencies
deploy
