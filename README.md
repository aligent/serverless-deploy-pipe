# Aligent Serverless Deploy Pipe

This pipe is used to deploy Aligent [Serverless](https://www.serverless.com/) applications.

## YAML Definition

Add the following your `bitbucket-pipelines.yml` file:
> Please note: there is currently an issue when used with Bitbucket's node cache type. This cannot be used in the step until resolved.

```yaml
    - step:
        name: "deploy service"
        script:
          - pipe: docker://aligent/serverless-deploy-pipe:latest
            variables:
              AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
              AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}

```
## Variables

| Variable              | Usage                                                                                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| DEBUG                 | (Optional) Turn on extra debug information. Default: `false`.                                                                                             |
| AWS_ACCESS_KEY_ID     | Injects AWS Access key                                                                                                                                    |
| AWS_SECRET_ACCESS_KEY | Injects AWS Secret key                                                                                                                                    |
| CFN_ROLE              | (Optional) [CloudFormation service role](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html) to use for deployment |
| STAGE                 | (Optional) Define the stage to deploy. If not provided use branch name                                                                                    |
| YARN                  | (Optional) Use yarn to resolve dependencies                                                                                                               |
| UPLOAD_BADGE          | (Optional) Whether or not to upload a deployment badge to the repositories downloads section.                                                             |
| TIMEZONE              | (Optional) Which timezone the time in the badge should use (Default: 'Australia/Adelaide')                                                                |
| APP_USERNAME          | (Optional) The user to upload the badge as. Required if UPLOAD_BADGE is set to true.                                                                      |
| APP_PASSWORD          | (Optional) The app password of the user uploading the badge. Required if UPLOAD_BADGE is set to true.                                                     |
| ACTION                | (Optional) Custom serverless action. Defaults to deploy                                                                                                   |

See here: https://support.atlassian.com/bitbucket-cloud/docs/app-passwords/ for how to generate an app password.

## Development

Commits published to the `main` branch  will trigger an automated build.
