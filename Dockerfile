FROM python:3.7
EXPOSE 5005
WORKDIR /app
ENV FLASK_APP application.py
CMD ["gunicorn", "--config", "/app/gunicorn-cfg.py", "application:application"]

COPY ./app /app
RUN pip install -r /app/requirements.txt
