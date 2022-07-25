from __future__ import print_function
from pprint import pprint, pformat

import common

import FWCore.ParameterSet.Config as cms


driver = common.CMSDriver('TTbar_14TeV_TuneCP5_cfi', '--no_exec')
driver.kwargs.update({
    '--conditions'      : 'auto:phase2_realistic_T15',
    '-n'                : '10',
    '--era'             : 'Phase2C9',
    '--eventcontent'    : 'FEVTDEBUG',
    '-s'                : 'GEN',
    '--datatier'        : 'GEN',
    '--beamspot'        : 'NoSmear',
    '--geometry'        : 'Extended2026D49',
    '--pileup'          : 'NoPileUp',
    })


def minbias(pt_min=None, pt_max=None, n_events=1):
    """
    Creates a cms.Process() instance.
    First loads baseline process from fragment file, and then modifies it.
    """
    process = common.load_process_from_driver(driver, 'gen_driver.py')
    common.rng(process, 1)
    process.maxEvents.input = cms.untracked.int32(n_events)
    process.source.firstLuminosityBlock = cms.untracked.uint32(1)
    process.FEVTDEBUGoutput.fileName = cms.untracked.string('file:minbias_GEN.root')

    # From hgcBiasedGenProcesses_cfi.py: minbias settings
    # Taken from https://cms-pdmv.cern.ch/mcm/public/restapi/requests/get_fragment/PPD-RunIIFall17GS-00004
    processParameters = cms.vstring(
        'SoftQCD:nonDiffractive = on',
        'SoftQCD:singleDiffractive = on',
        'SoftQCD:doubleDiffractive = on',
        )
    if pt_min is not None: processParameters.append('PhaseSpace:pTHatMin = {}'.format(pt_min))
    if pt_max is not None: processParameters.append('PhaseSpace:pTHatMax = {}'.format(pt_max))

    from Configuration.Generator.Pythia8CommonSettings_cfi import pythia8CommonSettingsBlock
    from Configuration.Generator.MCTunes2017.PythiaCP5Settings_cfi import pythia8CP5SettingsBlock

    process.generator = cms.EDFilter(
        "Pythia8GeneratorFilter",
        maxEventsToPrint = cms.untracked.int32(1),
        pythiaPylistVerbosity = cms.untracked.int32(1),
        filterEfficiency = cms.untracked.double(1.0),
        pythiaHepMCVerbosity = cms.untracked.bool(False),
        comEnergy = cms.double(14000.),
        PythiaParameters = cms.PSet(
            pythia8CommonSettingsBlock,
            pythia8CP5SettingsBlock,
            processParameters = processParameters,
            parameterSets = cms.vstring(
                'pythia8CommonSettings',
                'pythia8CP5Settings',
                'processParameters',
                )
            )
        )
    # Here potentially: A jet filter, to filter out events with very little activity (skipped for now)
    return process

def tau():
    process = common.load_process_from_driver(driver, 'gen_driver.py')
    common.rng(process, 1)
    process.maxEvents.input = cms.untracked.int32(1)
    process.source.firstLuminosityBlock = cms.untracked.uint32(1)
    process.FEVTDEBUGoutput.fileName = cms.untracked.string('file:tau_GEN.root')
    process.generator = cms.EDProducer("FlatRandomEGunProducer",
        AddAntiParticle = cms.bool(True),
        PGunParameters = cms.PSet(
            MaxEta = cms.double(3.0),
            MaxPhi = cms.double(3.14159265359),
            MaxE = cms.double(35.0),
            MinEta = cms.double(1.479),
            MinPhi = cms.double(-3.14159265359),
            MinE = cms.double(35.0),
            PartID = cms.vint32(13)
            ),
        Verbosity = cms.untracked.int32(0),
        firstRun = cms.untracked.uint32(1),
        psethack = cms.string('multiple particles predefined pT/E eta 1p479 to 3')
        )
    return process


from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('analysis')
options.register(
    'thing', 'minbias', VarParsing.multiplicity.singleton, VarParsing.varType.string, 'Thing to generate'
    )
options.register(
    'n', 1, VarParsing.multiplicity.singleton, VarParsing.varType.int, 'Number of events'
    )
options.parseArguments()

if options.thing not in locals(): raise Exception('Invalid thing %s' % options.thing)
common.logger.info('Doing %s', options.thing)
process = locals()[options.thing](n_events=options.n)
common.logger.info('Created process %s', process)