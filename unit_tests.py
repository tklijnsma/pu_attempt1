from __future__ import print_function

import common


def test_cmsdriver():
    driver = common.CMSDriver('TTbar_14TeV_TuneCP5_cfi')
    driver.args.extend(['--no_exec'])
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
        '--python_filename' : 'test.py',
        })
    print(driver)
    # common.run_driver_cmd(driver)
    process = common.load_process_from_driver(driver)

if __name__ == '__main__':
    test_cmsdriver()