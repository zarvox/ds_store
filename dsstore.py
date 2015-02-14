#!/usr/bin/env python

# By Drew Fisher <zarvox@zarvox.org>
# I release this software into the public domain.

# This software was written based on the excellent and detailed description of
# the file format at:
# http://search.cpan.org/~wiml/Mac-Finder-DSStore/DSStoreFormat.pod
# Many of the comments in this code were lifted from that reference.

import biplist
from construct import Adapter, Anchor, Array, Bytes, Enum, Pointer, RepeatUntil, String, Struct, Switch, UBInt64, UBInt32, UBInt16, UBInt8

# This file contains a bunch of things related to the structure of a DS_Store file.

RecordType = Enum(Bytes("RecordType", 4),
        BKGD = 'BKGD', # 12-byte blob, directories only.  Three possible subtypes.
        ICVO = 'ICVO', # bool, directories only.
        Iloc = 'Iloc', # 16-byte blob - icon location.
        LSVO = 'LSVO',
        bwsp = 'bwsp',
        cmmt = 'cmmt',
        dilc = 'dilc',
        dscl = 'dscl',
        extn = 'extn',
        fwi0 = 'fwi0',
        fwsw = 'fwsw',
        fwvh = 'fwvh',
        GRP0 = 'GRP0', # ustr.  unknown.
        icnv = 'icnv', # Unknown, seen in LOVE's DS_Store
        icgo = 'icgo', # 8-byte blob, directories (and files?). Unknown. Probably two integers, and often the value 00 00 00 00 00 00 00 04.
        icsp = 'icsp', # 8-byte blob, directories only. Unknown, usually all but the last two bytes are zeroes.
        icvo = 'icvo', #
        icvp = 'icvp',
        icvt = 'icvt',
        info = 'info',
        logS = 'logS', # comp, logical size of directory's contents.  Appeared in 10.7
        lg1S = 'lg1S', # comp, logical size of directory's contents.  Appeared in 10.8, replacing logS
        lssp = 'lssp', # 8-byte blob, directories only.  Possibly the scroll position in list view mode?
        lsvo = 'lsvo',
        lsvt = 'lsvt',
        lsvp = 'lsvp',
        lsvP = 'lsvP',
        modD = 'modD', # dutc, directories only - modification date
        moDD = 'moDD', # dutc, directories only - modification date
        pBB0 = 'pBB0', # blob
        pBBk = 'pBBk', # blob, something to do with bookmarks
        phyS = 'phyS',
        ph1S = 'ph1S',
        pict = 'pict',
        vSrn = 'vSrn',
        vstl = 'vstl',
        )

longData = Struct("longData",
        UBInt32("Value")
        )

shorData = Struct("shorData",
        UBInt32("Value")
        )
boolData = Struct("boolData",
        UBInt8("Value")
        )
blobData = Struct("blobData",
        UBInt32("Length"),
        Bytes("Blob", lambda env:env.Length)
        )
typeData = Struct("typeData",
        RecordType
        )
ustrData = Struct("ustrData",
        UBInt32("Length"),
        String("Data", lambda env:env.Length * 2, encoding="utf_16_be")
        )
compData = Struct("compData",
        UBInt64("Value")
        )
dutcData = Struct("dutcData",
        UBInt64("Ticks") # UTCDateTime structure
        )

def BPlistData():
    return BPlistAdapter(
            blobData
            )

class BPlistAdapter(Adapter):
    def __init__(self, subcon):
        Adapter.__init__(self, subcon)
    def _encode(self, obj, context):
        return biplist.writePlistToString(obj.Blob)
    def _decode(self, obj, context):
        return biplist.readPlistFromString(obj.Blob)

DataType = Enum(Bytes("DataType", 4),
        LONG = 'long', # 'long' - integer (four bytes)
        SHOR = 'shor', # 'shor' - short integer, stored as four bytes, but
                       #          the first two are always zero
        BOOL = 'bool', # 'bool' - boolean value, stored as one byte
        BLOB = 'blob', # 'blob' - block of bytes, stored as integer
                       #          followed by that many bytes of data
        TYPE = 'type', # 'type' - four bytes containing a FourCharCode
        USTR = 'ustr', # 'ustr' - Unicode text string - stored as integer
                       #          character count followed by big-endian UTF-16
        COMP = 'comp', # 'comp' - 64-bit integer
        DUTC = 'dutc', # 'dutc' - A datestamp, represented as an 8-byte
                       #          integer count of the number of
                       #          (1/65536)-second intervals since the Mac
                       #          epoch in 1904. Given the name, this
                       #          probably corresponds to the UTCDateTime
                       #          structure.
        )

Record = Struct("Record",
        UBInt32("FilenameLength"), # Filename length, in characters, as an integer
        String("Filename", lambda env:env.FilenameLength * 2, encoding="utf_16_be"), # Filename, in big-endian UTF-16
        RecordType, # a FourCharCode indicating what property of the file this entry describes
        DataType, # What kind of data field follows
        Switch("RecordData", lambda env: env.RecordType,
            {
                'BKGD': blobData, # 12-byte blob, directories only.  Three possible subtypes.
                'ICVO': boolData, # bool, directories only.  Always 1, so 0 must be the default value
                'Iloc': blobData, # 16-byte blob - icon location.
                                  #   4 bytes horizontal position of the icon's center
                                  #   4 bytes vertical position of the icon's center
                                  #   6 bytes 0xff
                                  #   2 bytes 0x00
                                  # Icon size comes from icvo blob.
                'LSVO': boolData, # bool, directories only.  Purpose unknown.
                'bwsp': BPlistData(), # blob containing a binary plist.  Contains size and layout of the window.
                                  # "The plist contains the keys WindowBounds
                                  # (a string in the same format in which
                                  # AppKit saves window frames); SidebarWidth
                                  # (a float), and booleans ShowSidebar,
                                  # ShowToolbar, ShowStatusBar, and
                                  # ShowPathbar. Sometimes contains ViewStyle
                                  # (a string), TargetURL (a string), and
                                  # TargetPath (an array of strings)."
                'cmmt': ustrData, # ustr, containing a file's Spotlight Comments
                'dilc': blobData, # 32-byte blob, unknown, might be icon location when files are displayed on the desktop
                'dscl': boolData, # bool.  Indicates that the subdir is open (disclosed) in list view.
                'extn': ustrData, # Often contains extension of the file, but sometimes contains a different extension.  Purpose unknown.
                'fwi0': blobData, # 16-byte blob.  Finder window information.
                'fwsw': longData, # long, finder window sidebar width (in pixels/points).  Zero if collapsed.
                'fwvh': shorData, # short, finder window vertical height.  overrides height in fwi0 if present.
                'GRP0': ustrData, # ustr.  unknown.
                'icgo': blobData, # 8-byte blob, directories (and files?). Unknown. Probably two integers, and often the value 00 00 00 00 00 00 00 04.
                'icsp': blobData, # 8-byte blob, directories only. Unknown, usually all but the last two bytes are zeroes.
                'icvo': blobData, # 18- or 26-byte blob.  Icon view options.
                'icvp': BPlistData(), # blob containing a plist, giving settings for the icon view.  appears to supplant icvo.
                                  # The plist holds a dictionary with several key-value pairs:
                                  # booleans `showIconPreview`, `showItemInfo`, and `labelOnBottom`;
                                  # numbers `scrollPositionX`, `scrollPositionY`, `gridOffsetX`, `gridOffsetY`, `textSize`,
                                  #         `iconSize`, `gridSpacing`, and `viewOptionsVersion`;
                                  # string `arrangeBy`.

                                  # The value of the `backgroundType` key (an integer) presumably controls the presence
                                  # of further optional keys such as
                                  # backgroundColorRed/backgroundColorGreen/backgroundColorBlue.
                'icvt': shorData, # icon view text label (filename) size, in points
                'info': blobData, # 40 or 48-byte blob, unknown format
                'logS': compData, # comp, logical size of directory's contents.  Appeared in 10.7
                'lg1S': compData, # comp, logical size of directory's contents.  Appeared in 10.8, replacing logS
                'lssp': blobData, # 8-byte blob, directories only.  Possibly the scroll position in list view mode?
                'lsvo': blobData, # 76-byte blob.  List view options.  Supplanted by lsv[pP]
                'lsvt': shorData, # List view text (filename) size, in points
                'lsvp': BPlistData(), # blob containing a binary plist.  List view settings, perhaps supplanting the 'lsvo' record.
                                  # Contains booleans for keys `showIconPreview`, `useRelativeDates`, `calculateAllSizes`
                                  #          numbers for keys `scrollPositionX`, `scrollPositionY`, `textSize`, `iconSize`,
                                  #                           `viewOptionsVersion` (usually 1)
                                  #          string for key `sortColumn`
                                  #          array for key `columns`
                'lsvP': BPlistData(), # Same as lsvp, but with dictionary for `columns` instead of array
                'modD': dutcData, # dutc, directories only - modification date
                'moDD': dutcData, # dutc, directories only - modification date
                'pBB0': blobData, # blob, something to do with app-sandbox.read-write
                'pBBk': blobData, # blob, something to do with bookmarks
                'phyS': compData, # comp, a multiple of 8192, and slightly larger than logS.  Presumably the physical size
                'ph1S': compData, # see phyS
                'pict': blobData, # variable length blob, dirs only.  Alias
                                  # record which resolves to the file
                                  # containing the actual background image.
                'vSrn': longData, # always contains the value 1.
                'vstl': typeData, # Directories only.  Indicates the style of
                                  # view (one of icnv, clmv, Nlsv, or Flwv,
                                  # indicating icon view, column/browser view,
                                  # list view, or coverflow view) selected by
                                  # Finder's "Always open in <view>" checkbox.
            }),
        )

BuddyAllocatorHeader = Struct("BuddyAllocatorHeader",
        Bytes("Magic", 4),          # 0x42756431 'Bud1'
        UBInt32("InfoBlockOffset"), # "Offset to the allocator's bookkeeping information block"
        UBInt32("InfoBlockSize"),   # "Size of the allocator's bookkeeping information block"
        UBInt32("InfoBlockOffsetBackup"), # "A second copy of the offset; the
                                          # Finder will refuse to read the file
                                          # if this does not match the first
                                          # copy. Perhaps this is a safeguard
                                          # against corruption from an
                                          # interrupted write transaction."
        Bytes("Unknown", 16),
        )

def roundUpToNearest256(i):
    modulus = i % 256
    if modulus == 0:
        return i
    else:
        return i - modulus + 256

FreeList = Struct("FreeList",
        UBInt32("Count"),
        Array(lambda env:env.Count, UBInt32("Offset")),
        )

BuddyDirEnt = Struct("BuddyDirEnt",
        UBInt8("Length"),
        Bytes("Name", lambda env:env.Length),
        UBInt32("BlockNumber"),
        )

InternalNodeData = Struct("InternalNodeData",
        UBInt32("ChildBlockNumber"),
        Record
        )

BTreeNode = Struct("BTreeNode",
        UBInt32("P"), # if 0, leaf node, if nonzero, BlockNumber at the end of the list
        UBInt32("Count"),
        # TODO finish this
        #Probe(),
        Switch("BlockData", lambda env: env.P == 0, {
                    True: Array(lambda env:env.Count, Record), # leaf node
                    False: Array(lambda env:env.Count, InternalNodeData),
                    }
              )
        )

BTreeMetadata = Struct("BTreeMetadata",
        UBInt32("RootBlockNumber"), # the block number of the root node of the B-tree
        UBInt32("NumLevels"), # Tree height minus one - for a tree with a single, leaf node, this is 0
        UBInt32("NumRecords"), # Number of records in the tree
        UBInt32("NumNodes"), # Number of nodes in this tree, not counting this header block
        UBInt32("PageSize"), # Always 4096.
        # Deref the root node
        Pointer(lambda env: env._._.ArenaOffset + offsetFromAddress(env._.BlockAddresses[env.RootBlockNumber]) , BTreeNode)
        )

BuddyAllocatorMetadata = Struct("BuddyAllocatorMetadata",
        UBInt32("NumBlocks"), # The number of blocks in the allocated-blocks list
        UBInt32("Zeros"),     # Always zero.
        Array(lambda env:roundUpToNearest256(env.NumBlocks), UBInt32("BlockAddresses")), # Block addresses.
        # Array of integers. There are NumBlocks block addresses here, with
        # unassigned block numbers represented by zeroes. This is followed by
        # enough zeroes to round the section up to the next multiple of 256
        # entries (1024 bytes).

        # A directory that always appears to have exactly one entry: "DSDB"
        UBInt32("DirectoryCount"),
        Array(lambda env:env.DirectoryCount, BuddyDirEnt),

        # DSDB is a pointer to the BTreeMetadata
        Pointer(lambda env: env._.ArenaOffset + offsetFromAddress(env.BlockAddresses[next((x.BlockNumber for x in env.BuddyDirEnt if x.Name == "DSDB"))]), BTreeMetadata),

        # Freelist
        Array(32, FreeList)
        # TODO: add an Array of Pointers to other BuddyBlocks based on NumBlocks and the BlockAddresses?
        )

# From http://search.cpan.org/~wiml/Mac-Finder-DSStore/DSStoreFormat.pod :
# "The entries in the block address table are what I call block addresses. Each
# address is a packed offset+size. The least-significant 5 bits of the number
# indicate the block's size, as a power of 2 (from 2^5 to 2^31). If those bits
# are masked off, the result is the starting offset of the block (keeping in
# mind the 4-byte fudge factor). Since the lower 5 bits are unusable to store
# an offset, blocks must be allocated on 32-byte boundaries, and as a side
# effect the minimum block size is 32 bytes (in which case the least
# significant 5 bits are equal to 0x05)."
def sizeFromAddress(i):
    return 2 ** (i & 0x1f)

def offsetFromAddress(i):
    return i & 0xffffffe0

DSStoreFile = Struct("DSStoreFile",
        UBInt32("FixedHeader"), # 0x00000001
        Anchor("ArenaOffset"),
        BuddyAllocatorHeader,
        Pointer(lambda env:env.BuddyAllocatorHeader.InfoBlockOffset + env.ArenaOffset, BuddyAllocatorMetadata)
        )

