FROM python:slim

RUN pip install requests schedule mysql-connector-python pytz

RUN mkdir /app

COPY src /app

CMD ["/app/main.py"]
ENTRYPOINT ["python"]
