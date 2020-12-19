#!/usr/bin/env python3
# .dsk (409600/819200 bytes) to .mac (819200/1638400 bytes) converter

# AUTHOR=EMARD
# LICENSE=BSD

from uctypes import addressof
import dsk2mac

conv_dataIn=bytearray(512)
conv_nibsOut=bytearray(1024)
@micropython.viper
def convert_dsk2mac(rfs,wfs):
  dsk2mac.init_nibsOut(conv_nibsOut)
  rfs.seek(0,2) # end of file
  rfs_Length=int(rfs.tell())
  rfs.seek(0) # rewind to start of file
  numSides=rfs_Length//409600
  for track in range(80):
    for side in range(numSides):
      for sector in range(12-track//16):
        rfs.readinto(conv_dataIn)
        dsk2mac.convert_sector(conv_dataIn,0,conv_nibsOut,track,side,sector)
        wfs.write(conv_nibsOut)

rfs=open("/sd/mac/disks/Disk605.dsk","rb")
wfs=open("/sd/mac/disks/Disk605b.mac","wb")
convert_dsk2mac(rfs,wfs)
wfs.close()
rfs.close()
