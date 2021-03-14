# Stages:
#   root       : Common image, both for the builder and for the final image.
#                This contains only minimal dependencies required in both cases
#                for miniconda and the Makefile.
#   env_builder: stage in which the conda envrionment is created
#                and dependencies are installed
#   base       : the final image containing only the required environment files,
#                and none of the infrastructure required to generate them.

# root
FROM debian:buster-slim as base

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV LANGUAGE en_US.UTF-8

ENV SHELL /bin/bash

RUN apt-get --yes install
# required for weasyprint: cairo, pango etc
RUN apt-get update && \
    apt-get install --yes bash make sed grep gawk curl git bzip2 unzip \
    ca-certificates \
    gcc build-essential shared-mime-info libffi-dev \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0


ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH

# The latest version of conda can be newer than the latest
# version for which an installer is available. Further
# down we invoke "conda update --all" to update to the lates
# version. This Marker is incremented when we know such an
# update was published and want to update the image.
ENV MINICONDA_VERSION_MARKER 4.8.2
ENV MINICONDA Miniconda3-latest-Linux-x86_64.sh
ENV MINICONDA_URL https://repo.continuum.io/miniconda/$MINICONDA

RUN curl -L "$MINICONDA_URL" --silent -o miniconda3.sh && \
    /bin/bash miniconda3.sh -f -b -p $CONDA_DIR && \
    rm miniconda3.sh && \
    /opt/conda/bin/conda clean -tipy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc && \
    conda update --all --yes && \
    conda config --set auto_update_conda False


FROM base as builder

ADD requirements/ requirements/
ADD scripts/ scripts/

ADD Makefile.bootstrapit.make Makefile.bootstrapit.make
ADD Makefile Makefile

# install envs (relatively stable)
ADD requirements/conda.txt requirements/conda.txt
RUN make build/envs.txt

# install python package dependencies (change more often)
ADD requirements/ requirements/
RUN make conda

# Deleting pkgs implies that `conda install`
# will have to pull all packages again.
RUN conda clean --all --yes
# Conda docs say that it is not safe to delete pkgs
# because there may be symbolic links, so we verify
# first that there are no such links.
RUN find -L /opt/conda/envs/ -type l | grep "/opt/conda/pkgs" || exit 0

# The conda install is not usable after this RUN command. Since
# we only need /opt/conda/envs/ anyway, this shouldn't be an issue.
RUN conda clean --all --yes && \
    ls -d /opt/conda/* | grep -v envs | xargs rm -rf && \
    find /opt/conda/ -name "*.exe" | xargs rm -rf && \
    find /opt/conda/ -name "__pycache__" | xargs rm -rf && \
    rm -rf /opt/conda/pkgs/


FROM base

COPY --from=builder /opt/conda/ /opt/conda/
COPY --from=builder /vendor/ /vendor

CMD [ "/bin/bash" ]
