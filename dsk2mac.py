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
  csum[0]=c1&0x3F
  csum[1]=c2&0x3F
  csum[2]=c3&0x3F
  csum[3]=c4&0x3F

def convert_dsk2mac():
  rfs=open("Disk605.dsk","rb")
  wfs=open("Disk605.mac","wb")
  #rfs.readinto(dsksector)
  format=0x22 # 0x22 = MacOS double-sided, 0x02 = single sided
  rfs_Length=819200 # TODO from file
  numSides=rfs_Length//409600
  side=0
  track=0
  sectorInTrack=0
  offset=0
  

mess_sony_nibblize35(dsksector,macsector,csum)
# print(dsksector,macsector,csum)
print(csum)

