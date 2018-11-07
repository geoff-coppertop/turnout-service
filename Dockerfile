FROM coppertopgeoff/rpi-python:3.7-101518

WORKDIR /app

RUN apt install -y python3-smbus

ADD ./*.py ./
ADD ./requirements.txt ./requirements.txt
ADD ./example_config.yml ./config.yml

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3" ]

CMD [ "./app.py", "-c", "config.yml" ]

