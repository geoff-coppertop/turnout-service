FROM coppertopgeoff/rpi-python:3.7-101518

ENV INITSYSTEM on

WORKDIR /app

RUN apt install -y python3-smbus

COPY ./requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY ./example_config.yml ./config.yml

COPY ./*.py ./

ENTRYPOINT [ "python3" ]

CMD [ "./app.py", "-c", "config.yml" ]

