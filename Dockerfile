FROM python:3.8.12-bullseye
# If you are deploying this container yourself,
# include your own label. Example below.
#LABEL James Kunstle <jkunstle@redhat.com>
EXPOSE 8050

# OpenShift uses Podman.
# Doesn't automatically create a directory.
RUN mkdir ./explorer
WORKDIR /explorer
COPY ./requirements.txt /explorer
RUN pip3 install -r /explorer/requirements.txt
CMD python3 index.py
