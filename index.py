from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
from numpy.linalg import norm, inv
from collections import defaultdict
from OpenGL.arrays import GLfloat_3  # For GLfloat_3

# --- Math helpers ---
def translation(displacement):
    t = np.identity(4)
    t[0, 3], t[1, 3], t[2, 3] = displacement
    return t

def scaling(scale):
    s = np.identity(4)
    s[0, 0], s[1, 1], s[2, 2] = scale
    return s

# --- Viewer & GL setup ---
class Viewer(object):
    def __init__(self):
        self.init_interface()
        self.init_opengl()
        self.init_scene()
        self.init_interaction()
        init_primitives()

    def init_interface(self):
        glutInit()
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(640, 480)
        glutCreateWindow("3D Modeler")
        glutDisplayFunc(self.render)

    def init_opengl(self):
        self.modelView = np.identity(4)
        self.inverseModelView = np.identity(4)

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 1, 0])
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, GLfloat_3(0, 0, -1))

        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glClearColor(0.4, 0.4, 0.4, 0.0)

    def init_scene(self):
        self.scene = Scene()
        self.create_sample_scene()

    def create_sample_scene(self):
        cube_node = Cube()
        cube_node.translate(2, 0, 2)
        cube_node.color_index = 2
        self.scene.add_node(cube_node)

        sphere_node = Sphere()
        sphere_node.translate(-2, 0, 2)
        sphere_node.color_index = 3
        self.scene.add_node(sphere_node)

        snow = SnowFigure()
        snow.translate(-2, 0, -2)
        self.scene.add_node(snow)

    def init_interaction(self):
        self.interaction = Interaction()
        self.interaction.register_callback('pick', self.pick)
        self.interaction.register_callback('move', self.move)
        self.interaction.register_callback('place', self.place)
        self.interaction.register_callback('scale', self.scale)
        self.interaction.register_callback('rotate_color', self.rotate_color)

    def main_loop(self):
        glutMainLoop()

    def init_view(self):
        w, h = glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT)
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        glViewport(0, 0, w, h)
        gluPerspective(70, w/float(h), 0.1, 1000.0)
        glTranslated(0, 0, -15)

    def render(self):
        self.init_view()
        glEnable(GL_LIGHTING)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        loc = self.interaction.translation
        glTranslated(*loc[:3])
        glMultMatrixf(self.interaction.trackball.matrix)

        mv = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
        self.modelView = mv.T
        self.inverseModelView = inv(mv.T)

        self.scene.render()

        glDisable(GL_LIGHTING)
        glCallList(G_OBJ_PLANE)
        glPopMatrix()
        glFlush()

    def get_ray(self, x, y):
        self.init_view()
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()

        start = np.array(gluUnProject(x, y, 0.001))
        end   = np.array(gluUnProject(x, y, 0.999))
        direction = (end - start)
        direction /= norm(direction)
        return start, direction

    def pick(self, x, y):
        s, d = self.get_ray(x, y)
        self.scene.pick(s, d, self.modelView)

    def move(self, x, y):
        s, d = self.get_ray(x, y)
        self.scene.move_selected(s, d, self.inverseModelView)

    def scale(self, up):
        self.scene.scale_selected(up)

    def rotate_color(self, forward):
        self.scene.rotate_selected_color(forward)

    def place(self, shape, x, y):
        s, d = self.get_ray(x, y)
        self.scene.place(shape, s, d, self.inverseModelView)


# --- Scene & Nodes ---
class Scene(object):
    PLACE_DEPTH = 15.0

    def __init__(self):
        self.node_list = []
        self.selected_node = None

    def add_node(self, node):
        self.node_list.append(node)

    def render(self):
        for node in self.node_list:
            node.render()

    def pick(self, start, direction, mat):
        if self.selected_node:
            self.selected_node.select(False)
            self.selected_node = None

        mindist = sys.maxsize
        closest = None
        for node in self.node_list:
            hit, dist = node.pick(start, direction, mat)
            if hit and dist < mindist:
                mindist, closest = dist, node

        if closest:
            closest.select(True)
            closest.depth = mindist
            closest.selected_loc = start + direction * mindist
            self.selected_node = closest

    def move_selected(self, start, direction, inv_modelview):
        if not self.selected_node: return
        n = self.selected_node
        newloc = start + direction * n.depth
        trans = newloc - n.selected_loc
        pre = np.array([*trans, 0.0])
        delta = inv_modelview.dot(pre)
        n.translate(*delta[:3])
        n.selected_loc = newloc

    def scale_selected(self, up):
        if self.selected_node: self.selected_node.scale(up)

    def place(self, shape, start, direction, inv_modelview):
        if shape == 'sphere': new = Sphere()
        elif shape == 'cube': new = Cube()
        else:                 new = SnowFigure()

        self.add_node(new)
        loc = start + direction * self.PLACE_DEPTH
        pre = np.array([*loc, 1.0])
        world = inv_modelview.dot(pre)
        new.translate(*world[:3])


class Node(object):
    def __init__(self):
        self.color_index = random.randint(color.MIN_COLOR, color.MAX_COLOR)
        self.aabb = AABB([0,0,0],[0.5,0.5,0.5])
        self.translation_matrix = np.identity(4)
        self.scaling_matrix     = np.identity(4)
        self.selected = False

    def render(self):
        glPushMatrix()
        glMultMatrixf(self.translation_matrix.T)
        glMultMatrixf(self.scaling_matrix)
        c = color.COLORS[self.color_index]
        glColor3f(*c)
        if self.selected:
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.3]*3)
        self.render_self()
        if self.selected:
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0]*3)
        glPopMatrix()

    def pick(self, start, direction, mat):
        m = mat.dot(self.translation_matrix).dot(inv(self.scaling_matrix))
        return self.aabb.ray_hit(start, direction, m)

    def select(self, flag=None):
        self.selected = not self.selected if flag is None else flag

    def scale(self, up):
        s = 1.1 if up else 0.9
        self.scaling_matrix = self.scaling_matrix.dot(scaling([s]*3))
        self.aabb.scale(s)

    def translate(self, x, y, z):
        self.translation_matrix = self.translation_matrix.dot(translation([x,y,z]))


class Primitive(Node):
    def __init__(self):
        super(Primitive, self).__init__()
        self.call_list = None

    def render_self(self):
        glCallList(self.call_list)


class Sphere(Primitive):
    def __init__(self):
        super(Sphere, self).__init__()
        self.call_list = G_OBJ_SPHERE


class Cube(Primitive):
    def __init__(self):
        super(Cube, self).__init__()
        self.call_list = G_OBJ_CUBE


class HierarchicalNode(Node):
    def __init__(self):
        super(HierarchicalNode, self).__init__()
        self.child_nodes = []

    def render_self(self):
        for c in self.child_nodes:
            c.render()


class SnowFigure(HierarchicalNode):
    def __init__(self):
        super(SnowFigure, self).__init__()
        self.child_nodes = [Sphere(), Sphere(), Sphere()]
        # ... set up translations & scales as before ...
        self.aabb = AABB([0.0, 0.0, 0.0], [0.5, 1.1, 0.5])


# --- Interaction handler (fixed self.pressed, defaultdict) ---
class Interaction(object):
    def __init__(self):
        self.pressed = None
        self.translation = [0.0, 0.0, 0.0, 0.0]
        self.trackball = trackball.Trackball(theta=-25, distance=15)
        self.mouse_loc = None
        self.callbacks = defaultdict(list)
        self.register()

    # ... rest of your mouse/keyboard handling unchanged ...


if __name__ == "__main__":
    viewer = Viewer()
    viewer.main_loop()
