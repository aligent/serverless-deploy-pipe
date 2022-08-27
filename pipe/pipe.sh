#!/usr/bin/env bash

set -e

source "/common.sh"

DEBUG=${DEBUG:=false}
DEPLOYMENT_STAGE=${STAGE:=$BITBUCKET_BRANCH}

/serverless/node_modules/serverless/bin/serverless.js --version

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

     if [ $YARN ]
     then
          yarn install --frozen-lockfile
     else
          npm config set user 0
          npm config set unsafe-perm true
          npm ci
     fi
}

inject_cfn_role() {
     EXISTING_LEGACY_CFN_ROLE=$(yq '.provider.cfnRole' serverless.yml)
     EXISTING_CFN_ROLE=$(yq '.provider.iam.deploymentRole' serverless.yml)
     if [[ ! $EXISTING_CFN_ROLE == "null" ]] || [[ ! $EXISTING_LEGACY_CFN_ROLE == "null" ]]; then
          echo "It looks like serverless.yaml already defines a CFN role."
          if [ $CFN_ROLE ];
          then
               echo "This will be overwritten with ${CFN_ROLE}. Please remove from serverless.yaml"
          else
               echo "This can now be injected by serverless-deploy-pipe and removed from serverless.yaml"
          fi
     fi

     if [ $CFN_ROLE ]
     then
          mv serverless.yml /tmp/serverless.yml && yq -Y -y 'del(.provider.cfnRole) | .provider.iam.deploymentRole=env.CFN_ROLE'  /tmp/serverless.yml > ./serverless.yml
     fi
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
inject_cfn_role
install_dependencies
deploy
