from __future__ import print_function
from contextlib import contextmanager
from itertools import chain


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

class Track:
    def __init__(self, track):
        self.track = track
        self.parent = None
        self.children = []

    @property
    def id(self):
        return self.track.trackId()

    def add_child(self, child):
        self.children.append(child)
        child.parent = self
    
    def add_parent(self, parent):
        parent.add_child(self)

    @property
    def is_root(self):
        return self.parent is None

    def __repr__(self):
        t = self.track
        mom = t.momentum()
        return (
            '<trackid={trackid:6d}'
            ' pdgid={pdgid:<5d}'
            ' E={e:{ff}}'
            ' pt={pt:{ff}}'
            ' eta={eta:{ff}}'
            ' phi={phi:{ff}}'
            ' crossed_b={crossed_boundary}'
            '>'
            .format(
                trackid = t.trackId(),
                pdgid = t.type(),
                e=mom.E(),
                pt=mom.Pt(),
                eta=mom.Eta(),
                phi=mom.Phi(),
                crossed_boundary = int(t.crossedBoundary()),
                ff='<7.2f'
                )
            )


def dfs(track, depth=0):
    yield track, depth
    for child in track.children:
        for _ in dfs(child, depth+1):
            yield _

def print_sim(rootfile, n=1):
    with open_root(rootfile) as f:
        tree = f.Get('Events')
        i = 0
        for _ in tree:
            i += 1
            print('event %s' % i)

            def get(branch):
                try:
                    return getattr(tree, branch).product()
                except AttributeError:
                    try:
                        return getattr(tree, branch + 'SIM').product()
                    except AttributeError:
                        return getattr(tree, branch + 'HLT').product()

            # genparticles = [i for i in tree.recoGenParticles_genParticles__GEN.product()]
            simtracks = [Track(i) for i in get('SimTracks_g4SimHits__')]
            simtrack_ids = [t.id for t in simtracks]
            simvertices = [i for i in get('SimVertexs_g4SimHits__')]

            hitcount_per_track = {}
            for t in simtracks:
                parent_id = simvertices[t.track.vertIndex()].parentIndex()
                if parent_id != -1:
                    t.add_parent(simtracks[simtrack_ids.index(parent_id)])
                hitcount_per_track[t.id] = 0

            roots = [t for t in simtracks if t.is_root]

            for branch in [
                'PCaloHits_g4SimHits_HGCHitsEE_SIM',
                'PCaloHits_g4SimHits_HGCHitsHEback_SIM',
                'PCaloHits_g4SimHits_HGCHitsHEfront_SIM',
                ]:
                for hit in get(branch):
                    trackid = hit.geantTrackId()
                    hitcount_per_track[trackid] += 1

            for root in roots:
                for t, depth in dfs(root):
                    print('  '*depth + f'{t} nhits={hitcount_per_track[t.id]}')


            # hits = [h for h in get('PCaloHits_g4SimHits_HGCHitsEE_')]
            # print('%s hits' % len(hits))

            try:
                print('\nCaloParticles:')
                for p in get('CaloParticles_mix_MergedCaloTruth_'):
                    print('event_id={} trackId={}'.format(p.eventId().rawId(), p.particleId()))
            except AttributeError:
                print('Could not print CaloParticles')

            if i >= n: return



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('rootfile', type=str)
    parser.add_argument('-n', '--nevents', type=int, default=1)
    args = parser.parse_args()
    print_sim(args.rootfile, n=args.nevents)
