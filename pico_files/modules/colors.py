
#  Codes per GS4_HMSB
class GS4:
    BLACK      =  0
    GRAY       =  8
    RED        =  9
    GREEN      = 10
    YELLOW     = 11
    BLUE       = 12
    PURPLE     = 13
    CYAN       = 14
    LIGHT_GRAY = 15

class RGB_565:

    BLACK = 0x0
    BLUE  = 0x001f
    GREEN = 0x07e0
    RED   = 0xf800
    WHITE = 0xffff

    @staticmethod
    def from_rgb( r, g, b ):
        # Ensure the RGB values are within the 0-255 range
        r = int( max(0, min(255, r)) / 255.0 * 31.0 )
        g = int( max(0, min(255, g)) / 255.0 * 63.0 )
        b = int( max(0, min(255, b)) / 255.0 * 31.0 )
    
        # Convert to RGB565
        rgb565 = (r << 11) | (g << 5) | b
        return rgb565
    