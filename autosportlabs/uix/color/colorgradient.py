import math

class HeatColorGradient(object):
    '''
    Calculate a heat gradient color based on the specified value
    
    :param value the value for the gradient, between 0.0 - 1.0
    :type value float
    '''
    
    def __init__(self):
        self.alpha = 1.0
    
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
        
        return [red, green, blue, self.alpha]
    
class SimpleColorGradient(object):
    '''
    Generates a simple 2-color gradient
    '''
    
    def __init__(self, **kwargs):
        self.alpha = 1.0
        max_color = kwargs.get('max_color', [1.0, 1.0, 1.0])
        min_color = kwargs.get('min_color', None)
        alpha = kwargs.get('alpha', 1.0)
        self.set_colors(max_color, min_color, alpha = alpha)
    
    def set_colors(self, max_color, min_color = None, **kwargs):
        '''
        Sets the min/max gradient values 
        Color for max value is set from the supplied color; min color is set as the inverse of the max if not specified
        :param max_color the color to set for the max color value
        :type max_color list rgb color values 
        :param min_color the color to set for the min color value
        :type min_color list rgb color values
        :param alpha kwarg specifying alpha transparency
        :param alpha float
        '''
        self.max_color = max_color[:]
        if min_color:
            self.min_color = min_color[:]
        else:
            self.min_color=[1.0 - max_color[0], 1.0 - max_color[1], 1.0 - max_color[2]]

        self.alpha = kwargs.get('alpha', self.alpha)

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
        return [red, green, blue, self.alpha]
        
        