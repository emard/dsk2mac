#!/usr/bin/env python3
# .dsk (409600/819200 bytes) to .mac (819200/1638400 bytes) converter

# AUTHOR=EMARD
# LICENSE=BSD

#from micropython import const, alloc_emergency_exception_buf
from uctypes import addressof

sony_to_disk_byte = bytearray([
    0x96, 0x97, 0x9A, 0x9B,  0x9D, 0x9E, 0x9F, 0xA6, # 0x00
    0xA7, 0xAB, 0xAC, 0xAD,  0xAE, 0xAF, 0xB2, 0xB3,
    0xB4, 0xB5, 0xB6, 0xB7,  0xB9, 0xBA, 0xBB, 0xBC, # 0x10
    0xBD, 0xBE, 0xBF, 0xCB,  0xCD, 0xCE, 0xCF, 0xD3,
    0xD6, 0xD7, 0xD9, 0xDA,  0xDB, 0xDC, 0xDD, 0xDE, # 0x20
    0xDF, 0xE5, 0xE6, 0xE7,  0xE9, 0xEA, 0xEB, 0xEC,
    0xED, 0xEE, 0xEF, 0xF2,  0xF3, 0xF4, 0xF5, 0xF6, # 0x30
    0xF7, 0xF9, 0xFA, 0xFB,  0xFC, 0xFD, 0xFE, 0xFF
])

# nibblize35 tmp store
nib1=bytearray(175)
nib2=bytearray(175)
nib3=bytearray(175)

@micropython.viper
def sony_nibblize35(dataIn_ba,nib_ptr_ba,offset:int):
  dataIn=ptr8(addressof(dataIn_ba))
  nib_ptr=ptr8(addressof(nib_ptr_ba))
  s2d=ptr8(addressof(sony_to_disk_byte))
  b1=ptr8(addressof(nib1))
  b2=ptr8(addressof(nib2))
  b3=ptr8(addressof(nib3))
  # Copy from the user's buffer to our buffer, while computing
  # the three-byte data checksum
  i=0
  j=0
  c1=0
  c2=0
  c3=0
  while(True):
    # ROL.B
    c1=(c1&0xFF)<<1
    if (c1&0x0100)!=0:
      c1+=1
    val=dataIn[i]
    i+=1
    # ADDX?
    c3+=val
    if (c1&0x0100)!=0:
      c3+=1
      c1&=0xFF
    b1[j]=val^c1
    val=dataIn[i]
    i+=1
    c2+=val
    if c3>0xFF:
      c2+=1
      c3&=0xFF
    b2[j]=val^c3
    if i==524:
      break
    val=dataIn[i]
    i+=1
    c1+=val
    if c2>0xFF:
      c1+=1
      c2&=0xFF
    b3[j]=val^c2
    j+=1
  c4=((c1&0xC0)>>6)|((c2&0xC0)>>4)|((c3&0xC0)>>2)
  b3[174]=0
  j=offset # offset writing to dataOut
  for i in range(0,175):
    w1=b1[i]&0x3F
    w2=b2[i]&0x3F
    w3=b3[i]&0x3F
    w4 =(b1[i]&0xC0)>>2
    w4|=(b2[i]&0xC0)>>4
    w4|=(b3[i]&0xC0)>>6
    nib_ptr[j]=s2d[w4]
    j+=1
    nib_ptr[j]=s2d[w1]
    j+=1
    nib_ptr[j]=s2d[w2]
    j+=1
    if i!=174:
      nib_ptr[j]=s2d[w3]
      j+=1
  # checksum at j=offset+699
  nib_ptr[j]=s2d[c4&0x3F]
  j+=1
  nib_ptr[j]=s2d[c3&0x3F]
  j+=1
  nib_ptr[j]=s2d[c2&0x3F]
  j+=1
  nib_ptr[j]=s2d[c1&0x3F]

conv_dataIn=bytearray(524)
conv_nibsOut=bytearray(1024)
@micropython.viper
def init_nibsOut():
  p8n=ptr8(addressof(conv_nibsOut))
  # 56+19+703+3+243=1024
  for i in range(1024):
    p8n[i]=0xFF
  # 0-55: 56*0xFF sync
  p8n[56]=0xD5
  p8n[57]=0xAA
  p8n[58]=0x96
  # 59-63: track/sector/format/checksum
  p8n[64]=0xDE
  p8n[65]=0xAA
  # 66-70: 0xFF sync
  p8n[71]=0xD5
  p8n[72]=0xAA
  p8n[73]=0xAD
  # 74: sector in track
  # 75-777: nibblized sector
  # 778-780: data block trailer
  p8n[778]=0xDE
  p8n[779]=0xAA
  #p8n[780]=0xFF   
  # 781-1024: 243*0xFF padding sync
init_nibsOut()

#@micropython.viper
def convert_dsk2mac(rfs,wfs):
  # tmp storage
  dataIn=memoryview(conv_dataIn)
  nibsOut=memoryview(conv_nibsOut)

  format=0x22 # 0x22 = MacOS double-sided, 0x02 = single sided
  rfs.seek(0,2) # end of file
  rfs_Length=int(rfs.tell())
  rfs.seek(0) # rewind to start of file
  numSides=rfs_Length//409600
  side=0
  track=0
  sectorInTrack=0
  offset=0
  while offset<rfs_Length:
    trackLow=track&0x3F
    trackHigh=(side<<5)|(track>>6)
    checksum=(trackLow^sectorInTrack^trackHigh^format)&0x3F
    nibsOut[59]=sony_to_disk_byte[trackLow]
    nibsOut[60]=sony_to_disk_byte[sectorInTrack]
    nibsOut[61]=sony_to_disk_byte[trackHigh]
    nibsOut[62]=sony_to_disk_byte[format]
    nibsOut[63]=sony_to_disk_byte[checksum]
    # Data block
    nibsOut[74]=sony_to_disk_byte[sectorInTrack]    
    # get the tags and sector data
    for i in range(12):
      dataIn[i]=0
    rfs.readinto(dataIn[12:524]) # FIXME micropython incompatible
    # convert the sector data
    sony_nibblize35(dataIn,nibsOut,75)
    wfs.write(nibsOut)
    # next sector
    offset+=512
    sectorInTrack+=1
    if sectorInTrack==12-track//16:
      sectorInTrack=0
      if numSides==2 and side==0:
        side=1
      else:
        track+=1
        side=0
  wfs.close()
  rfs.close()

rfs=open("/sd/mac/disks/Disk605.dsk","rb")
wfs=open("/sd/mac/disks/Disk605b.mac","wb")
convert_dsk2mac(rfs,wfs)
wfs.close()
rfs.close()

#convert_dsk2mac("Space_Invaders.dsk","Space_Invaders.mac") # 400K
