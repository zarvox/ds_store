from __future__ import print_function
from construct import *

def NamedChild(name):
    return Struct(name,
        UBInt32("ChildNumber"),
        UBInt32("SomethingElse"),
        )

def InternalNodeData(nodes):
    return Struct("InternalNodeData",
        Array(lambda ctx: nodes - 1, NamedChild("InnerChildren")),
        UBInt32("LastChild")
    )

foo = '\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05'

print (InternalNodeData(3).parse(foo))
