ARG SERVERLESS_VERSION
FROM aligent/serverless:${SERVERLESS_VERSION}

ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 git && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

COPY pipe requirements.txt pipe.yml /
RUN chmod a+x /pipe.py
RUN python3 -m pip install --no-cache-dir -r /requirements.txt

ENTRYPOINT ["/pipe.py"]
