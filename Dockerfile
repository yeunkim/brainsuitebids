FROM continuumio/anaconda3

RUN apt-get install -y wget git build-essential
RUN git clone --branch 0.13.0-rc1 https://github.com/nipy/nipype && \
    cd nipype && \
    pip install -r requirements.txt && \
    python setup.py develop

#Temp for install
RUN wget users.bmap.ucla.edu/~jwong/private/BrainSuite16a1.linux.tgz --user jwong --password notPublic && \
    tar -xf BrainSuite16a1.linux.tgz && cd BrainSuite16a1/bin && \
    wget users.bmap.ucla.edu/~jwong/private/volblend --user jwong --password notPublic && \
    wget users.bmap.ucla.edu/~jwong/private/dfsrender --user jwong --password notPublic
RUN chmod +x BrainSuite16a1/bin/volblend && chmod +x BrainSuite16a1/bin/dfsrender
#End temp


ENV PATH="/BrainSuite16a1/bin/:/BrainSuite16a1/svreg/bin/:/BrainSuite16a1/bdp/:${PATH}"
ADD . /qc-system

CMD ./qc-system/run.sh -d /data -p /public -w
