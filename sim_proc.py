import os, os.path as osp, importlib

import FWCore.ParameterSet.Config as cms

import common


def sim(
    input_rootfiles,
    outfile=None, dofinecalo=True,
    pt_min=None, pt_max=None,
    pu_rootfiles=None,
    n_events=-1
    ):
    """
    Creates a cms.Process() instance.
    First loads baseline process from fragment file, and then modifies it.
    """
    # Some IO validation
    if isinstance(input_rootfiles, basestring): input_rootfiles = [input_rootfiles]
    for i, f in enumerate(input_rootfiles):
        if not f.startswith('file:'): input_rootfiles[i] = 'file:' + f

    # Format outfile
    if outfile is None:
        outfile = input_rootfiles[0].replace('.root', '_SIM.root')
    outfile = outfile.replace('_GEN', '')
    if pu_rootfiles:
        outfile = outfile.replace('.root', '_PU.root')
    outfile = outfile.replace('.root', '_fine.root' if dofinecalo else '_default.root')    
    if not outfile.startswith('file:'): outfile = 'file:' + outfile
    common.logger.info('Will write output to %s', outfile)

    driver = common.CMSDriver('TTbar_14TeV_TuneCP5_cfi', '--no_exec')
    driver.kwargs.update({
        '--conditions'      : 'auto:phase2_realistic_T15',
        '--era'             : 'Phase2C9',
        '--eventcontent'    : 'FEVTDEBUG',
        '-s'                : 'SIM',
        '--datatier'        : 'SIM',
        '--beamspot'        : 'NoSmear',
        '--geometry'        : 'Extended2026D49',
        '--pileup'          : 'AVE_200_BX_25ns' if pu_rootfiles else 'NoPileUp',
        })
    if dofinecalo: driver.kwargs['--procModifier'] = 'fineCalo'
    process = common.load_process_from_driver(driver, 'sim_driver.py')

    if dofinecalo:
        for module_name in ['CaloSD', 'CaloTrkProcessing', 'TrackingAction']:
            pset = getattr(process.g4SimHits, module_name)
            pset.DoFineCalo = cms.bool(True)
            pset.UseFineCalo = [2]
            pset.EminFineTrack = cms.double(0.0)
    
    process.maxEvents.input = cms.untracked.int32(n_events)

    # random seeds
    process.RandomNumberGeneratorService.generator.initialSeed = cms.untracked.uint32(1)
    process.RandomNumberGeneratorService.VtxSmeared.initialSeed = cms.untracked.uint32(1)
    process.RandomNumberGeneratorService.mix.initialSeed = cms.untracked.uint32(1)

    # Input source
    process.source.firstLuminosityBlock = cms.untracked.uint32(1)
    process.source.fileNames = cms.untracked.vstring(input_rootfiles)

    # Output definition
    process.FEVTDEBUGoutput.fileName = cms.untracked.string(outfile)

    # PU mixing
    if pu_rootfiles:
        common.logger.info('Doing pu mixing: %s', ', '.join(pu_rootfiles))
        process.load("SimGeneral.MixingModule.mix_POISSON_average_cfi")
        process.mix.input.nbPileupEvents.averageNumber = cms.double(4.)
        process.mix.input.fileNames = cms.untracked.vstring(pu_rootfiles)

        # process.mix.input.nbPileupEvents.averageNumber = cms.double(200.000000)
        process.mix.bunchspace = cms.int32(25)
        process.mix.minBunch = cms.int32(-3)
        process.mix.maxBunch = cms.int32(3)
        process.mix.input.fileNames = cms.untracked.vstring([])
        process.mix.digitizers = cms.PSet(process.theDigitizersValid)

        


    common.add_debug_module(process, 'DoFineCalo')
    common.add_debug_module(process, 'mix')
    common.add_debug_module(process, 'MixingModule')

    return process


from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('analysis')
options.register('pu', '', VarParsing.multiplicity.list, VarParsing.varType.string, 'List of PU rootfiles')
options.register('n', 1, VarParsing.multiplicity.singleton, VarParsing.varType.int, 'Number of events')
options.parseArguments()
process = sim(options.inputFiles, pu_rootfiles=options.pu, n_events=options.n)
common.logger.info('Created process %s', process)
