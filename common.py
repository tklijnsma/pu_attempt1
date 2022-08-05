from __future__ import print_function

import logging
from collections import OrderedDict
import subprocess
import copy
import importlib
import os, os.path as osp
from functools import cached_property

import FWCore.ParameterSet.Config as cms


def setup_logger(name='myproc'):
    if name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.info('Logger %s is already defined', name)
    else:
        fmt = logging.Formatter(
            fmt = (
                '\033[34m%(levelname)7s:%(asctime)s:%(module)s:%(lineno)s\033[0m'
                + ' %(message)s'
                ),
            datefmt='%Y-%m-%d %H:%M:%S'
            )
        handler = logging.StreamHandler()
        handler.setFormatter(fmt)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
    return logger
logger = setup_logger()
subprocess_logger = setup_logger('subp')
subprocess_logger.handlers[0].formatter._fmt = '\033[35m%(asctime)s\033[0m %(message)s'


class CMSDriver(object):
    def __init__(self, *args, **kwargs):
        self.args = list(args)
        self.kwargs = OrderedDict()
        for k in sorted(kwargs.keys()): self.kwargs[k] = kwargs[k]

    @property
    def cmd(self):
        cmd_list = ['cmsDriver.py'] + self.args
        for k, v in self.kwargs.items(): cmd_list.extend([k, v])
        return cmd_list

    def __repr__(self):
        s = '<cmsDriver.py'
        for arg in self.args: s += '\n  ' + str(arg)
        for k, v in self.kwargs.items(): s += '\n  {} {}'.format(k, v)
        s += '\n  >'
        return s
    
    @property
    def outfile(self):
        if '--python_filename' in self.kwargs: return self.kwargs['--python_filename']
        name = self.args[0]
        if '-s' in self.kwargs:
            name += self.kwargs['-s'].replace(',', '_')
        return name + '.py'

    @cached_property
    def hash(self):
        import hashlib
        return hashlib.sha224(self.__repr__().encode()).hexdigest()


def run_command(cmd, dry=False, stdout=None, stderr=None, stop_on_error=True):
    """
    Runs a command and captures output.
    Returns return code and captured output.
    """
    logger.info('%sIssuing command %s', '(dry) ' if dry else '', ' '.join(cmd))
    if dry: return 0, '<dry output>'
    process = subprocess.Popen(
        cmd,
        stdout=(subprocess.PIPE if stdout is None else stdout),
        stderr=(subprocess.STDOUT if stderr is None else stderr),
        universal_newlines=True,
        )
    # Start running command and capturing output
    output = []
    for stdout_line in iter(process.stdout.readline, ''):
        subprocess_logger.debug(stdout_line.strip('\n'))
        output.append(stdout_line)
    process.stdout.close()
    process.wait()
    if stop_on_error and process.returncode != 0:
        raise Exception('Status {}!'.format(process.returncode))
    return process.returncode, output


def run_driver_cmd(driver, *args, **kwargs):
    recreate = kwargs.pop('recreate', False)
    # Make sure outfile is clearly defined
    outfile = kwargs.pop('outfile', None)
    if outfile:
        driver = copy.deepcopy(driver)
        driver.kwargs['--python_filename'] = outfile
    elif '--python_filename' not in driver.kwargs:
        driver.kwargs['--python_filename'] = 'tmp.py'
    # Determine whether driver command should be rerun:
    # - if recreate option is True
    # - if the outfile does not exist yet
    # - if the hash stored in the outfile differs from the driver hash
    #   (i.e. the command has changed)
    def run():
        logger.info('Running driver command %s', driver)
        output = run_command(driver.cmd, *args, **kwargs)
        add_hash_to_file(driver.outfile, driver.hash)
        return output
    if recreate:
        logger.info(f'Force recreating {outfile}')
        run()
    elif not(osp.isfile(driver.outfile)):
        logger.info(f'{outfile} does not exist yet')
        run()
    elif (stored_hash:=read_hash(driver.outfile)) != driver.hash:
        logger.info(f'Hash in {outfile} {stored_hash} != {driver.hash}')
        run()
    else:
        logger.info(
            f'Not running driver command; {driver.outfile} exists and hashes match.'
            f' Driver:\n{driver}'
            )


def add_hash_to_file(filename, hash):
    logger.info(f'Adding hash {hash} to {filename}')
    with open(filename, 'r') as f:
        txt = f.read()
    txt = f'#{hash}\n' + txt
    with open(filename, 'w') as f:
        f.write(txt)


def read_hash(filename):
    with open(filename, 'r') as f:
        return f.readline().strip().lstrip('#')


def load_process_from_driver(driver, outfile=None):
    """
    Runs a driver command, dumping the output in `outfile`.
    Then imports that outfile, and returns the `process` variable
    from it.
    """
    run_driver_cmd(driver, outfile=outfile)
    process = importlib.import_module(driver.kwargs['--python_filename'].replace('.py', '')).process
    logger.info('Loaded process %s from %s', process, driver.kwargs['--python_filename'])
    return process


WARNED_ABOUT_EDM_ML_DEBUG = False

def add_debug_module(process, module_name):
    process.MessageLogger.cerr.threshold = "DEBUG"
    process.MessageLogger.cerr.FwkReport.limit = 1000
    process.MessageLogger.cerr.FwkSummary.limit = 1000
    process.MessageLogger.cerr.default.limit = 1000
    process.MessageLogger.debugModules.append(module_name)
    setattr(
        process.MessageLogger.cerr, module_name,
        cms.untracked.PSet(limit = cms.untracked.int32(10000000))
        )
    global WARNED_ABOUT_EDM_ML_DEBUG
    if not WARNED_ABOUT_EDM_ML_DEBUG:
        logger.warning(
            'Added debug module %s, but need'
            ' `scram b -j8 USER_CXXFLAGS="-DEDM_ML_DEBUG"`'
            ' in order for it to actually work.', module_name
            )
        WARNED_ABOUT_EDM_ML_DEBUG = True


def rng(process, seed=1001):
    """
    Sets the RandomNumberGeneratorService to a fixed seed
    """
    process.RandomNumberGeneratorService.generator.initialSeed = cms.untracked.uint32(seed)
    process.RandomNumberGeneratorService.VtxSmeared.initialSeed = cms.untracked.uint32(seed)
    process.RandomNumberGeneratorService.mix.initialSeed = cms.untracked.uint32(seed)
    logger.info('Set RNG to seed %s', seed)


def activate_finecalo(process):
    for module_name in ['CaloSD', 'CaloTrkProcessing', 'TrackingAction']:
        pset = getattr(process.g4SimHits, module_name)
        pset.DoFineCalo = cms.bool(True)
        pset.UseFineCalo = [2]
        pset.EminFineTrack = cms.double(0.0)
        add_debug_module(process, 'DoFineCalo')


def add_generator(process, thing):
    if thing in {'muon', 'tau'}:
        pdgid = dict(muon=13, tau=15)[thing]
        process.generator = cms.EDProducer("FlatRandomEGunProducer",
            AddAntiParticle = cms.bool(True),
            PGunParameters = cms.PSet(
                MaxEta = cms.double(3.0),
                MaxPhi = cms.double(3.14159265359),
                MaxE = cms.double(35.0),
                MinEta = cms.double(1.479),
                MinPhi = cms.double(-3.14159265359),
                MinE = cms.double(35.0),
                PartID = cms.vint32(pdgid)
                ),
            Verbosity = cms.untracked.int32(0),
            firstRun = cms.untracked.uint32(1),
            psethack = cms.string('multiple particles predefined pT/E eta 1p479 to 3')
            )
    elif thing == 'minbias':
        process_parameters = cms.vstring(
            'SoftQCD:nonDiffractive = on',
            'SoftQCD:singleDiffractive = on',
            'SoftQCD:doubleDiffractive = on',
            )
        # if pt_min is not None: process_parameters.append('PhaseSpace:pTHatMin = {}'.format(pt_min))
        # if pt_max is not None: process_parameters.append('PhaseSpace:pTHatMax = {}'.format(pt_max))
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
                processParameters = process_parameters,
                parameterSets = cms.vstring(
                    'pythia8CommonSettings',
                    'pythia8CP5Settings',
                    'processParameters',
                    )
                )
            )
    else:
        raise Exception('Unknown thing %s' % thing)


def guntype(filename):
    basename = osp.basename(filename)
    for keyword in ['muon', 'tau', 'minbias']:
        if keyword in basename:
            return keyword
    else:
        raise Exception('Could not find a keyword')
