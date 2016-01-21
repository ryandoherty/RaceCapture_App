class HeatColorGradient:
    '''
    Generates heat color tuples
    '''
    
    def get_color_value(self, percent):
        pass
    
class SimpleColorGradient():
    '''
    Generates a simple 2-color gradient
    '''
    
    def __init__(self):
        self.min_color = [0.0, 0.0, 0.0, 0.0]
        self.max_color = [0.0, 0.0, 0.0, 0.0]
    
    def get_color_value(self, percent):
        '''
        Calculate a gradient color based on the specified percentage
        
        :param percent the value for the gradient, between 0.0 - 1.0
        :type percent float
        '''
        min_color = self.min_color
        max_color = self.max_color
        red = min_color[0] + (max_color[0] - min_color[0]) * percent
        green = min_color[1] + (max_color[1] - min_color[1]) * percent
        blue = min_color[2] + (max_color[2] - min_color[2]) * percent
        return [red, green, blue, 1.0]
        
        