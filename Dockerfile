FROM python3.6

RUN apt install build-essential python-dev libasound2
RUN pip install git+https://github.com/dpallot/simple-websocket-server.git
RUN pip install -r requirements.txt
