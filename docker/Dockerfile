FROM registry.access.redhat.com/ubi9/python-39:latest

WORKDIR /opt/app-root/src

# Install UV package installer
RUN pip3 install --no-cache-dir -U pip setuptools && \
    pip3 install --no-cache-dir uv

# install required packages with UV
COPY ./requirements.txt /opt/app-root/src/
RUN uv pip install --no-cache-dir -r requirements.txt

# copy the contents of current file into the
# working directory.
COPY ./8Knot/ /opt/app-root/src/

# Description of how to choose the number of workers and threads.
# common wisdom is (2*CPU)+1 workers:
# https://medium.com/building-the-system/gunicorn-3-means-of-concurrency-efbb547674b7
# this is a microservice - above may not apply
CMD [ "gunicorn", "--bind", ":8080", "app:server", "--workers", "1", "--threads", "2" ]
