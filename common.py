from __future__ import print_function

import logging
from collections import OrderedDict
import subprocess
import copy
import importlib
import os, os.path as osp

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
    if recreate or not(osp.isfile(driver.outfile)):
        logger.info('Running driver command %s', driver)
        return run_command(driver.cmd, *args, **kwargs)
    else:
        logger.info('Not running driver command %s', driver)


def load_process_from_driver(driver, outfile=None):
    """
    Runs a driver command, dumping the output in `outfile`.
    Then imports that outfile, and returns the `process` variable
    from it.
    """
    if outfile:
        driver = copy.deepcopy(driver)
        driver.kwargs['--python_filename'] = outfile
    if '--python_filename' not in driver.kwargs: driver.kwargs['--python_filename'] = 'tmp.py'
    run_driver_cmd(driver)
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