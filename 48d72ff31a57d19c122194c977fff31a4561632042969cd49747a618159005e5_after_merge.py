    def _open(self):

        # The Sun Raster file header is 32 bytes in length and has the following format:

        #     typedef struct _SunRaster
        #     {
        #         DWORD MagicNumber;      /* Magic (identification) number */
        #         DWORD Width;            /* Width of image in pixels */
        #         DWORD Height;           /* Height of image in pixels */
        #         DWORD Depth;            /* Number of bits per pixel */
        #         DWORD Length;           /* Size of image data in bytes */
        #         DWORD Type;             /* Type of raster file */
        #         DWORD ColorMapType;     /* Type of color map */
        #         DWORD ColorMapLength;   /* Size of the color map in bytes */
        #     } SUNRASTER;


        # HEAD
        s = self.fp.read(32)
        if i32(s) != 0x59a66a95:
            raise SyntaxError("not an SUN raster file")

        offset = 32

        self.size = i32(s[4:8]), i32(s[8:12])

        depth = i32(s[12:16])
        data_length = i32(s[16:20])  # unreliable, ignore. 
        file_type = i32(s[20:24])
        palette_type = i32(s[24:28]) # 0: None, 1: RGB, 2: Raw/arbitrary
        palette_length = i32(s[28:32])
        
        if depth == 1:
            self.mode, rawmode = "1", "1;I"
        elif depth == 4:
            self.mode, rawmode = "L", "L;4"
        elif depth == 8:
            self.mode = rawmode = "L"
        elif depth == 24:
            if file_type == 3:
                self.mode, rawmode = "RGB", "RGB"
            else:
                self.mode, rawmode = "RGB", "BGR"
        elif depth == 32:
            if file_type == 3:
                self.mode, rawmode = 'RGB', 'RGBX'
            else:
                self.mode, rawmode = 'RGB', 'BGRX'
        else:
            raise SyntaxError("Unsupported Mode/Bit Depth")    
        
        if palette_length:
            if palette_length > 1024:
                raise SyntaxError("Unsupported Color Palette Length")

            if palette_type != 1:
                raise SyntaxError("Unsupported Palette Type")
            
            offset = offset + palette_length
            self.palette = ImagePalette.raw("RGB;L", self.fp.read(palette_length))
            if self.mode == "L":
                self.mode = "P"
                rawmode = rawmode.replace('L', 'P')
            
        # 16 bit boundaries on stride
        stride = ((self.size[0] * depth + 15) // 16) * 2  

        # file type: Type is the version (or flavor) of the bitmap
        # file. The following values are typically found in the Type
        # field:
        # 0000h	Old
        # 0001h	Standard
        # 0002h	Byte-encoded
        # 0003h	RGB format
        # 0004h	TIFF format
        # 0005h	IFF format
        # FFFFh	Experimental

        # Old and standard are the same, except for the length tag.
        # byte-encoded is run-length-encoded
        # RGB looks similar to standard, but RGB byte order
        # TIFF and IFF mean that they were converted from T/IFF
        # Experimental means that it's something else.
        # (http://www.fileformat.info/format/sunraster/egff.htm)

        if file_type in (0, 1, 3, 4, 5):
            self.tile = [("raw", (0, 0)+self.size, offset, (rawmode, stride))]
        elif file_type == 2:
            self.tile = [("sun_rle", (0, 0)+self.size, offset, rawmode)]
        else:
            raise SyntaxError('Unsupported Sun Raster file type')