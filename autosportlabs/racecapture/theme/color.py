from utils import get_color_from_hex

class ColorScheme(object):
    
    @staticmethod
    def get_alert():
        return get_color_from_hex("FFCC00")

    @staticmethod
    def get_primary():
        return get_color_from_hex("F44336")

    @staticmethod
    def get_dark_primary():
        return get_color_from_hex("D32F2F")
        
    @staticmethod
    def get_light_primary():
        return get_color_from_hex("FFCDD2")

    @staticmethod
    def get_accent():
        return get_color_from_hex("00BCD4")
    
    @staticmethod
    def get_dark_primary_text():
        return get_color_from_hex("212121")
    
    @staticmethod
    def get_light_primary_text():
        return get_color_from_hex("FFFFFF")
    
    @staticmethod
    def get_secondary_text():
        return get_color_from_hex("727272")
    
    @staticmethod
    def get_divider():
        return get_color_from_hex("B6B6B6")
    
    @staticmethod
    def get_dark_background():
        return get_color_from_hex("202020")
    
    @staticmethod
    def get_background():
        return get_color_from_hex("000000")

    
        
        
