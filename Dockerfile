FROM ubuntu:16.04
RUN apt-get -y update --fix-missing && apt-get install -y \
    build-essential \
    git \
    libxt6 \
    unzip \
    wget

# Anaconda
RUN mkdir conda_install && cd conda_install && \
    wget -q https://repo.continuum.io/archive/Anaconda3-4.3.1-Linux-x86_64.sh && \
    bash Anaconda3-4.3.1-Linux-x86_64.sh -b -p /opt/conda && \
    cd / && \
    rm -rf conda_install && \
    echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh 
ENV PATH /opt/conda/bin:$PATH

# MATLAB MCR
RUN mkdir mcr_install && \
    cd mcr_install && \
    wget -q https://www.mathworks.com/supportfiles/downloads/R2015b/deployment_files/R2015b/installers/glnxa64/MCR_R2015b_glnxa64_installer.zip && \ 
    unzip -q MCR_R2015b_glnxa64_installer.zip && \
    ./install -agreeToLicense yes -mode silent && \
    cd / && \
    rm -rf mcr_install

# Nipype
RUN git clone https://github.com/nipy/nipype && \
    cd nipype && \
    pip install -r requirements.txt && \
    python setup.py develop

# BrainSuite
RUN wget -q users.bmap.ucla.edu/~jwong/private/BrainSuite16a1.linux.tgz --user jwong --password notPublic && \
    tar -xf BrainSuite16a1.linux.tgz && \
    cd BrainSuite16a1/bin && \
    wget -q users.bmap.ucla.edu/~jwong/private/volblend --user jwong --password notPublic && \
    wget -q users.bmap.ucla.edu/~jwong/private/dfsrender --user jwong --password notPublic && \
    chmod +x /BrainSuite16a1/bin/volblend && \
    chmod +x /BrainSuite16a1/bin/dfsrender && \
    chmod -R ugo+r /BrainSuite16a1 && \
    cd / && \
    rm BrainSuite16a1.linux.tgz 

# Stats Executables
RUN cd /BrainSuite16a1/bin && \
    wget -q users.bmap.ucla.edu/~jwong/private/tissueFrac --user jwong --password notPublic && \
    wget -q users.bmap.ucla.edu/~jwong/private/voxelCount --user jwong --password notPublic  && \
    chmod +x /BrainSuite16a1/bin/tissueFrac && \
    chmod +x /BrainSuite16a1/bin/voxelCount


ENV PATH=/BrainSuite16a1/bin/:/BrainSuite16a1/svreg/bin/:/BrainSuite16a1/bdp/:${PATH}

ADD . /qc-system

# Remove ^M at end of line from DOS systems.
RUN find ./qc-system -type f | xargs -I {} sed -i -e 's/\r$//' {}

# TODO remove options used in testing
CMD ./qc-system/run.sh -d /data -w -i 402
