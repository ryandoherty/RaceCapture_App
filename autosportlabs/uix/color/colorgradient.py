import math

class HeatColorGradient:
    '''
    Calculate a heat gradient color based on the specified percentage
    
    :param value the value for the gradient, between 0.0 - 1.0
    :type value float
    '''
    
    def get_color_value(self, value):
        colors = [[0,0,1,1], [0,1,0,1], [1,1,0,1], [1,0,0,1]]
        num_colors = len(colors)

        idx1 = 0
        idx2 = 0
        frac_between = 0.0

        if value <= 0:
            idx1 = idx2 = 0
        elif value >= 1:
            idx1 = idx2 = num_colors - 1
        else:
            value = value * (num_colors - 1)
            idx1  = int(math.floor(value))
            idx2  = idx1 + 1
            frac_between = value - float(idx1)

        red   = (colors[idx2][0] - colors[idx1][0]) * frac_between + colors[idx1][0];
        green = (colors[idx2][1] - colors[idx1][1]) * frac_between + colors[idx1][1];
        blue  = (colors[idx2][2] - colors[idx1][2]) * frac_between + colors[idx1][2];
        
        return [red, green, blue, 1.0]
    
class SimpleColorGradient():
    '''
    Generates a simple 2-color gradient
    '''
    
    def __init__(self):
        self.min_color = [0.0, 0.0, 0.0, 0.0]
        self.max_color = [0.0, 0.0, 0.0, 0.0]
    
    def get_color_value(self, value):
        '''
        Calculate a gradient color based on the specified percentage
        
        :param value the value for the gradient, between 0.0 - 1.0
        :type value float
        '''
        min_color = self.min_color
        max_color = self.max_color
        red = min_color[0] + (max_color[0] - min_color[0]) * value
        green = min_color[1] + (max_color[1] - min_color[1]) * value
        blue = min_color[2] + (max_color[2] - min_color[2]) * value
        return [red, green, blue, 1.0]
        
        