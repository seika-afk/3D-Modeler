from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy   # Use np instead of numpy in the code
from OpenGL.arrays import GLfloat_3  # For GLfloat_3

#creating the window viewing capability
class Viewer(object):
    def __init__(self):
        #initializing the viewer 
        self.init_interface()
        self.init_opengl()
        self.init_scene()
        self.init_interaction()
        init_primitives()
    def init_interface(self):
        glutInit()
        glutInitWindowSize(640,480)
        glutCreateWindow("3D Modeler")
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
        glutDisplayFunc(self.render)
    def init_opengl(self):
        self.inverseModelView = numpy.identity(4)
        self.modelView = numpy.identity(4)
        #dont show back dude
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        #depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS) #tells opengl to draw pixels near to camera

        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 1, 0])
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, GLfloat_3(0, 0, -1))

        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glClearColor(0.4,0.4,0.4,0.0)

    def init_scene(self):
        self.scene=Scene()
        self.create_sample_scene()
#continue
    def create_sample_scene(self):
        cube_node = Cube()
        cube_node.translate(2, 0, 2)
        cube_node.color_index = 2
        self.scene.add_node(cube_node)

        sphere_node = Sphere()
        sphere_node.translate(-2, 0, 2)
        sphere_node.color_index = 3
        self.scene.add_node(sphere_node)

        hierarchical_node = SnowFigure()
        hierarchical_node.translate(-2, 0, -2)
        self.scene.add_node(hierarchical_node)


    def init_interaction(self):
        self.interaction = Interaction()
        self.interaction.register_callback('pick',self.pick)
        self.interaction.register_callback('move',self.move)
        self.interaction.register_callback('place',self.place)
        self.interaction.register_callback('scale',self.scale)
        self.interaction.register_callback('rotate_color',self.rotate_color)

    def main_loop(self):
        glutMainLoop()
    def render(self):
        self.init_view()
        glEnable(GL_LIGHTING)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

if __name__=="__main__":
    viewer=Viewer()
    viewer.main_loop()



#rendering with the viewer