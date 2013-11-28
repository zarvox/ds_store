#!/usr/bin/env python

# By Drew Fisher <zarvox@zarvox.org>
# I release this software into the public domain.

import os
import sys

from alias import AliasRecord
from dsstore import DSStoreFile

def analyze_freelist(freelist):
    ranges = []
    for x in xrange(len(freelist)):
        size = 2 ** x
        for offset in freelist[x].Offset:
            ranges.append((offset, offset + size))
    ranges.sort()
    i = 0
    while i < len(ranges) - 1:
        if ranges[i][1] == ranges[i+1][0]:
            merged = (ranges[i][0], ranges[i+1][1])
            del ranges[i]
            ranges[i] = merged
        else:
            i += 1
    print "Free ranges:"
    for r in ranges:
        print r

if __name__ == "__main__":
    path = os.path.expanduser("~/.DS_Store")
    if len(sys.argv) > 1:
        path = sys.argv[1]
    with open(path) as f:
        buf = f.read()
    ds_store = DSStoreFile.parse(buf)
    print ds_store.BuddyAllocatorMetadata.BTreeMetadata
    aliasrecorddata = [ entry.RecordData for entry in ds_store.BuddyAllocatorMetadata.BTreeMetadata.BTreeNode.BlockData if entry.RecordType == 'icvp' ][0]['backgroundImageAlias']
    aliasrecord = AliasRecord.parse(aliasrecorddata)
    print aliasrecord
    #freelist = ds_store.BuddyAllocatorMetadata.FreeList
    #analyze_freelist(freelist)

