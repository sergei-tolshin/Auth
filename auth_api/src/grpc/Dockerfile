FROM python:3.9-slim-buster
RUN apt-get update -y && apt-get upgrade -y
WORKDIR /auth_api
COPY ../../requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY ../../src .
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh .
RUN chmod +x wait-for-it.sh

CMD [ "python", "./grpc/server.py" ]