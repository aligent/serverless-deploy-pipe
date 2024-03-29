#!/usr/bin/env python3

from operator import sub
import os
from sre_constants import SUCCESS
import subprocess
from sys import stdout
from bitbucket_pipes_toolkit import Pipe, get_logger
import yaml
from pybadges import badge
from datetime import datetime
import pytz
import requests
from semver.version import Version
import shutil

logger = get_logger()
schema = {
    'AWS_ACCESS_KEY_ID': {'type': 'string', 'required': True},
    'AWS_SECRET_ACCESS_KEY': {'type': 'string', 'required': True},
    'CFN_ROLE': {'type': 'string', 'required': False},
    'STAGE': {'type': 'string', 'required': False},
    'YARN': {'type': 'boolean', 'required': False},
    'DEBUG': {'type': 'boolean', 'required': False, 'nullable': True},
    'TIMEZONE': {'type': 'string', 'required': False, 'default': 'Australia/Adelaide'},
    'UPLOAD_BADGE': {'type': 'boolean', 'required': False, 'default': False},
    'APP_USERNAME': {'type': 'string', 'required': False},
    'APP_PASSWORD': {'type': 'string', 'required': False},
    'CMD': {'type': 'string', 'required': False}
}

class ServerlessDeploy(Pipe):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Deployment Configuration
        self.access_key_id = self.get_variable('AWS_ACCESS_KEY_ID')
        self.secret_acces_key = self.get_variable('AWS_SECRET_ACCESS_KEY')
        self.cfn_role = self.get_variable('CFN_ROLE')
        self.stage = self.get_variable('STAGE')
        self.yarn = self.get_variable('YARN')
        self.timezone = self.get_variable('TIMEZONE')
        self.upload_badge = self.get_variable('UPLOAD_BADGE')
        self.app_username = self.get_variable('APP_USERNAME')
        self.app_password = self.get_variable('APP_PASSWORD')
        self.cmd = self.get_variable('CMD')

        # Bitbucket Configuration
        self.bitbucket_workspace = os.getenv('BITBUCKET_WORKSPACE')
        self.bitbucket_repo_slug = os.getenv('BITBUCKET_REPO_SLUG')
        self.bitbucket_pipeline_uuid = os.getenv('BITBUCKET_PIPELINE_UUID')
        self.bitbucket_step_uuid = os.getenv('BITBUCKET_STEP_UUID')
        self.bitbucket_commit = os.getenv('BITBUCKET_COMMIT')
        self.bitbucket_branch = os.getenv('BITBUCKET_BRANCH')

    def determine_npm_version(self):
        version = subprocess.run(args=["npm", "-v"], universal_newlines=True, capture_output=True)

        if version.returncode != 0:
            raise Exception("Cannot determine version of npm being used.")

        return Version.parse(version.stdout)

    def setup_ssh_credentials(self):
        ssh_dir = os.path.expanduser("~/.ssh/")
        injected_ssh_config_dir = "/opt/atlassian/pipelines/agent/ssh"
        identity_file = f"{injected_ssh_config_dir}/id_rsa_tmp"
        known_servers_file = f"{injected_ssh_config_dir}/known_hosts"
        os.mkdir(ssh_dir)

        if os.path.exists(identity_file):
            self.log_info('SSH identity file found, copying...')
            shutil.copy(identity_file, f"{ssh_dir}pipelines_id")

            self.log_info('Adding identity file config to config file')
            with open(f"{ssh_dir}config", 'a') as config_file:
                config_file.write("IdentityFile ~/.ssh/pipelines_id")
        else:
            self.log_info(message="No default SSH key configured in Pipelines.\n These are required to install internal node packages. \n These should be generated in bitbucket settings at Pipelines > SSH Keys.")

        if os.path.exists(known_servers_file):
            # Read contents of pipe-injected known hosts and pipe into 
            # runtime ssh config
            self.log_info('Piping known hosts into runtime ssh config')
            with open(known_servers_file) as pipe_known_host_file:
                with open(f"{ssh_dir}known_hosts", 'a') as known_host_file:
                    for line in pipe_known_host_file:
                        known_host_file.write(line)
        else: 
            self.log_info(message="No SSH known_hosts configured in Pipelines.")
       
        subprocess.run(["chmod", "-R", "go-rwx", ssh_dir], check=True)

    def inject_aws_creds(self):
        self.log_debug("Configuring AWS Deployment user.")

        configure = subprocess.run(
            args=[
                    "/serverless/node_modules/serverless/bin/serverless.js",
                    "config",
                    "credentials",
                    "--provider",
                    "aws",
                    "--profile",
                    "bitbucket-deployer",
                    "--key",
                    self.access_key_id,
                    "--secret",
                    self.secret_acces_key
                ],
            universal_newlines=True)

        if configure.returncode != 0:
            raise Exception("Failed to configure serverless credentials.")

    def inject_cfn_role(self):
        self.log_debug("Injecting CFN_ROLE")

        with open(f'{os.getcwd()}/serverless.yml', "r") as file:
            try:
                serverless = yaml.load(file, Loader=yaml.BaseLoader)

                # Ensure iam exists in the provider block
                if "iam" not in serverless["provider"]:
                    serverless["provider"]["iam"] = {}

                # if a role already exists DO NOT override it
                if "cfnRole" in serverless["provider"] or "deploymentRole" in serverless["provider"]["iam"]:
                    self.log_info("It looks like serverless.yaml already defines a CFN role.")

                    if self.cfn_role is None or not self.cfn_role:
                        self.log_info("This can now be injected by serverless-deploy-pipe and removed from serverless.yaml")
                    else: 
                        self.log_info(f'This will be overwritten with {self.cfn_role}. Please remove from serverless.yaml')

                # If we don't have a role to inject no point writing the file
                if self.cfn_role is None or not self.cfn_role:
                    return

            except yaml.YAMLError as exc:
                self.log_debug(exc)
                raise Exception("Failed to inject CFN_role")

        update = subprocess.run(
            args=[
                    "yq",
                    "-Y",
                    "-i",
                    f'del(.provider.cfnRole) | .provider.iam.deploymentRole="{self.cfn_role}"', 
                    "serverless.yml"
                ],
            universal_newlines=True)
        
        if update.returncode != 0:
            raise Exception("Failed to update the deployment role.")

    def install_dependencies(self):
        if self.yarn:
            self.log_debug("Installing dependencies with yarn.")

            install = subprocess.run(
                args=["yarn", "install", "--frozen-lockfile"],
                universal_newlines=True)

            if install.returncode != 0:
                raise Exception("Failed to install dependencies")
        else:
            self.log_debug("Installing dependencies with npm.")

            # Set node version 
            npm_version = self.determine_npm_version()

            # Only execute config set commands if using an npm version < 9.0.0
            if npm_version < Version.parse("9.0.0"):
                configure = subprocess.run(
                    args=["npm", "config", "set", "user", "0"],
                    universal_newlines=True)

                if configure.returncode != 0:
                    raise Exception("Failed to configure npm user id")

                configure = subprocess.run(
                    args=["npm", "config", "set", "unsafe-perm", "true"],
                    universal_newlines=True)

                if configure.returncode != 0:
                    raise Exception("Failed to configure npm permissions")

            install = subprocess.run(
                args=["npm", "ci"],
                universal_newlines=True)

            if install.returncode != 0:
                raise Exception("Failed to install dependencies")

    def upload_deployment_badge(self, wasSuccessful):
        if not self.upload_badge:
            self.log_debug("Skipping badge upload.")
            return

        if not self.app_password or not self.app_username:
            self.log_error("APP_USERNAME or APP_PASSWORD not set, we cannot upload without them.")
            self.fail(message="Failed to upload deployment badge.")
            return

        time = datetime.now(pytz.timezone(self.timezone))
        file_name = f'{self.bitbucket_branch}_status.svg'

        if wasSuccessful:
            deployment_badge = badge(left_text='deployment', right_text=time.strftime("%d %b, %Y, %H:%M"), right_color='green')
        else: 
            deployment_badge = badge(left_text='deployment', right_text=time.strftime("%d %b, %Y, %H:%M"), right_color='red')
        
        request = requests.post(f'https://api.bitbucket.org/2.0/repositories/{self.bitbucket_workspace}/{self.bitbucket_repo_slug}/downloads', files=[('files', (file_name, deployment_badge, 'image/svg+xml'))], auth=(self.app_username, self.app_password))

        if request.status_code != 201:
            self.log_error(f'Request to upload deployment badge failed with HTTP: {request.status_code}')
            self.fail(message="Failed to upload deployment badge.")
            return

        self.log_debug("Badge uploaded.")

    def run_serverless(self):
        cmd = self.cmd or 'deploy'
        self.log_debug(f'Running serverless cmd: {cmd}')
        stage = self.stage or self.bitbucket_branch
        self.log_debug(f'Running on stage: {stage}')
        command_args = [
          "/serverless/node_modules/serverless/bin/serverless.js",
          cmd,
          "--stage",
          stage,
          "--aws-profile",
          "bitbucket-deployer",
        ]

        if cmd == 'deploy':
          command_args.append("--conceal")
          command_args.append("--force")

        self.log_debug(f'Running with args: {command_args}')
        command = subprocess.run(args=command_args, universal_newlines=True)

        if command.returncode != 0:
                raise Exception(f'Failed run {cmd} for service.')

    def doctor(self):
        self.log_debug("Running serverless doctor")

        doctor = subprocess.run(
                args=[
                        "/serverless/node_modules/serverless/bin/serverless.js",
                        "doctor"
                    ],
                universal_newlines=True)

        if doctor.returncode != 0:
                raise Exception("Failed to run serverless doctor.")

    def run(self):
        super().run()
        try: 
            self.setup_ssh_credentials()
            self.install_dependencies()
            self.inject_aws_creds()
            self.inject_cfn_role()
            self.run_serverless()
            self.doctor()
        except:
            self.fail(message="Serverless deploy failed.")
            self.upload_deployment_badge(False)
            return

        self.upload_deployment_badge(True)
        self.success(message=f"Serverless Deploy Succeeded Passed")

if __name__ == '__main__':
    pipe = ServerlessDeploy(schema=schema, logger=logger)
    pipe.run()
