FROM coppertopgeoff/rpi-python:3.7-101518

ENV INITSYSTEM on

WORKDIR /app

ADD ./requirements.txt ./requirements.txt

RUN apt install -y python3-smbus

RUN pip3 install -r requirements.txt

ADD ./example_config.yml ./config.yml

ADD ./*.py ./

# CMD modprobe i2c-dev && python3 ./app.py -c ./config.yml

ENTRYPOINT [ "python3" ]

CMD [ "./app.py", "-c", "config.yml" ]

