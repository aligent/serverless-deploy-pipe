ARG SERVERLESS_VERSION
FROM aligent/serverless:${SERVERLESS_VERSION}

COPY pipe /
RUN apk add --no-cache wget jq

ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools yq

RUN wget -O /common.sh https://bitbucket.org/bitbucketpipelines/bitbucket-pipes-toolkit-bash/raw/0.6.0/common.sh

RUN chmod a+x /*.sh

ENTRYPOINT ["/pipe.sh"]
