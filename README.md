## Setup Aug 5 2022

```
cmsrel CMSSW_12_1_1
cd CMSSW_12_1_1/src
cmsenv
git cms-init
git remote add thomas-cmssw git@github.com:tklijnsma/cmssw.git
git fetch thomas-cmssw jansmerging:jansmerging
git cms-merge-topic tklijnsma:jansmerging

git clone git@github.com:tklijnsma/pu_attempt1.git
scramb
```