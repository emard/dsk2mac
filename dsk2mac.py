#!/usr/bin/env python3
# .dsk (409600/819200 bytes) to .mac (819200/1638400 bytes) converter

# AUTHOR=EMARD
# LICENSE=BSD

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
# dataIn_ba: 512 bytes, dataOut_ba: 703 bytes
def sony_nibblize35(dataIn_ba,roffset:int,dataOut_ba,woffset:int):
  dataIn=memoryview(dataIn_ba)
  nib_ptr=memoryview(dataOut_ba)
  b1=memoryview(nib1)
  b2=memoryview(nib2)
  b3=memoryview(nib3)
  # Copy from the user's buffer to our buffer, while computing
  # the three-byte data checksum
  i=-12 # prepend 12 bytes of 0
  j=0
  c1=0
  c2=0
  c3=0
  while(True):
    # ROL.B
    c1=(c1&0xFF)<<1
    if (c1&0x0100)!=0:
      c1+=1
    val=0
    if i>=0:
      val=dataIn[i+roffset]
      c3+=val
    i+=1
    # ADDX?
    if (c1&0x0100)!=0:
      c3+=1
      c1&=0xFF
    b1[j]=val^c1
    val=0
    if i>=0:
      val=dataIn[i+roffset]
      c2+=val
    i+=1
    if c3>0xFF:
      c2+=1
      c3&=0xFF
    b2[j]=val^c3
    if i>=512:
      break
    val=0
    if i>=0:
      val=dataIn[i+roffset]
      c1+=val
    i+=1
    if c2>0xFF:
      c1+=1
      c2&=0xFF
    b3[j]=val^c2
    j+=1
  c4=((c1&0xC0)>>6)|((c2&0xC0)>>4)|((c3&0xC0)>>2)
  b3[174]=0
  j=woffset # offset writing to dataOut
  for i in range(0,175):
    w1=b1[i]&0x3F
    w2=b2[i]&0x3F
    w3=b3[i]&0x3F
    w4 =(b1[i]&0xC0)>>2
    w4|=(b2[i]&0xC0)>>4
    w4|=(b3[i]&0xC0)>>6
    nib_ptr[j]=sony_to_disk_byte[w4]
    j+=1
    nib_ptr[j]=sony_to_disk_byte[w1]
    j+=1
    nib_ptr[j]=sony_to_disk_byte[w2]
    j+=1
    if i!=174:
      nib_ptr[j]=sony_to_disk_byte[w3]
      j+=1
  # checksum at j=offset+699
  nib_ptr[j]=sony_to_disk_byte[c4&0x3F]
  j+=1
  nib_ptr[j]=sony_to_disk_byte[c3&0x3F]
  j+=1
  nib_ptr[j]=sony_to_disk_byte[c2&0x3F]
  j+=1
  nib_ptr[j]=sony_to_disk_byte[c1&0x3F]

conv_nibsOut=bytearray(1024)
def init_nibsOut():
  p8n=memoryview(conv_nibsOut)
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

# dsk=bytearray(512)
# nib=bytearray(1024)
# track=0-79, side=0-1, sector=0-11
def convert_sector(dsk,nib,track:int,side:int,sector:int):
  nibsOut=memoryview(nib)
  s2d=memoryview(sony_to_disk_byte)
  format=0x22 # 0x22 = MacOS double-sided, 0x02 = single sided
  trackLow=track&0x3F
  trackHigh=(side<<5)|(track>>6)
  checksum=(trackLow^sector^trackHigh^format)&0x3F
  nibsOut[59]=s2d[trackLow]
  nibsOut[60]=s2d[sector]
  nibsOut[61]=s2d[trackHigh]
  nibsOut[62]=s2d[format]
  nibsOut[63]=s2d[checksum]
  # data block
  nibsOut[74]=s2d[sector]    
  # convert the sector data
  sony_nibblize35(dsk,0,nib,75)

conv_dataIn=bytearray(512)
def convert_dsk2mac(rfs,wfs):
  rfs.seek(0,2) # end of file
  rfs_Length=int(rfs.tell())
  rfs.seek(0) # rewind to start of file
  numSides=rfs_Length//409600
  for track in range(80):
    for side in range(numSides):
      for sector in range(12-track//16):
        rfs.readinto(conv_dataIn)
        convert_sector(conv_dataIn,conv_nibsOut,track,side,sector)
        wfs.write(conv_nibsOut)

rfs=open("Disk605.dsk","rb")
wfs=open("Disk605b.mac","wb")
#rfs=open("Space_Invaders.dsk","rb")
#wfs=open("Space_Invaders.mac","wb")
convert_dsk2mac(rfs,wfs)
wfs.close()
rfs.close()
