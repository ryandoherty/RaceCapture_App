import math
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.resources import resource_find
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import *
from kivy.graphics import *
from autosportlabs.uix.opengl.objloader import ObjFileLoader
from kivy.properties import ReferenceListProperty, NumericProperty
from kivy.logger import Logger
from kivy.vector import Vector
from kivy.core.image import Image

class ImuView(Widget):
    accel_x = NumericProperty(0)
    accel_y = NumericProperty(0)
    accel_z = NumericProperty(0)
    accel = ReferenceListProperty(accel_x, accel_y, accel_z)
    
    gyro_yaw = NumericProperty(0)
    gyro_pitch = NumericProperty(0)
    gyro_roll = NumericProperty(0)
    gyro = ReferenceListProperty(gyro_yaw, gyro_pitch, gyro_roll)
    
    def __init__(self, **kwargs):
        self.canvas = RenderContext(compute_normal_mat=True)
        #self.scene = ObjFileLoader(resource_find("resource/models/car-kart-white.obj"))
        self.scene = ObjFileLoader(resource_find("resource/models/car-formula-white.obj"))
        #self.scene = ObjFileLoader(resource_find("resource/models/car-parsche-sport-white.obj"))
#TODO: the following needs work
        #self.scene = ObjFileLoader(resource_find("resource/models/car-groupc-2-white.obj"))
        #self.scene = ObjFileLoader(resource_find("resource/models/car-groupc-1-white.obj"))

        self.canvas.shader.source = resource_find('resource/models/shaders.glsl')
        super(ImuView, self).__init__(**kwargs)
        with self.canvas:
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()
            self.setup_scene()
            PopMatrix()
            self.cb = Callback(self.reset_gl_context)
        self.camera_translate = [0, 0, -2.5]
        self.camera_ax = 0
        self.camera_ay = 0
        Clock.schedule_once(self.update_glsl, .5 )    
        self._touches = []
        

    def setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def update_glsl(self, *largs):
        asp = self.width / float(self.height)
        asp = asp*0.3
        asp = 0.8
        proj = Matrix()
        mat = Matrix()
        mat = mat.look_at(0.0, 0.6, self.camera_translate[2], 0, 0, 0, 0, 1, 0)
        proj = proj.view_clip(-asp, asp, -0.6, .6, 1, 100, 1)
        
        self.canvas['projection_mat'] = proj
        self.canvas['modelview_mat'] = mat

    def setup_scene(self):
        PushMatrix()
        Translate(0, 0, 0)
        self.rotx = Rotate(0, 0, 1, 0)
        self.roty = Rotate(0, 1, 0, 0)
        self.rotz = Rotate(0, 0, 0, 1)
        
        #self.scale = Scale(0.75)
        m = self.scene.objects.values()[0]
        UpdateNormalMatrix()
        print('diffuse color ' + str(m.diffuse_color))
        print('specular color ' + str(m.specular_color))
        print('ambient color ' + str(m.ambient_color))
        ChangeState(Kd=m.diffuse_color,
                        Ka=m.ambient_color,
                        Ks=m.specular_color,
                        Tr=m.transparency,
                        Ns=1.,
                        intensity=1.)
        self.mesh = Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt=m.vertex_format,
            mode='triangles'
        )
        PopMatrix()
        
    def define_rotate_angle(self, touch):
        x_angle = (touch.dx/self.width)*360
        y_angle = -1*(touch.dy/self.height)*360
        return x_angle, y_angle
    
    def xon_touch_down(self, touch):
        touch.grab(self)
        self._touches.append(touch)
        
    def xon_touch_up(self, touch):
        touch.ungrab(self)
        self._touches.remove(touch)
    
    def xon_touch_move(self, touch): 
        Logger.debug("dx: %s, dy: %s. Widget: (%s, %s)" % (touch.dx, touch.dy, self.width, self.height))
        #self.update_glsl()
        if touch in self._touches and touch.grab_current == self:
            if len(self._touches) == 1:
                # here do just rotation        
                ax, ay = self.define_rotate_angle(touch)
                
                self.rotx.angle += ax
                self.roty.angle += ay
                
                #ax, ay = math.radians(ax), math.radians(ay)
                

            elif len(self._touches) == 2: # scaling here
                #use two touches to determine do we need scal
                touch1, touch2 = self._touches 
                old_pos1 = (touch1.x - touch1.dx, touch1.y - touch1.dy)
                old_pos2 = (touch2.x - touch2.dx, touch2.y - touch2.dy)
                
                old_dx = old_pos1[0] - old_pos2[0]
                old_dy = old_pos1[1] - old_pos2[1]
                
                old_distance = (old_dx*old_dx + old_dy*old_dy)
                Logger.debug('Old distance: %s' % old_distance)
                
                new_dx = touch1.x - touch2.x
                new_dy = touch1.y - touch2.y
                
                new_distance = (new_dx*new_dx + new_dy*new_dy)
                
                Logger.debug('New distance: %s' % new_distance)
                SCALE_FACTOR = 0.05
                
                if new_distance > old_distance: 
                    scale = -1*SCALE_FACTOR
                    Logger.info('Scale up')
                elif new_distance == old_distance:
                    scale = 0
                else:
                    scale = SCALE_FACTOR
                    Logger.info('Scale down')
                
                if scale:
                    self.camera_translate[2] += scale
            self.update_glsl()

    def on_accel_x(self, instance, value):
        pass
    
    def on_accel_y(self, instance, value):
        pass
    
    def on_accel_z(self, instance, value):
        pass
    
    def on_gyro_yaw(self, instance, value):
        self.rotx.angle = value        
    
    def on_gyro_pitch(self, instance, value):
        self.roty.angle = -value
    
    def on_gyro_roll(self, instance, value):
        self.rotz.angle = value
    
