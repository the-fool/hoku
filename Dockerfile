FROM python3.6

RUN apt install build-essential 
RUN apt install python-dev 
RUN apt install libasound2
RUN apt install python-gi 
RUN apt install python-gi-cairo 
RUN apt install python3-gi 
RUN apt install python3-gi-cairo 
RUN apt install gir1.2-gtk-3.0
RUN apt install libcairo2-dev 
RUN apt install libgirepository1.0-dev

RUN pip install git+https://github.com/dpallot/simple-websocket-server.git
RUN pip install -r requirements.txt
