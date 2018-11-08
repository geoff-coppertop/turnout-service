FROM coppertopgeoff/rpi-python:3.7-101518

ENV INITSYSTEM on

WORKDIR /app

RUN apt install -y python3-smbus

ADD ./requirements.txt ./requirements.txt
ADD ./example_config.yml ./config.yml

RUN pip3 install -r requirements.txt

ADD ./*.py ./

CMD modprobe i2c-dev && python3 ./app.py -c ./config.yml

#ENTRYPOINT [ "python3" ]

#MD [ "./app.py", "-c", "config.yml" ]

