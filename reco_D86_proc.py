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


    # _____________________________________________
    # Special settings for merging
    process.load("SimTracker.TrackAssociation.trackingParticleRecoTrackAsssociation_cfi")
    # append the HGCTruthProducer to the recosim step

    # # If you want to run the associations or SC merging
    # from SimCalorimetry.HGCalSimProducers.hgcHitAssociation_cfi import lcAssocByEnergyScoreProducer, scAssocByEnergyScoreProducer
    # from SimCalorimetry.HGCalAssociatorProducers.LCToCPAssociation_cfi import layerClusterCaloParticleAssociation as layerClusterCaloParticleAssociationProducer
    # from SimCalorimetry.HGCalAssociatorProducers.LCToSCAssociation_cfi import layerClusterSimClusterAssociation as layerClusterSimClusterAssociationProducer

    # process.lcAssocByEnergyScoreProducer = lcAssocByEnergyScoreProducer
    # process.layerClusterCaloParticleAssociationProducer = layerClusterSimClusterAssociationProducer
    # process.scAssocByEnergyScoreProducer = scAssocByEnergyScoreProducer
    # process.layerClusterSimClusterAssociationProducer = layerClusterCaloParticleAssociationProducer

    # process.hgcalAssociators = cms.Task(
    #     process.lcAssocByEnergyScoreProducer,
    #     process.layerClusterCaloParticleAssociationProducer,
    #     process.scAssocByEnergyScoreProducer,
    #     process.layerClusterSimClusterAssociationProducer,
    #     process.trackingParticleRecoTrackAsssociation
    #     )

    # process.assoc = cms.Sequence(process.hgcalAssociators)
    # process.recosim_step *= process.assoc
    # _____________________________________________


    process.FEVTDEBUGHLToutput.outputCommands.extend([
        "keep *_*G4*_*_*",
        "keep *_MergedTrackTruth_*_*",
        "keep *_trackingParticleRecoTrackAsssociation_*_*", 
        "keep *_hgcRecHitsToSimClusters_*_*", 
        "keep SimClustersedmAssociation_mix_*_*", "keep CaloParticlesedmAssociation_mix_*_*", 
        "keep *_pfParticles_*_*",
        "keep recoPFRecHits_*_*_*", 
        "keep *_hgcSimTruth_*_*",
        "keep *_lcAssocByEnergyScoreProcer_*_*",
        "keep *_layerClusterCaloParticleAssociationProducer_*_*",
        "keep *_scAssocByEnergyScoreProducer_*_*",
        "keep *_layerClusterSimClusterAssociationProducer_*_*",
        "keep *_AllSimTracksAndVerticesProducer_*_*",
        ])

    # process.cfviewer = cms.EDAnalyzer("cfviewer")
    # process.cfviewer_step = cms.Path(process.cfviewer)
    # process.schedule.append(process.cfviewer_step)

    process.AllSimTracksAndVerticesProducer = cms.EDProducer("AllSimTracksAndVerticesProducer")
    process.AllSimTracksAndVerticesProducer_step = cms.Path(process.AllSimTracksAndVerticesProducer)
    process.schedule.append(process.AllSimTracksAndVerticesProducer_step)

    return process


from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('analysis')
options.register('pu', '', VarParsing.multiplicity.list, VarParsing.varType.string, 'List of PU rootfiles')
options.register('n', 1, VarParsing.multiplicity.singleton, VarParsing.varType.int, 'Number of events')
options.parseArguments()
process = reco(options.inputFiles, options.pu, n_events=options.n)
common.logger.info('Created process %s', process)
