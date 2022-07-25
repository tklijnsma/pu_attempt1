from __future__ import print_function
from contextlib import contextmanager

import ROOT
from DataFormats.FWLite import Events, Handle

@contextmanager
def open_root(rootfile, mode='read'):
    try:
        tfile = ROOT.TFile.Open(rootfile, mode)
        yield tfile
    finally:
        tfile.Close()

def repr_genparticle(p):
    return (
        '<pdgid={pdgid:<5d} E={e:{ff}} pt={pt:{ff}} eta={eta:{ff}} phi={phi:{ff}} status={status:<3d}>'
        .format(
            pdgid = p.pdgId(),
            e=p.energy(),
            pt=p.pt(),
            eta=p.eta(),
            phi=p.phi(),
            status=p.status(),
            ff='<7.2f'
            )
        )

def print_gen_particles(rootfile):
    with open_root(rootfile) as f:
        t = f.Get('Events')

        for _ in t:
            genparticles_vector = t.recoGenParticles_genParticles__GEN.product()            
            for p in genparticles_vector:
                print(repr_genparticle(p))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('rootfile', type=str)
    args = parser.parse_args()
    print_gen_particles(args.rootfile)
