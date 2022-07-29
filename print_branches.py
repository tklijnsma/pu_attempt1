#!/usr/bin/env python 
from __future__ import print_function

"""
Takes a path to a root file, and prints the branches of the
found TTrees.
"""

import sys, os.path as osp, os, argparse

try:
    import ROOT
except ImportError:
    print('ROOT could not be imported')
    sys.exit(1)

def iter_trees_recursively(node, directory=''):
    listofkeys = node.GetListOfKeys()
    n_keys = listofkeys.GetEntries()
    for i_key in range(n_keys):
        key = listofkeys[i_key]
        classname = key.GetClassName()
        # Recurse through TDirectories
        if classname == 'TDirectoryFile':
            dirname = key.GetName()
            lower_node = node.Get(dirname)
            print('\033[31mTDirectory {0}\033[0m'.format(dirname))
            iter_trees_recursively(lower_node, directory=dirname)
            continue
        elif not classname == 'TTree':
            continue
        treename = key.GetName()
        tree = node.Get(treename)
        n_entries = tree.GetEntries()
        listofbranches = tree.GetListOfBranches()
        n_branches = listofbranches.GetEntries()
        indent = '  ' if directory else ''
        print(
            '\033[31m{indent}TTree {0} ({1} entries)\033[0m'
            .format(treename, n_entries, indent=indent)
            )
        for i_branch in range(n_branches):
            branch = listofbranches[i_branch]
            print(
                '{indent}  {branch_name}'
                .format(indent=indent, branch_name=branch.GetName())
                )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('rootfile', type=str, help='Path to a root file')
    args = parser.parse_args()
    try:
        tfile = ROOT.TFile.Open(args.rootfile)
        iter_trees_recursively(tfile)
    finally:
        # Always try to close
        try:
            tfile.Close()
        except:
            pass

if __name__ == '__main__':
    main()