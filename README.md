# Aligent Magento Code Standards Pipe

This pipe is used to deploy standardised Aligent microsevers.

## YAML Definition

Add the following your `bitbucket-pipelines.yml` file:

```yaml
    - step:
        name: "deploy service"
        caches:
          - node
        script:
          - pipe: docker://aligent/microservice-deploy-pipe:latest
            variables:
              aws_access_key_id: ${aws_access_key_id}
              aws_secret_access_key: ${aws_secret_access_key}

```
## Variables

| Variable              | Usage                                                       |
| --------------------- | ----------------------------------------------------------- |
| DEBUG                 | (Optional) Turn on extra debug information. Default: `false`. |
| AWS_ACCESS_KEY_ID     | Injects AWS Access key |
| AWS_SECRET_ACCESS_KEY | Injects AWS Secret key |

## Development

Commits published to the `main` branch  will trigger an automated build.
