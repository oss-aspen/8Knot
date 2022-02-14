FROM python:3.8.12-bullseye
# If you are deploying this container yourself,
# include your own label. Example below.
#LABEL James Kunstle <jkunstle@redhat.com>

# need this for the Dash app
EXPOSE 8050

# copy requirements from directory
# -- trying to cache this step for faster container builds.
COPY ./requirements.txt /

# install requirements
RUN pip3 install -r /requirements.txt

# create a working directory
RUN mkdir explorer

# set that directory as working dir
WORKDIR /explorer

# copy the contents of current file into the
# working directory.
COPY ./ /explorer/

# run app
CMD python3 index.py
