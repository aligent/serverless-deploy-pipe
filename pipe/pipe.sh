#!/usr/bin/env bash

set -e

source "/common.sh"

DEBUG=${DEBUG:=false}

inject_aws_creds() {
     mkdir -p ~/.aws
     echo "[bitbucket-deployer]" >> ~/.aws/credentials 
     echo "aws_access_key_id=$AWS_ACCESS_KEY_ID"  >> ~/.aws/credentials 
     echo "aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"  >> ~/.aws/credentials 
}

install_dependencies() {
     if [ $DEBUG ]
     then
          debug "Current user:"
          id -u
          id -un
          debug "Current path permissions:"
          stat .
          debug "node_modules path permissions"
          stat ./node_modules || true
          debug "Listing dir"
          ls -alth ./
          debug "Listing node_modules dir"
          ls -alth ./node_modules || true
          
     fi
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
