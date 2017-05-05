FROM continuumio/anaconda3

RUN apt-get install -y wget git build-essential

#Temp for install
RUN wget -q users.bmap.ucla.edu/~jwong/private/BrainSuite16a1.linux.tgz --user jwong --password notPublic && \
    tar -xf BrainSuite16a1.linux.tgz && cd BrainSuite16a1/bin && \
    wget -q users.bmap.ucla.edu/~jwong/private/volblend --user jwong --password notPublic && \
    wget -q users.bmap.ucla.edu/~jwong/private/dfsrender --user jwong --password notPublic
RUN chmod +x BrainSuite16a1/bin/volblend && chmod +x BrainSuite16a1/bin/dfsrender
RUN chmod -R ugo+r BrainSuite16a1

RUN cd BrainSuite16a1/bin && \
    wget -q users.bmap.ucla.edu/~jwong/private/tissueFrac --user jwong --password notPublic && \
    wget -q users.bmap.ucla.edu/~jwong/private/voxelCount --user jwong --password notPublic

RUN chmod +x BrainSuite16a1/bin/tissueFrac && chmod +x BrainSuite16a1/bin/voxelCount
#End temp

RUN git clone https://github.com/nipy/nipype && \
    cd nipype && \
    pip install -r requirements.txt && \
    python setup.py develop

ENV PATH="/BrainSuite16a1/bin/:/BrainSuite16a1/svreg/bin/:/BrainSuite16a1/bdp/:${PATH}"
ADD . /qc-system

CMD ./qc-system/run.sh -d /data -w
