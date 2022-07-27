from __future__ import print_function
from pprint import pprint, pformat
from time import strftime

import common

import FWCore.ParameterSet.Config as cms


driver = common.CMSDriver('TTbar_14TeV_TuneCP5_cfi', '--no_exec')
driver.kwargs.update({
    '--conditions'   : 'auto:phase2_realistic_T15',
    '--era'          : 'Phase2C9',
    '--eventcontent' : 'FEVTDEBUG',
    '-s'             : 'GEN,SIM,DIGI:pdigi_valid,L1,L1TrackTrigger,DIGI2RAW,HLT:@fake2',
    '--datatier'     : 'GEN-SIM',
    '--beamspot'     : 'NoSmear',
    '--geometry'     : 'Extended2026D49',
    '--pileup'       : 'AVE_200_BX_25ns',
    '--procModifier' : 'fineCalo',
    })

def gensim():
    process = common.load_process_from_driver(driver, 'gensim_driver.py')
    common.rng(process, 1)
    process.maxEvents.input = cms.untracked.int32(1)
    process.source.firstLuminosityBlock = cms.untracked.uint32(1)
    
    process.FEVTDEBUGoutput.fileName = cms.untracked.string(strftime('file:muon_GENSIM_PU_fine_%b%d.root'))

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


    for module_name in ['CaloSD', 'CaloTrkProcessing', 'TrackingAction']:
        pset = getattr(process.g4SimHits, module_name)
        pset.DoFineCalo = cms.bool(True)
        pset.UseFineCalo = [2]
        pset.EminFineTrack = cms.double(0.0)

    # pu_rootfile = 'file:minbias_SIM_fine.root'
    # common.logger.info('Doing pu mixing: file:minbias_SIM_fine.root')
    process.load("SimGeneral.MixingModule.mix_POISSON_average_cfi")
    process.mix.input.nbPileupEvents.averageNumber = cms.double(4.)
    process.mix.input.fileNames = cms.untracked.vstring('file:minbias_SIM_fine.root')
    # process.mix.input.fileNames = cms.untracked.vstring([
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/101440b7-3fbe-415a-bdee-d0ae744ad240.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/24dfaf66-12d0-4a6f-b203-c2d51cfac1ac.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/4cf74e5e-ce29-4a74-b300-6506653b366a.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/65b9a8f8-f28e-4b0d-8534-3e2220f3ac8d.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/688e0ca4-156f-47c4-9c6c-c0ea8a0f3f5a.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/7da95fdd-e9dd-4f5b-a98d-ba95a0948a08.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/a226653e-25a1-483b-8445-579fe186feeb.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/af03e700-aa75-44ed-8dd2-f8c31c042465.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/d885ae2b-9687-402e-8eb8-1c649656cf14.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/e457e496-55c7-4d65-8218-31b5d502bef3.root',
    #     '/store/relval/CMSSW_11_3_0_pre3/RelValMinBias_14TeV/GEN-SIM/113X_mcRun4_realistic_v3_2026D49noPU-v1/00000/fd5040a0-5240-453f-a6af-c07c528cba38.root',
    #     ])
    process.mix.bunchspace = cms.int32(25)
    process.mix.minBunch = cms.int32(-3)
    process.mix.maxBunch = cms.int32(3)
    process.mix.digitizers = cms.PSet(process.theDigitizersValid)

    common.add_debug_module(process, 'DoFineCalo')
    common.add_debug_module(process, 'mix')
    common.add_debug_module(process, 'MixingModule')

    common.logger.info('process.mix = \n{}'.format(process.mix))
    common.logger.info('process.mix.input = \n{}'.format(process.mix.input))
    common.logger.info('process.mix.input.fileNames = \n{}'.format(process.mix.input.fileNames))


    process.FEVTDEBUGoutput.outputCommands.append("keep *_*G4*_*_*")
    process.FEVTDEBUGoutput.outputCommands.append("keep SimClustersedmAssociation_mix_*_*")
    process.FEVTDEBUGoutput.outputCommands.append("keep CaloParticlesedmAssociation_mix_*_*")
    process.FEVTDEBUGoutput.outputCommands.append("keep *_*G4*_*_*")
    process.FEVTDEBUGoutput.outputCommands.append("keep *SimTrack*_*_*_*")
    
    return process

process = gensim()
common.logger.info('Created process %s', process)
