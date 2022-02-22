ARG SERVERLESS_VERSION
FROM aligent/serverless:${SERVERLESS_VERSION}

COPY pipe /
RUN apk add --no-cache wget
RUN wget -O /common.sh https://bitbucket.org/bitbucketpipelines/bitbucket-pipes-toolkit-bash/raw/0.6.0/common.sh

RUN chmod a+x /*.sh

ENTRYPOINT ["/pipe.sh"]
