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

def repr_hgcrechit(h):
    s = (
        '<HGCRecHit id={} e={:.3f} t={:.3f} flags={:b}>'
        .format(
            h.id().rawId(), h.energy(), h.time(), h.flags()
            )
        )
    return s

def hash_hgcrechit(h):
    return hash((h.id().rawId(), h.energy(), h.time()))

def print_reco(rootfile, n=1):
    with open_root(rootfile) as f:
        tree = f.Get('Events')
        i = 0
        for _ in tree:
            i += 1
            print('event %s' % i)

            def get(branch):
                return [i for i in getattr(tree, branch).product()]


            ee_rechits = get('HGCRecHitsSorted_HGCalRecHit_HGCEERecHits_RECO')


            print(f'{len(ee_rechits)} ee rechits')
            print(f'{len(get("PCaloHits_g4SimHits_HGCHitsEE_SIM"))} ee simhits')
            print(f'{sum(h.time() >= 0. for h in ee_rechits)} ee hits with t>0')

            # print('CaloParticles:')
            # for p in get('CaloParticles_mix_MergedCaloTruth_'):
            #     print('event_id={} trackId={}'.format(p.eventId().rawId(), p.particleId()))


            def repr_sc(h):
                s = (
                    '<SimCluster particleId={} pdgId={:} energy={:.3f} nrechits={}>'
                    .format(
                        h.particleId(), h.pdgId(), h.energy(), h.numberOfRecHits()
                        )
                    )
                return s

            hit_set = { h.id().rawId() for h in ee_rechits }

            # Also add the other HGC subsystems
            for branch in [
                # 'HGCRecHitsSorted_HGCalRecHit_HGCEERecHits_RECO',
                'HGCRecHitsSorted_HGCalRecHit_HGCHEBRecHits_RECO',
                'HGCRecHitsSorted_HGCalRecHit_HGCHEFRecHits_RECO',
                # 'HGCRecHitsSorted_HGCalRecHit_HGCHFNoseRecHits_RECO',
                ]:
                hit_set.update((h.id().rawId() for h in get(branch)))

            print()
            n_rechits_total = 0
            n_rechits_found = 0
            for sc in get('SimClusters_mix_MergedCaloTruth_HLT'):
                print(repr_sc(sc))
                n_rechits_total += sc.numberOfRecHits()

                for pair in sc.hits_and_energies():
                    hit = pair.first
                    print(f'  {hit=}')
                    if hit in hit_set:
                        n_rechits_found += 1


            print(f'Counted {n_rechits_total} rechits in all simclusters')
            print(f'{n_rechits_found}/{n_rechits_total} rechits were found in ee_rechits')



            print('\nCaloParticles:')
            for p in get('CaloParticles_mix_MergedCaloTruth_HLT'):
                print('event_id={} trackId={}'.format(p.eventId().rawId(), p.particleId()))


            if i >= n: return



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('rootfile', type=str)
    parser.add_argument('-n', '--nevents', type=int, default=1)
    args = parser.parse_args()
    print_reco(args.rootfile, n=args.nevents)
