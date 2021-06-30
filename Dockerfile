FROM aligent/serverless

COPY pipe .
RUN apk add --no-cache wget
RUN wget -P . https://bitbucket.org/bitbucketpipelines/bitbucket-pipes-toolkit-bash/raw/0.4.0/common.sh

RUN chmod a+x *.sh

ENTRYPOINT ["./pipe.sh"]
