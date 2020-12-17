#!/usr/bin/env python3

# .dsk (819200 bytes) to .mac (1638400 bytes) decoder

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

dsksector=bytearray(524)
macsector=bytearray(2048)
csum=bytearray(4)

# nibblize35 tmp store
nib1=bytearray(175)
nib2=bytearray(175)
nib3=bytearray(175)

def mess_sony_nibblize35(dataIn_ba, nib_ptr_ba, csum_ba):
  dataIn=memoryview(dataIn_ba)
  nib_ptr=memoryview(nib_ptr_ba)
  csum=memoryview(csum_ba)
  b1=memoryview(nib1)
  b2=memoryview(nib2)
  b3=memoryview(nib3)
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
  j=0
  for i in range(0,175):
    w1=b1[i]&0x3F
    w2=b2[i]&0x3F
    w3=b3[i]&0x3F
    w4 =(b1[i]&0xC0)>>2
    w4|=(b2[i]&0xC0)>>4
    w4|=(b3[i]&0xC0)>>6
    nib_ptr[j]=w4
    j+=1
    nib_ptr[j]=w1
    j+=1
    nib_ptr[j]=w2
    j+=1
    if i!=174:
      nib_ptr[j]=w3
      j+=1
  # reverse to file write order
  csum[3]=c1&0x3F
  csum[2]=c2&0x3F
  csum[1]=c3&0x3F
  csum[0]=c4&0x3F

conv_dataIn=bytearray(524)
conv_nibOut=bytearray(699)
conv_dataChecksum=bytearray(4)
def convert_dsk2mac(src,dst):
  rfs=open(src,"rb")
  wfs=open(dst,"wb")

  dataIn=memoryview(conv_dataIn)
  nibOut=memoryview(conv_nibOut)
  dataChecksum=memoryview(conv_dataChecksum)

  #rfs.readinto(dsksector)
  format=0x22 # 0x22 = MacOS double-sided, 0x02 = single sided
  rfs.seek(0,2) # end of file
  rfs_Length=rfs.tell()
  rfs.seek(0) # rewind to start of file
  numSides=rfs_Length//409600
  side=0
  track=0
  sectorInTrack=0
  offset=0
  while offset<rfs_Length:
    for i in range(14*4): # TODO micropython optimize
      wfs.write(bytearray([0xFF]))
    trackLow=track&0x3F
    trackHigh=(side<<5)|(track>>6)
    checksum=(trackLow^sectorInTrack^trackHigh^format)&0x3F
    wfs.write(bytearray([
      0xd5,0xaa,0x96,
      sony_to_disk_byte[trackLow],
      sony_to_disk_byte[sectorInTrack],
      sony_to_disk_byte[trackHigh],
      sony_to_disk_byte[format],
      sony_to_disk_byte[checksum],
      0xde,0xaa]))
    # More syncs
    wfs.write(bytearray([0xff,0xff,0xff,0xff,0xff]))
    # Data block
    wfs.write(bytearray([0xd5,0xaa,0xad,sony_to_disk_byte[sectorInTrack]]))
    nibCount=699
    # get the tags and sector data
    for i in range(12):
      dataIn[i]=0
    rfs.readinto(dataIn[12:524]) # FIXME micropython incompatible
    # convert the sector data
    mess_sony_nibblize35(dataIn, nibOut, dataChecksum)
    # in-place sony_to_disk_byte
    for i in range(nibCount):
      nibOut[i]=sony_to_disk_byte[nibOut[i]]
    for i in range(4):
      dataChecksum[i]=sony_to_disk_byte[dataChecksum[i]]
    # write the sector data and the checksum
    wfs.write(nibOut)
    wfs.write(dataChecksum)
    # data block trailer
    wfs.write(bytearray([0xde,0xaa,0xff]))
    # padding to make a power of 2 size for encoded sectors
    for i in range(243): # TODO micropython optimize
      wfs.write(bytearray([0xFF]))
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

convert_dsk2mac("Disk605.dsk","Disk605.mac") # 800K
#convert_dsk2mac("Space_Invaders.dsk","Space_Invaders.mac") # 400K
