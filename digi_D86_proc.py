from __future__ import print_function
from pprint import pprint, pformat
from time import strftime
import os.path as osp

import common

import FWCore.ParameterSet.Config as cms


def digi(input_rootfiles, pu_rootfiles=None, n_events=1):
    digi_driver = common.CMSDriver('digi', '--no_exec')
    digi_driver.kwargs.update({
        '-s'              : 'DIGI:pdigi_valid,L1TrackTrigger,L1,DIGI2RAW,HLT:@fake2',
        '--conditions'    : 'auto:phase2_realistic_T21',
        '--datatier'      : 'GEN-SIM-DIGI-RAW',
        '--eventcontent'  : 'FEVTDEBUGHLT',
        '--geometry'      : 'Extended2026D86',
        '--era'           : 'Phase2C11I13M9',
        '--pileup'        : 'AVE_200_BX_25ns',
        '--pileup_input'  : 'das:/RelValMinBias_14TeV/1/GEN-SIM',
        })

    common.logger.info('input_rootfiles: %s', input_rootfiles)
    common.logger.info('pu_rootfiles: %s', pu_rootfiles)

    process = common.load_process_from_driver(digi_driver, 'digi_driver.py')
    common.rng(process, 1)
    process.source.fileNames = cms.untracked.vstring(input_rootfiles)
    process.maxEvents.input = cms.untracked.int32(n_events)
    process.source.firstLuminosityBlock = cms.untracked.uint32(1)
    process.mix.input.fileNames = cms.untracked.vstring(pu_rootfiles)
    process.mix.input.nbPileupEvents.averageNumber = cms.double(4.)

    output_file = 'file:{}_digi_D86_fine_n{}_{}.root'.format(common.guntype(input_rootfiles[0]), n_events, strftime('%b%d'))
    common.logger.info('Output: %s', output_file)
    process.FEVTDEBUGHLToutput.fileName = cms.untracked.string(output_file)

    # Not sure if needed - copied from the gensim step to make sure it all propagates
    process.FEVTDEBUGHLToutput.outputCommands.append("keep *_*G4*_*_*")
    process.FEVTDEBUGHLToutput.outputCommands.append("keep SimClustersedmAssociation_mix_*_*")
    process.FEVTDEBUGHLToutput.outputCommands.append("keep CaloParticlesedmAssociation_mix_*_*")

    return process


from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('analysis')
options.register('pu', '', VarParsing.multiplicity.list, VarParsing.varType.string, 'List of PU rootfiles')
options.register('n', 1, VarParsing.multiplicity.singleton, VarParsing.varType.int, 'Number of events')
options.parseArguments()
process = digi(options.inputFiles, options.pu, n_events=options.n)
common.logger.info('Created process %s', process)
