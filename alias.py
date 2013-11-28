#!/usr/bin/env python
from construct import Enum, UBInt16, Bytes, Struct, RepeatUntil, UBInt32, UBInt8, Anchor

# This file contains some structures relating to Alias records.
# http://en.wikipedia.org/wiki/Alias_(Mac_OS)#File_structure

AliasType = Enum(UBInt16("AliasType"),
        DIRECTORY_NAME = 0,
        DIRECTORY_IDS = 1,
        ABSOLUTE_PATH = 2,
        APPLESHARE_ZONE_NAME = 3,
        APPLESHARE_SERVER_NAME = 4,
        APPLESHARE_USER_NAME = 5,
        DRIVER_NAME = 6,
        REVISED_APPLESHARE_INFO = 9,
        APPLEREMOTEACCESS_DIALUP_INFO = 10,
        UNK0 = 14,
        UNK1 = 15,
        UNK2 = 16,
        UNK3 = 17,
        UNK4 = 18,
        UNK5 = 19,
        UNK6 = 20,
        END_OF_LIST = 0xffff,
        )

AliasKind = Enum(UBInt16("AliasKind"),
        FILE = 0,
        DIRECTORY = 1,
        )

VolumeType = Enum(UBInt16("VolumeType"),
        FIXED_HD = 0,
        NETWORK_DISK = 1,
        FLOPPY_400K = 2,
        FLOPPY_800K = 3,
        FLOPPY_1_4M = 4,
        OTHER_EJECTABLE_MEDIA = 5,
        )

def roundUpToNearest2(x):
    return x if x % 2 == 0 else x + 1

AliasBlob = Struct("AliasBlob",
        AliasType,
        UBInt16("AliasLength"),
        Bytes("AliasData", lambda env: roundUpToNearest2(env.AliasLength))
        )


def PaddedString(name, total_length):
    return Struct(name,
        UBInt8("Length"),
        Bytes("Name", lambda env: env.Length),
        Bytes("Padding", lambda env: total_length - 1 - env.Length),
        )

AliasRecord = Struct("AliasRecord",
        UBInt32("UserType"),        # 0 for Alias Manager
        UBInt16("AliasSize"),       # The size of the alias record
        UBInt16("RecordVersion"),   # Version of the alias record, currently 2
        AliasKind,                  # file = 0, directory = 1
        PaddedString("VolumeName", 28), # Volume name
        UBInt32("VolumeMacDate"),   # unsigned, seconds since epoch 1904
        UBInt16("VolumeSignature"), # HFS value
        VolumeType,                 # Fixed HD = 0, Network Disk = 1, 400k floppy = 2, 800k floppy = 3, 1.4M floppy = 4, Other Ejectable Media = 5
        UBInt32("ParentDirID"),     # ???
        PaddedString("FileName", 64), # Filename
        UBInt32("FileNumber"),      # ???
        UBInt32("FileMacDate"),     # unsigned, seconds since epoch 1904
        Bytes("FileType", 4),       # file type name?
        Bytes("FileCreator", 4),    # file creator name?
        UBInt16("nlvlFrom"),        # directories from alias through to root (-1 if alias on different volume?)
        UBInt16("nlvlTo"),          # directories from root through to source
        UBInt32("VolumeFlags"),     # hex flags
        UBInt16("VolumeFSID"),      # volume filesystem id
        Bytes("Reserved", 10),      # zeros
#        Array(11, AliasBlob),
        RepeatUntil(lambda obj, env: obj.AliasType == "END_OF_LIST", AliasBlob),
        Anchor("DataBegin"),
        Bytes("AliasData", lambda env: env.AliasSize - env.DataBegin) # The alias record data
        )

