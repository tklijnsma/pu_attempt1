from __future__ import print_function
from pprint import pprint, pformat
from time import strftime

import common

import FWCore.ParameterSet.Config as cms


def gensim(thing, n_events):
    gensim_driver = common.CMSDriver('TTbar_14TeV_TuneCP5_cfi', '--no_exec')
    gensim_driver.kwargs.update({
        '-s'             : 'GEN,SIM',
        '--conditions'   : 'auto:phase2_realistic_T21',
        '--beamspot'     : 'HLLHC14TeV',
        '--datatier'     : 'GEN-SIM',
        '--eventcontent' : 'FEVTDEBUG',
        '--geometry'     : 'Extended2026D86',
        '--era'          : 'Phase2C11I13M9',
        '--procModifier' : 'fineCalo',
        })
    process = common.load_process_from_driver(gensim_driver, 'gensim_driver.py')
    common.rng(process, 1)
    common.activate_finecalo(process)
    process.maxEvents.input = cms.untracked.int32(n_events)
    process.source.firstLuminosityBlock = cms.untracked.uint32(1)

    output_file = 'file:{}_GENSIM_D86_fine_n{}_{}.root'.format(thing, n_events, strftime('%b%d'))
    common.logger.info('Output: %s', output_file)
    process.FEVTDEBUGoutput.fileName = cms.untracked.string(output_file)

    common.add_generator(process, thing)
    return process


from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('analysis')
options.register('thing', 'minbias', VarParsing.multiplicity.singleton, VarParsing.varType.string, 'Choices: "tau", "muon", "minbias"')
options.register('n', 1, VarParsing.multiplicity.singleton, VarParsing.varType.int, 'Number of events')
options.parseArguments()
process = gensim(options.thing, n_events=options.n)
common.logger.info('Created process %s', process)

