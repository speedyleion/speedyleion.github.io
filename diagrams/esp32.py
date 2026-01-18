import schemdraw.pictorial as pictorial

class Esp32c6Pictorial(pictorial.FritzingPart):
    """
    Fritzing part for the esp32-c6 from
    https://github.com/Seeed-Studio/fritzing_parts/blob/master/XIAO%20Boards/Seeed%20Studio%20XIAO%20ESP32C6.fzpz
    """
    def __init__(self, **kwargs):
        super().__init__('seeed-studio-xiao-esp32c6.fzpz', **kwargs)
    
    @classmethod
    def bb_offset(cls):
        """
        # The at(x, y) is a hack offset to prevent a bunch of empty space at the
        # left of the image
        """
        # return (-6.27, -2)
        return (0, 0)