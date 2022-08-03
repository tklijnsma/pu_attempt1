from __future__ import print_function
import numpy as np
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

def repr_dfs(track):
    s = ''
    for t, depth in dfs(track):
        s += depth*'  ' + str(t) + '\n'
    return s.rstrip()

def build_tree(tracks, vertices):
    tracks = [Track(t) for t in tracks]
    track_ids = [t.id for t in tracks]
    for t in tracks:
        parent_id = vertices[t.track.vertIndex()].parentIndex()
        if parent_id != -1:
            t.add_parent(tracks[track_ids.index(parent_id)])
    roots = [t for t in tracks if t.is_root]
    return roots


def print_tracks_and_vertices(rootfile, n):
    with open_root(rootfile) as f:
        tree = f.Get('Events')
        i = 0
        for _ in tree:
            i += 1
            print(f'{rootfile}: event {i}')

            tracks = tree.SimTracks_AllSimTracksAndVerticesProducer_AllSimTracks_RECO.product()
            vertices = tree.SimVertexs_AllSimTracksAndVerticesProducer_AllSimVertices_RECO.product()

            print(f'Found {len(tracks)} tracks and {len(vertices)} vertices')

            roots = build_tree(tracks, vertices)

            for root in roots:
                print(repr_dfs(root))




if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('rootfile', type=str)
    parser.add_argument('-n', '--nevents', type=int, default=1)
    args = parser.parse_args()
    print_tracks_and_vertices(args.rootfile, n=args.nevents)
