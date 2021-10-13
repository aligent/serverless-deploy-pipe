#!/usr/bin/env bash

set -e

source "/common.sh"

DEBUG=${DEBUG:=false}
DEPLOYMENT_STAGE=${STAGE:=$BITBUCKET_BRANCH}

inject_aws_creds() {
     mkdir -p ~/.aws
     echo "[bitbucket-deployer]" >> ~/.aws/credentials 
     echo "aws_access_key_id=$AWS_ACCESS_KEY_ID"  >> ~/.aws/credentials 
     echo "aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"  >> ~/.aws/credentials 
}

install_dependencies() {
     if [ $DEBUG ]
     then
          debug "install_dependencies()"
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
     if [ $DEBUG ]
     then
          debug "deploy()"
          debug "Stage = $STAGE, DEPLOYMENT_STAGE = $DEPLOYMENT_STAGE"
          echo "/serverless/node_modules/serverless/bin/serverless.js deploy --stage $DEPLOYMENT_STAGE --aws-profile bitbucket-deployer --conceal --force"
     fi

     /serverless/node_modules/serverless/bin/serverless.js deploy --stage $DEPLOYMENT_STAGE --aws-profile bitbucket-deployer --conceal --force
}

inject_aws_creds
install_dependencies
deploy
