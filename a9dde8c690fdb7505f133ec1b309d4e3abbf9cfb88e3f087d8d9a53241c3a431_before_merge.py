def population_count(x):
  dtype = x.dtype
  if x.dtype in (np.uint8, np.uint16):
    x = x.astype(np.uint32)
  assert x.dtype in (np.uint32, np.uint64)
  m = [
      0x5555555555555555,  # binary: 0101...
      0x3333333333333333,  # binary: 00110011..
      0x0f0f0f0f0f0f0f0f,  # binary:  4 zeros,  4 ones ...
      0x00ff00ff00ff00ff,  # binary:  8 zeros,  8 ones ...
      0x0000ffff0000ffff,  # binary: 16 zeros, 16 ones ...
      0x00000000ffffffff,  # binary: 32 zeros, 32 ones
  ]

  if x.dtype == np.uint32:
    m = list(map(np.uint32, m[:-1]))
  else:
    m = list(map(np.uint64, m))

  x = (x & m[0]) + ((x >>  1) & m[0])  # put count of each  2 bits into those  2 bits
  x = (x & m[1]) + ((x >>  2) & m[1])  # put count of each  4 bits into those  4 bits
  x = (x & m[2]) + ((x >>  4) & m[2])  # put count of each  8 bits into those  8 bits
  x = (x & m[3]) + ((x >>  8) & m[3])  # put count of each 16 bits into those 16 bits
  x = (x & m[4]) + ((x >> 16) & m[4])  # put count of each 32 bits into those 32 bits
  if x.dtype == np.uint64:
    x = (x & m[5]) + ((x >> 32) & m[5])  # put count of each 64 bits into those 64 bits
  return x.astype(dtype)