FROM registry.access.redhat.com/ubi9/python-39

WORKDIR /8knot

# install required packages
COPY ./requirements.txt /8knot/
RUN pip3 install --no-cache-dir -r requirements.txt

# copy the contents of current file into the
# working directory.
COPY ./ /8knot/

# run flower
# CMD ["celery", "-A", "app:celery_app", "flower"]

# run app
# Description of how to choose the number of workers and threads.
# common wisdom is (2*CPU)+1 workers:
# https://medium.com/building-the-system/gunicorn-3-means-of-concurrency-efbb547674b7
# this is a microservice - above may not apply
# CMD [ "gunicorn", "--bind", ":8080", "app:server", "--workers", "1", "--threads", "2" ]

# run worker
CMD ["celery", "-A", "app:celery_app", "worker", "--loglevel=INFO"]