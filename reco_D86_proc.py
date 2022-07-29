from __future__ import print_function
from pprint import pprint, pformat
from time import strftime

import common

import FWCore.ParameterSet.Config as cms


def reco(input_rootfiles, pu_rootfiles=None, n_events=1):
    reco_driver = common.CMSDriver('reco', '--no_exec')
    reco_driver.kwargs.update({
        '-s'             : 'RAW2DIGI,L1Reco,RECO,RECOSIM,PAT,VALIDATION:@phase2Validation+@miniAODValidation,DQM:@phase2+@miniAODDQM',
        '--conditions'   : 'auto:phase2_realistic_T21',
        '--datatier'     : 'GEN-SIM-RECO,MINIAODSIM,DQMIO',
        '-n'             : '10',
        '--eventcontent' : 'FEVTDEBUGHLT,MINIAODSIM,DQM',
        '--geometry'     : 'Extended2026D86',
        '--era'          : 'Phase2C11I13M9',
        '--pileup'       : 'AVE_200_BX_25ns',
        '--pileup_input' : 'das:/RelValMinBias_14TeV/1/GEN-SIM',
        })
    common.logger.info('input_rootfiles: %s', input_rootfiles)
    common.logger.info('pu_rootfiles: %s', pu_rootfiles)

    process = common.load_process_from_driver(reco_driver, 'reco_driver.py')
    common.rng(process, 1)
    process.source.fileNames = cms.untracked.vstring(input_rootfiles)
    process.maxEvents.input = cms.untracked.int32(n_events)
    process.source.firstLuminosityBlock = cms.untracked.uint32(1)
    process.mix.input.fileNames = cms.untracked.vstring(pu_rootfiles)
    process.mix.input.nbPileupEvents.averageNumber = cms.double(4.)

    output_file = 'file:{}_reco_D86_fine_n{}_{}.root'.format(common.guntype(input_rootfiles[0]), n_events, strftime('%b%d'))
    common.logger.info('Output: %s', output_file)
    process.FEVTDEBUGHLToutput.fileName = cms.untracked.string(output_file)

    process.FEVTDEBUGHLToutput.outputCommands.append('keep PSimTrackCrossingFrame_*_*_*')
    process.FEVTDEBUGHLToutput.outputCommands.append('keep PSimVertexCrossingFrame_*_*_*')

    process.cfviewer = cms.EDAnalyzer("cfviewer")
    process.cfviewer_step = cms.Path(process.cfviewer)
    process.schedule.append(process.cfviewer_step)

    return process


from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('analysis')
options.register('pu', '', VarParsing.multiplicity.list, VarParsing.varType.string, 'List of PU rootfiles')
options.register('n', 1, VarParsing.multiplicity.singleton, VarParsing.varType.int, 'Number of events')
options.parseArguments()
process = reco(options.inputFiles, options.pu, n_events=options.n)
common.logger.info('Created process %s', process)
