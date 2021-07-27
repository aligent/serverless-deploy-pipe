# Aligent Serverless Deploy Pipe

This pipe is used to deploy Aligent [Serverless](https://www.serverless.com/) applications.

## YAML Definition

Add the following your `bitbucket-pipelines.yml` file:
> Please note: there is currently an issue when used with Bitbucket's node cache type. This cannot be used in the step until resolved.

```yaml
    - step:
        name: "deploy service"
        script:
          - pipe: docker://aligent/microservice-deploy-pipe:latest
            variables:
              AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
              AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}

```
## Variables

| Variable              | Usage                                                       |
| --------------------- | ----------------------------------------------------------- |
| DEBUG                 | (Optional) Turn on extra debug information. Default: `false`. |
| AWS_ACCESS_KEY_ID     | Injects AWS Access key |
| AWS_SECRET_ACCESS_KEY | Injects AWS Secret key |

## Development

Commits published to the `main` branch  will trigger an automated build.
