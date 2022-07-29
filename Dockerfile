FROM python:3.8.12-bullseye
# If you are deploying this container yourself,
# include your own label. Example below.
#LABEL James Kunstle <jkunstle@redhat.com>

# need this for the Dash app
EXPOSE 8050
EXPOSE 8888

# install pipenv
RUN pip install pipenv

# create a working directory
RUN mkdir explorer

# set that directory as working dir
WORKDIR /explorer

# copy the contents of current file into the
# working directory.
COPY ./ /explorer/

# install required modules at system level
RUN pipenv install --system --deploy

# run app
# CMD python3 app.py
# using production-level WSGI interface for server deployment
CMD gunicorn --bind :8050 app:server
