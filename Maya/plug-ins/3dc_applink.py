import sys
import os
import posixpath
import subprocess
import xml.dom.minidom as dom
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
import maya.OpenMayaUI as omui
import pymel.core as pmc
import maya.cmds as cmds
import json

try:
    from PySide import QtGui, QtCore
    from shiboken import wrapInstance as wrapinstance
except ImportError:
    try:
        from PySide2 import QtCore
        from PySide2 import QtWidgets as QtGui
        from shiboken2 import wrapInstance as wrapinstance
    except ImportError:
        try:
            from PyQt4 import QtGui, QtCore
            from sip import wrapinstance
        except ImportError:
            line = '-' * 44
            print line, '\n<Applink> PySide or PyQt must be installed\n', line
            raise ImportError

PLUGIN_VERSION = '2.2.0 beta'
MAYA_VERSION = int(str(pmc.about(api=1))[:4])


class ApplinkError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


def try_do(func, *args, **kwargs):
    """ Help function, allows to skip exceptions """
    try:
        func(*args, **kwargs)
        return True
    except:
        return False


def warning_msg(text):
    pmc.warning('<Applink> %s' % text)


def error_msg(text):
    raise ApplinkError(text)


def info_msg(text):
    sys.stdout.write('<Applink> %s\n' % text)


def warning_dialog(text, inftext='', justok=False, parent=None):
    msgbox = QtGui.QMessageBox(parent)
    msgbox.setWindowTitle('Warning')
    msgbox.setText(text)
    msgbox.setInformativeText(inftext) if inftext else None
    flags = QtGui.QMessageBox.Yes if justok else QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
    msgbox.setStandardButtons(flags)
    msgbox.setDefaultButton(QtGui.QMessageBox.Yes)
    res = msgbox.exec_()
    return res == QtGui.QMessageBox.Yes


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Preset(object):
    TEX_EMPTY = 'TEX_EMPTY'
    TEX_ONE = 'TEX_ONE'
    TEX_ZERO = 'TEX_ZERO'
    TEX_ALPHA = 'TEX_ALPHA'
    TEX_COLOR = 'TEX_COLOR'
    TEX_COLOR_NOGGX = 'TEX_COLOR_NOGGX'
    TEX_DIFFUSE = 'TEX_DIFFUSE'
    TEX_EMISSIVE = 'TEX_EMISSIVE'
    TEX_EMISSIVE_POWER = 'TEX_EMISSIVE_POWER'
    TEX_ROUGHNESS = 'TEX_ROUGHNESS'
    TEX_METALL = 'TEX_METALL'
    TEX_GLOSS = 'TEX_GLOSS'
    TEX_SPECULARCOLOR = 'TEX_SPECULARCOLOR'
    TEX_SPECULAR_TINT = 'TEX_SPECULAR_TINT'
    TEX_SPECULAR_INTENSITY = 'TEX_SPECULAR_INTENSITY'
    TEX_SPECULARCOLOR_NOGGX = 'TEX_SPECULARCOLOR_NOGGX'
    TEX_SPECULARCOLOR_IORWF = 'TEX_SPECULARCOLOR_IORWF'
    TEX_SPECULARCOLOR_IORWF_NOGGX = 'TEX_SPECULARCOLOR_IORWF_NOGGX'
    TEX_REFLECTION_FRESNEL_IOR = 'TEX_REFLECTION_FRESNEL_IOR'
    TEX_DISPLACEMENT = 'TEX_DISPLACEMENT'
    TEX_TANGENTNORMALMAP = 'TEX_TANGENTNORMALMAP'
    TEX_TANGENT_RED_CHANNEL = 'TEX_TANGENT_RED_CHANNEL'
    TEX_TANGENT_GREEN_CHANNEL = 'TEX_TANGENT_GREEN_CHANNEL'
    TEX_TANGENT_BLUE_CHANNEL = 'TEX_TANGENT_BLUE_CHANNEL'
    TEX_TANGENT_VECTOR_DISPLACEMENT = 'TEX_TANGENT_VECTOR_DISPLACEMENT'
    TEX_ABSOLUTE_VECTOR_DISPLACEMENT = 'TEX_ABSOLUTE_VECTOR_DISPLACEMENT'
    TEX_WORLD_NORMALS = 'TEX_WORLD_NORMALS'
    TEX_CAVITY = 'TEX_CAVITY'
    TEX_AO = 'TEX_AO'

    ALIASES = {
        TEX_COLOR: (TEX_COLOR_NOGGX,),
        TEX_SPECULARCOLOR: (TEX_SPECULARCOLOR_NOGGX, TEX_SPECULARCOLOR_IORWF, TEX_SPECULARCOLOR_IORWF_NOGGX)
    }

    def __init__(self, filename):
        self.filename = filename
        self.slots = []
        self.name = ''
        self.valid = False

        with open(filename) as f:
            xml_string = '\n'.join([x.translate(None, '!&:') for x in f.readlines() if x.count('/') <= 1])
            xmldata = dom.parseString(xml_string)
            root = xmldata.documentElement

            self.valid = True if self.get_node_data(root, 'UseExportConstructor') == 'true' else False
            if self.valid:
                self.name = self.get_node_data(root, 'ExportPreset')
                for etex in root.getElementsByTagName('OneExportTexture'):
                    tex = (
                        self.get_node_data(etex, 'RGB'),
                        self.get_node_data(etex, 'TextureSuffix'),
                        self.get_node_data(etex, 'ExpType').split('TEXTYPE_')[-1],
                        self.get_node_data(etex, 'Extension').split('EXT_')[-1]
                    )
                    self.slots.append(tex)

    @staticmethod
    def get_node_data(nroot, elname):
        return nroot.getElementsByTagName(elname)[0].childNodes[0].data

    @classmethod
    def get_alias(cls, typ, info):
        if typ in cls.ALIASES:
            for name in cls.ALIASES[typ]:
                if name in info:
                    return name

    def get_remapped_slot(self, slot):
        for slotyp, slotname, extyp, ext in self.slots:
            if slotname == slot:
                return slotyp


class ImportInfo(object):
    COLOR = 'color'
    SPECULAR = 'specular'
    SPECULAR_COLOR = 'specular_color'
    EMISSIVE = 'emissive'
    EMISSIVE_POWER = 'emissive_power'
    NORMALMAP = 'normalmap'
    DISPLACEMENT = 'displacement'

    REMAP_SLOTS = {
        COLOR: Preset.TEX_COLOR,
        SPECULAR: Preset.TEX_SPECULAR_INTENSITY,
        SPECULAR_COLOR: Preset.TEX_SPECULARCOLOR,
        EMISSIVE: Preset.TEX_EMISSIVE,
        EMISSIVE_POWER: Preset.TEX_EMISSIVE_POWER,
        NORMALMAP: Preset.TEX_TANGENTNORMALMAP,
        DISPLACEMENT: Preset.TEX_DISPLACEMENT
    }

    SLOTS = (COLOR, SPECULAR, SPECULAR_COLOR, EMISSIVE, EMISSIVE_POWER, NORMALMAP, DISPLACEMENT)

    def __init__(self, obj_import_path, tex_import_path):
        self._res = {}  # obj_path: {'mat': {'slot': (uv, filename, mul), ...}}}
        self._preset = None

        preset_path = os.path.join(os.path.dirname(obj_import_path), 'Export.xml')
        if os.path.exists(preset_path):
            self._preset = Preset(preset_path)
            self._preset = self._preset if self._preset.valid else None

        with open(obj_import_path) as f:
            objpath = os.path.normpath(f.readline().strip())

        with open(tex_import_path) as f:
            lines = filter(None, [x.strip() for x in f.readlines()])

        mats = {}
        if objpath and lines:
            for i in range(0, len(lines) / 4 * 4, 4):
                mat, uv, slot, filename = map(lambda x: os.path.normpath(x.strip()), lines[i:i + 4])
                mul = None
                if self.DISPLACEMENT in slot:
                    slot, mul = slot.split()

                slot = self._preset.get_remapped_slot(slot) if self._preset else self.REMAP_SLOTS[slot]
                mats.setdefault(mat, {}).update({slot: (uv, filename, mul)})
            self._res.update({objpath: mats})

        for path in (obj_import_path, tex_import_path, preset_path):
            try_do(os.remove, path)

    def __contains__(self, item):
        return item in self._res

    def items(self):
        return self._res.items()


class NodePin(object):
    COLOR = 'color'
    INCANDESCENCE = 'incandescence'
    SPECULAR_COLOR = 'specularColor'
    NORMAL_CAMERA = 'normalCamera'
    MR_DIFFUSE = 'diffuse'
    MR_ADDCOLOR = 'additional_color'
    MR_REFL_COLOR = 'refl_color'
    MR_BUMP = 'standard_bump'
    DIPL_SHADER = 'displacementShader'
    FILE = 'file'


class Renderer(object):
    SOFTWARE = 'Software'
    MR = 'Mental Ray'

    INITIAL_SG = 'initialShadingGroup'
    LAMBERT1 = 'lambert1'
    SG_PINS = ('surfaceShader', 'displacementShader', 'miMaterialShader', 'miShadowShader', 'miPhotonShader')
    SG_SURFACE_PINS = ('surfaceShader', 'miMaterialShader')

    PLUGINS = {
        SOFTWARE: None,
        MR: 'Mayatomr.mll'
    }

    SHADER_SG_PINS = {
        SOFTWARE: (('outColor', 'surfaceShader'),),
        MR: (('message', 'miMaterialShader'), ('message', 'miShadowShader'), ('message', 'miPhotonShader'))
    }

    SOFTWARE_COMMON_SHADER_REMAP = (
        (NodePin.COLOR, NodePin.COLOR),
        (NodePin.INCANDESCENCE, NodePin.INCANDESCENCE),
        (NodePin.NORMAL_CAMERA, NodePin.NORMAL_CAMERA),
        (NodePin.SPECULAR_COLOR, NodePin.SPECULAR_COLOR)
    )

    MR_COMMON_SHADER_REMAP = (
        (NodePin.COLOR, NodePin.MR_DIFFUSE),
        (NodePin.INCANDESCENCE, NodePin.MR_ADDCOLOR),
        (NodePin.SPECULAR_COLOR, NodePin.MR_REFL_COLOR),
        (NodePin.NORMAL_CAMERA, NodePin.MR_BUMP)
    )

    RENDERER_SHADERS = {
        SOFTWARE: {
            'lambert': SOFTWARE_COMMON_SHADER_REMAP[:-1],
            'phong': SOFTWARE_COMMON_SHADER_REMAP,
            'phongE': SOFTWARE_COMMON_SHADER_REMAP,
            'blinn': SOFTWARE_COMMON_SHADER_REMAP,
            'anisotropic': SOFTWARE_COMMON_SHADER_REMAP
        },
        MR: {
            'mia_material_x': MR_COMMON_SHADER_REMAP,
            'mia_material_x_passes': MR_COMMON_SHADER_REMAP
        }
    }

    ALL_SHADERS = {k: v for x in RENDERER_SHADERS.itervalues() for k, v in x.iteritems()}

    SOFTWARE_COMMON_SHADER_INPUTS = [
        (NodePin.COLOR, None, Preset.TEX_COLOR, 'texture'),
        (NodePin.NORMAL_CAMERA, None, Preset.TEX_TANGENTNORMALMAP, 'normalmap'),
        (None, NodePin.DIPL_SHADER, Preset.TEX_DISPLACEMENT, 'displacement'),
        (NodePin.INCANDESCENCE, None, (Preset.TEX_EMISSIVE, Preset.TEX_EMISSIVE_POWER), 'tex_with_mask'),
        (NodePin.SPECULAR_COLOR, None, (Preset.TEX_SPECULARCOLOR, Preset.TEX_SPECULAR_INTENSITY), 'tex_with_mask'),
    ]

    MR_COMMON_SHADER_INPUTS = (
        (NodePin.MR_DIFFUSE, None, Preset.TEX_COLOR, 'texture'),
        (NodePin.MR_ADDCOLOR, None, (Preset.TEX_EMISSIVE, Preset.TEX_EMISSIVE_POWER), 'tex_with_mask'),
        (NodePin.MR_REFL_COLOR, None, (Preset.TEX_SPECULARCOLOR, Preset.TEX_SPECULAR_INTENSITY), 'tex_with_mask'),
        (NodePin.MR_BUMP, None, Preset.TEX_TANGENTNORMALMAP, 'normalmap')
    )

    SHADER_INPUTS = {
        'lambert': SOFTWARE_COMMON_SHADER_INPUTS[:-1],
        'phong': SOFTWARE_COMMON_SHADER_INPUTS,
        'phongE': SOFTWARE_COMMON_SHADER_INPUTS,
        'blinn': SOFTWARE_COMMON_SHADER_INPUTS,
        'anisotropic': SOFTWARE_COMMON_SHADER_INPUTS,
        'mia_material_x': MR_COMMON_SHADER_INPUTS,
        'mia_material_x_passes': MR_COMMON_SHADER_INPUTS
    }

    @classmethod
    def get_renderers(cls):
        return [x for x, y in cls.PLUGINS.items() if not y or pmc.pluginInfo(y, q=True, loaded=True)]

    @classmethod
    def get_shaders(cls, renderer):
        return cls.RENDERER_SHADERS[renderer].keys()

    @classmethod
    def shader_exists(cls, shader):
        return shader.type() in cls.ALL_SHADERS

    @classmethod
    def get_renderer_name(cls, shader):
        for renderer, shaders in cls.RENDERER_SHADERS.iteritems():
            if shader in shaders:
                return renderer

    @classmethod
    def get_phong_shader_pins(cls, phong, shader):
        return [(getattr(phong, x), getattr(shader, y)) for x, y in cls.ALL_SHADERS[shader.type()]]

    @classmethod
    def get_shader_sg_pins(cls, shader, sg):
        res = []
        for shader_out, sg_in in cls.SHADER_SG_PINS[cls.get_renderer_name(shader.type())]:
            res.append((getattr(shader, shader_out), getattr(sg, sg_in)))
        return res

    @staticmethod
    def reassign_sg(src_sg, dst_sg):
        pmc.select(src_sg.dagSetMembers.connections())
        pmc.hyperShade(assign=dst_sg)

    @classmethod
    def collect_input_nodes(cls, nodes, res):
        for node in nodes:
            cls.collect_input_nodes(set(node.connections(s=True, d=False)), res)
            res.add(node)

    @classmethod
    def cleanup_shading_network(cls, sg):
        res = set()
        for pin_name in cls.SG_PINS:
            pin = getattr(sg, pin_name, None)
            if pin:
                cls.collect_input_nodes(pin.connections(), res)

        res = list(res)
        res.remove(cls.LAMBERT1) if cls.LAMBERT1 in res else None
        pmc.delete(res)

    @staticmethod
    def muldiv_node(op=1):
        node = pmc.shadingNode(pmc.nt.MultiplyDivide, asUtility=True)
        node.operation.set(op)  # (nop, mul, div, pow)
        return node

    @staticmethod
    def color_node(col=(1, 1, 1)):
        t2d = pmc.shadingNode(pmc.nt.Place2dTexture, asUtility=True)
        ramp = pmc.shadingNode(pmc.nt.Ramp, asUtility=True)
        ramp.interpolation.set(0)
        pmc.removeMultiInstance(ramp.colorEntryList[2], b=True)
        pmc.removeMultiInstance(ramp.colorEntryList[1], b=True)
        ramp.colorEntryList[0].color.set(*col)

        t2d.outUV.connect(ramp.uvCoord)
        t2d.outUvFilterSize.connect(ramp.uvFilterSize)
        return ramp

    @staticmethod
    def file_node(filename):
        tex = pmc.shadingNode(pmc.nt.File, asUtility=True)
        tex.fileTextureName.set(filename)
        t2d = pmc.shadingNode(pmc.nt.Place2dTexture, asUtility=True)

        t2d.coverage.connect(tex.coverage)
        t2d.translateFrame.connect(tex.translateFrame)
        t2d.rotateFrame.connect(tex.rotateFrame)
        t2d.mirrorU.connect(tex.mirrorU)
        t2d.mirrorV.connect(tex.mirrorV)
        t2d.stagger.connect(tex.stagger)
        t2d.wrapU.connect(tex.wrapU)
        t2d.wrapV.connect(tex.wrapV)
        t2d.repeatUV.connect(tex.repeatUV)
        t2d.offset.connect(tex.offset)
        t2d.rotateUV.connect(tex.rotateUV)
        t2d.noiseUV.connect(tex.noiseUV)
        t2d.vertexUvOne.connect(tex.vertexUvOne)
        t2d.vertexUvTwo.connect(tex.vertexUvTwo)
        t2d.vertexUvThree.connect(tex.vertexUvThree)
        t2d.vertexCameraOne.connect(tex.vertexCameraOne)
        t2d.outUV.connect(tex.uvCoord)
        t2d.outUvFilterSize.connect(tex.uvFilterSize)
        return tex

    @classmethod
    def texture(cls, typ, info, shader_pin, sg_pin):
        typ = typ if typ in info else Preset.get_alias(typ, info)
        if typ:
            uv, filename, mul = info[typ]
            tex = cls.file_node(filename)
            tex.outColor.connect(shader_pin)

    @classmethod
    def tex_with_mask(cls, types, info, shader_pin, sg_pin):
        typa, typb = [x if x in info else Preset.get_alias(x, info) for x in types]
        texa, texb = None, None

        if typa:
            uv, filename, mul = info[typa]
            texa = cls.file_node(filename)

        if typb:
            uv, filename, mul = info[typb]
            texb = cls.file_node(filename)

        if texa and texb:
            spec_mask = cls.muldiv_node()
            texa.outColor.connect(spec_mask.input1)
            texb.outColor.connect(spec_mask.input2)
            spec_mask.output.connect(shader_pin)

        elif texa or texb:
            tex = texa if texa else texb
            tex.outColor.connect(shader_pin)

    @classmethod
    def normalmap(cls, typ, info, shader_pin, sg_pin):
        if typ in info:
            uv, filename, mul = info[typ]
            tex = cls.file_node(filename)
            bump2d = pmc.shadingNode(pmc.nt.Bump2d, asUtility=True)
            bump2d.bumpInterp.set(1)
            tex.outAlpha.connect(bump2d.bumpValue)
            bump2d.outNormal.connect(shader_pin)

    @classmethod
    def displacement(cls, typ, info, shader_pin, sg_pin):
        if typ in info:
            uv, filename, mul = info[typ]
            tex = cls.file_node(filename)
            displ_shader = pmc.shadingNode(pmc.nt.DisplacementShader, asShader=True)
            displ_mul = cls.muldiv_node()
            displ_mul.input1X.set(float(mul))
            tex.outAlpha.connect(displ_mul.input2X)
            displ_mul.outputX.connect(displ_shader.displacement)
            displ_shader.displacement.connect(sg_pin)

    @classmethod
    def create_shading_network(cls, sg, info, shader_typ, preset=None, cleanup=True):
        """ Create a new shading network based on input slots
        (uv, tex_path, mul)
        info = {
            'TEX_COLOR': (
                'blinn1SG',
                'd:\\MayaExtensions\\projects\\default\\3dcoat\\export_blinn1SG_color.tga',
                None
            ),
            ...
        }
        """
        if cleanup:
            cls.cleanup_shading_network(sg)

        if sg == cls.INITIAL_SG:
            # if we used initial sg, we can't do remapping (have to use default lambert)
            shader = sg.surfaceShader.connections()[0]
            shader_typ = shader.type()
        else:
            shader = pmc.shadingNode(shader_typ, asShader=True)
            [x.connect(y, f=True) for x, y in cls.get_shader_sg_pins(shader, sg)]

        for shader_pin, sg_pin, typ, func_name in cls.SHADER_INPUTS[shader_typ]:
            shader_pin = getattr(shader, shader_pin) if shader_pin else None
            sg_pin = getattr(sg, sg_pin) if sg_pin else None
            func = getattr(cls, func_name)
            func(typ, info, shader_pin, sg_pin)


class Config(object):
    __metaclass__ = Singleton

    EXP_COL = 'ExportColor'
    EXP_SPEC = 'ExportSpecular'
    EXP_SPEC_COL = 'ExportSpecularColor'
    EXP_EM_POWER = 'ExportEmissivePower'
    EXP_EM_COL = 'ExportEmissive'
    EXP_NM = 'ExportNormalmap'
    EXP_ROUG = 'ExportRoughness'
    EXP_METAL = 'ExportMetallness'
    EXP_AO = 'ExportAO'
    EXP_DISPL = 'ExportDispl'

    TEX_COL = 'ColorFileExtension'
    TEX_SPEC = 'SpecExtension'
    TEX_NM = 'NormExtension'
    TEX_DISPL = 'DisplExt'

    GEOM_LEV = 'ExportResolution'
    DISPL_NORM = 'DisplNorm'
    DISPL_DEPTH = 'DisplDepth'
    SKIP_IMP = 'SkipImport'
    SKIP_EXP = 'SkipExport'
    PICK_SRCPOS = 'PickSourcePositions'
    PICK_DEPTH0 = 'PickDepthFromLayer0'
    COARSE_MESH = 'CoarseMesh'
    CREATE_PADDING = 'field $ExportOpt::CreatePadding'

    # internal settings
    COAT_PATH = 'Path'
    COAT_EXCH = 'Exchange'
    REPL_SHAPE = 'ReplaceShape'
    TEXSET_METHOD = 'TexturesSetMethod'
    PRESET = 'Preset'
    RENDERER = 'Renderer'
    SHADER = 'Shader'
    OBJ_EXT = 'obj'

    OP_BIN = (EXP_COL, EXP_SPEC, EXP_SPEC_COL, EXP_EM_POWER, EXP_EM_COL, EXP_NM, EXP_ROUG, EXP_METAL, EXP_AO,
              EXP_DISPL, SKIP_IMP, SKIP_EXP, PICK_SRCPOS, PICK_DEPTH0, COARSE_MESH, CREATE_PADDING)

    OP_TEX = (TEX_COL, TEX_SPEC, TEX_NM, TEX_DISPL)
    OP_SEL = (GEOM_LEV, DISPL_NORM)

    COL_EXTENSION = ('TGA (.tga)', 'BMP (.bmp)', 'PNG (.png)', 'JPG (.jpg)',
                     'TIF (.tif)', 'TIFF (.tiff)', 'EXR (.exr)', 'PSD (.psd)')

    DISPL_EXTENSION = ('BMP 8-bits(.bmp)', 'TGA 8-bits(.tga)', 'PNG 8-bits(.png)', 'TIF 16-bits(.tif)',
                       'TIFF 32-bits(.tiff)', 'EXR 32-bits(.exr)')

    SETS = {DISPL_NORM: ('GREYBASED', 'ZEROBASED', 'ZEROBASED_NORM', 'ZEROBASED_ABS'),
            TEX_DISPL: DISPL_EXTENSION,
            DISPL_DEPTH: [x.split()[-1].split('(')[0] for x in DISPL_EXTENSION],
            TEX_COL: COL_EXTENSION,
            TEX_SPEC: COL_EXTENSION,
            TEX_NM: COL_EXTENSION[:-1],
            RENDERER: Renderer.get_renderers(),
            SHADER: (),
            GEOM_LEV: ('LOW-POLY', 'MID-POLY')}

    BOOL_FIELD = {0: 'false', 1: 'true'}

    def __init__(self):
        self._data = {
            self.EXP_COL: 1, self.EXP_SPEC: 1, self.EXP_SPEC_COL: 1, self.EXP_EM_POWER: 1, self.EXP_EM_COL: 1,
            self.EXP_NM: 1, self.EXP_ROUG: 0, self.EXP_METAL: 0, self.EXP_AO: 0, self.EXP_DISPL: 0,
            self.TEX_COL: 0, self.TEX_SPEC: 0, self.TEX_NM: 0, self.TEX_DISPL: 0, self.GEOM_LEV: 0, self.DISPL_NORM: 0,
            self.DISPL_DEPTH: 0, self.SKIP_IMP: 0, self.SKIP_EXP: 0, self.CREATE_PADDING: 1,
            self.PICK_SRCPOS: 0, self.PICK_DEPTH0: 0, self.COARSE_MESH: 0, self.COAT_PATH: '', self.COAT_EXCH: '',
            self.REPL_SHAPE: 1, self.TEXSET_METHOD: 0, self.PRESET: 0, self.RENDERER: 0, self.SHADER: 0}

        self.maya_project_path = ''  # C:/Project/xxx/
        self.maya_project_coat = ''  # C:/Project/xxx/3dcoat/
        self.coat_maya_dir = ''  # C:/Users/xxx/Documents/3D-CoatVX/Exchange/Maya
        self.text_import_path2 = ''  # C:/Users/xxx/Documents/3D-CoatVX/Exchange/Maya/export.txt
        self.text_export_path = ''  # C:/Users/xxx/Documents/3D-CoatVX/Exchange/import.txt
        self.text_import_path = ''  # C:/Users/xxx/Documents/3D-CoatVX/Exchange/export.txt
        self.textures_import_path = ''  # C:/Users/xxx/Documents/3D-CoatVX/Exchange/textures.txt

        # C:/Users/xxx/Documents
        self.user_docs_dir, appext = self.get_platform()

        # C:/Users/xxx/Documents/applinkMayaCoat.cfg
        self.config_path = posixpath.join(self.user_docs_dir, 'applinkMayaCoat.cfg')

        self.load()

        # C:/Program Files/Autodesk/Maya2014/bin/maya.exe
        self.maya_path = posixpath.join(os.getenv('MAYA_LOCATION'), appext)

        # reset 3D-Coat path if it not exists anymore
        coat_path = self.get_opt(self.COAT_PATH)
        if coat_path and not os.path.exists(coat_path):
            self.set_opt(self.COAT_PATH, '')

        self.set_exchange()

        # C:/Users/xxx/Documents/3D-CoatVX/Exchange/Maya/run.txt ('extension.txt')
        with open(posixpath.join(self.coat_maya_dir, 'run.txt'), 'w+') as f:
            f.truncate()
            f.write(self.maya_path)

        with open(posixpath.join(self.coat_maya_dir, 'extension.txt'), 'w+') as f:
            f.truncate()
            f.write(self.OBJ_EXT)

        self.set_project()
        self.report()

    @staticmethod
    def check_dir(d):
        try_do(os.makedirs, d)

    @staticmethod
    def get_platform():
        ext = {'linux': 'bin/maya', 'linux2': 'bin/maya',
               'darwin': 'Maya.app/Contents/MacOS/Maya',
               'win32': 'bin/maya.exe'}

        home = os.path.expanduser('~')
        return home, ext.get(sys.platform, '')

    def get_coat_path(self):
        coat_path = self.get_opt(self.COAT_PATH)
        if coat_path and sys.platform == 'darwin':
            coat_path += '/Contents/MacOS/3D-Coat'
        return coat_path

    def set_project(self):
        maya_proj = cmds.workspace(q=1, rd=1)
        if self.maya_project_path != maya_proj:
            self.maya_project_path = maya_proj  # 'C:/Projects/Test/'
            self.maya_project_coat = posixpath.join(self.maya_project_path, '3dcoat/')  # 'C:/Projects/Test/3dcoat/'
            [self.check_dir(x) for x in (self.maya_project_path, self.maya_project_coat)]

    def set_exchange(self):
        exchange_dir = self.get_opt(self.COAT_EXCH)
        if not exchange_dir:
            exchange_dir = posixpath.join(self.user_docs_dir, '3D-CoatV4', 'Exchange')
            self.set_opt(self.COAT_EXCH, exchange_dir)

        self.coat_maya_dir = posixpath.join(exchange_dir, 'Maya')
        self.text_import_path2 = posixpath.join(self.coat_maya_dir, 'export.txt')
        self.text_export_path = posixpath.join(exchange_dir, 'import.txt')
        self.text_import_path = posixpath.join(exchange_dir, 'export.txt')
        self.textures_import_path = posixpath.join(exchange_dir, 'textures.txt')
        self.check_dir(self.coat_maya_dir)  # check/create all dirs

    def load(self):
        if not os.path.exists(self.config_path):
            return self.save()

        with open(self.config_path) as f:
            try:
                config = json.load(f)
            except ValueError:
                return self.save()  # can't parse config file, dump default config

        if sorted(config.keys()) != sorted(self._data.keys()):
            return self.save()
        self._data.update(config)

    def save(self):
        with open(self.config_path, 'w+') as f:
            json.dump(self._data, f)

    def get_opt(self, opt, default=None):
        return self._data.get(opt, default)

    def set_opt(self, key, val):
        if key in self._data:
            self._data[key] = val

    def rep(self):
        for k in self._data:
            print '"%s"=%s' % (k, self._data[k])

    def get_obj_import_path(self):
        if os.path.exists(self.text_import_path) and os.path.exists(self.textures_import_path):
            return self.text_import_path
        if os.path.exists(self.text_import_path2) and os.path.exists(self.textures_import_path):
            return self.text_import_path2

    def get_import_info(self):
        obj_import_path = self.get_obj_import_path()
        if obj_import_path:
            return ImportInfo(obj_import_path, self.textures_import_path)

    def get_options_dump(self):
        def _wrap(var, val=None, div='='):
            if val is None:
                return '[%s]\n' % var
            val = self.BOOL_FIELD[val] if var.startswith('field') and val in self.BOOL_FIELD else val
            return '[%s%s%s]\n' % (var, div, val)

        outcfg = [(x, self._data[x]) for x in self.OP_BIN]
        outcfg.extend([(x, self.SETS[x][self._data[x]].split()[0]) for x in self.OP_TEX])
        outcfg.extend([(x, self.SETS[x][self._data[x]]) for x in self.OP_SEL])
        outcfg.append((self.DISPL_DEPTH, self.SETS[self.DISPL_DEPTH][self._data[self.TEX_DISPL]]))

        res = ''
        for key, value in outcfg:
            res += _wrap(key, value)

        res += _wrap(self.SKIP_IMP) if self.get_opt(self.SKIP_IMP) else ''
        res += _wrap(self.SKIP_EXP) if self.get_opt(self.SKIP_EXP) else ''
        return res

    def report(self):
        print '3D-Coat settings:\n' \
              'maya.exe path:    %s\n' \
              'user docs path:   %s\n' \
              '3dcoat maya dir:  %s\n' \
              'maya project dir: %s\n' \
              'maya 3dcoat dir:  %s\n%s' % (
                  self.maya_path, self.user_docs_dir, self.coat_maya_dir,
                  self.maya_project_path, self.maya_project_coat, '-' * 32)


class ExportButton(QtGui.QPushButton):
    STYLE = 'QPushButton {background-color: #59585D;}'

    def __init__(self, text, ann, mode, parent=None):
        QtGui.QPushButton.__init__(self, text, parent)
        self.mode = mode
        self.setFixedHeight(20)
        self.setToolTip(ann)
        self.setStyleSheet(self.STYLE)


class CheckButton(QtGui.QPushButton):
    STYLE = 'QPushButton {background-color: #59585D;}' \
            'QPushButton:checked {color: #D2D1D6; background-color: #4C6A8C;}'

    def __init__(self, text, op, parent=None):
        QtGui.QPushButton.__init__(self, text, parent)
        self._op = op
        self.setFixedHeight(20)
        self.setCheckable(True)
        self.setChecked(Config().get_opt(op))
        self.setStyleSheet(self.STYLE)
        self.clicked.connect(self.on_checked_button)

    def on_checked_button(self):
        Config().set_opt(self._op, int(self.isChecked()))


class CheckBox(QtGui.QCheckBox):
    def __init__(self, text, op, parent=None):
        QtGui.QCheckBox.__init__(self, text, parent)
        self._op = op
        self.setFixedHeight(20)
        self.setCheckable(True)
        self.setChecked(Config().get_opt(op))
        self.clicked.connect(self.on_checked_button)

    def on_checked_button(self):
        Config().set_opt(self._op, int(self.isChecked()))


class SplitLine(QtGui.QFrame):
    def __init__(self, height=0, parent=None):
        QtGui.QFrame.__init__(self, parent)
        self.setFrameShape(QtGui.QFrame.HLine)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setMidLineWidth(1)
        self.setFixedHeight(height) if height else None


class OptionsFrame(QtGui.QFrame):
    def __init__(self, options):
        QtGui.QFrame.__init__(self, parent=None)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Sunken)

        layout = QtGui.QGridLayout(self)
        layout.setSpacing(2)
        for n in xrange(len(options)):
            i, j = n % 2, n / 2
            text, op = options[n]
            layout.addWidget(CheckBox(text, op), j, i)


class ComboBox(QtGui.QWidget):
    def __init__(self, text, op, parent_layout=None, width=(None, None), items=None, on_change_cb=None):
        QtGui.QWidget.__init__(self, parent=None)
        self._op = op
        self._on_change_cb = on_change_cb
        label_width, combox_width = width

        label = QtGui.QLabel(text)
        label.setFixedWidth(label_width) if label_width else None

        self._combox = QtGui.QComboBox()
        self._combox.setFixedWidth(combox_width) if combox_width else None
        self.reset(items)
        self.set_current_index(Config().get_opt(self._op))
        self._combox.currentIndexChanged.connect(self.on_index_changed)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(label)
        layout.addWidget(self._combox)
        self.setLayout(layout)
        parent_layout.addWidget(self) if isinstance(parent_layout, QtGui.QLayout) else None

    def current_text(self):
        return self._combox.currentText()

    def set_current_index(self, index):
        max_index = self._combox.count() - 1
        index = max_index if index > max_index else index
        self._combox.setCurrentIndex(index)

    def on_index_changed(self):
        Config().set_opt(self._op, self._combox.currentIndex())
        if self._on_change_cb:
            self._on_change_cb(self._combox.currentText())

    def reset(self, items=None):
        items = items if items else Config.SETS.get(self._op, [])
        self._combox.clear()
        self._combox.addItems(items)


class EditPath(QtGui.QWidget):
    def __init__(self, text, op, on_set, parent_layout=None):
        QtGui.QWidget.__init__(self, parent=None)
        label = QtGui.QLabel(text)

        self._edit = QtGui.QLineEdit(Config().get_opt(op))
        self._edit.setReadOnly(True)
        self._edit.op = op
        self._edit.textChanged.connect(self.on_text_changed)

        button = QtGui.QPushButton('Set')
        button.setFixedHeight(20)
        button.clicked.connect(on_set)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(label)
        layout.addWidget(self._edit)
        layout.addWidget(button)
        self.setLayout(layout)
        parent_layout.addWidget(self) if isinstance(parent_layout, QtGui.QLayout) else None

    def on_text_changed(self):
        Config().set_opt(self._edit.op, self._edit.text())

    def text(self):
        return self._edit.text()

    def set_text(self, text):
        self._edit.setText(text)


class ExportOptionsDialog(QtGui.QDialog):
    SLOT_BUTTONS = (('Color', Config.EXP_COL), ('Emissive', Config.EXP_EM_POWER),
                    ('Specular', Config.EXP_SPEC), ('Emissive Color', Config.EXP_EM_COL),
                    ('Specular Color', Config.EXP_SPEC_COL), ('Normals', Config.EXP_NM),
                    ('Roughness', Config.EXP_ROUG), ('Metalness', Config.EXP_METAL),
                    ('AO', Config.EXP_AO), ('Displacement', Config.EXP_DISPL))

    COLOR_POPS = (('Color/Emissive', Config.TEX_COL),
                  ('Specular', Config.TEX_SPEC),
                  ('Normals', Config.TEX_NM),
                  ('Displacement', Config.TEX_DISPL),
                  ('Displ Normalization ', Config.DISPL_NORM),
                  ('Export Resolution', Config.GEOM_LEV))

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('Manual Settings')

        slots_group = QtGui.QGroupBox('Texture Slots')
        slot_layout = QtGui.QGridLayout()
        slot_layout.setSpacing(4)

        for j in xrange(len(self.SLOT_BUTTONS) / 2):
            for i in xrange(2):
                text, op = self.SLOT_BUTTONS[j * 2 + i]
                slot_layout.addWidget(CheckButton(text, op), j, i)
        slots_group.setLayout(slot_layout)

        options_layout = QtGui.QVBoxLayout()
        combox_width = (92, None)
        for text, op in self.COLOR_POPS:
            ComboBox(text, op, options_layout, combox_width)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(slots_group)
        layout.addLayout(options_layout)
        self.setLayout(layout)
        self.setFixedSize(self.sizeHint())


class Tool(QtGui.QMainWindow):
    MISC_EXP_BUTTONS = (('Skip Import', Config.SKIP_IMP), ('Pick Src Pos', Config.PICK_SRCPOS),
                        ('Skip Export', Config.SKIP_EXP), ('Pick Depth L0', Config.PICK_DEPTH0),
                        ('Coarse Mesh', Config.COARSE_MESH), ('Create Padding', Config.CREATE_PADDING))

    MISC_IMP_BUTTONS = (('Replace Shape', Config.REPL_SHAPE),)

    IO_CONTROLS = (
        (' - Paint mesh in 3D-Coat using', None, None),
        ('per-pixel painting', 'Paint mesh in 3D-Coat using per-pixel painting', 0),
        ('microvertex painting', 'Paint mesh in 3D-Coat using microvertex painting', 1),
        ('Ptex', 'Paint mesh in 3D-Coat using Ptex', 2),

        (' - Drop mesh in 3D-Coat', None, None),
        ('as voxel object', 'Drop mesh in 3D-Coat as voxel object', 6),
        ('as single voxel object', 'Drop mesh in 3D-Coat as single voxel object, all objects will be merged', 10),
        ('as new pen alpha', 'Drop mesh in 3D-Coat as new pen alpha', 7),
        ('as new merging primitive for voxels', 'Drop mesh in 3D-Coat as new merging primitive for voxels', 8),
        ('as a curve profile', 'Drop mesh in 3D-Coat as a curve profile', 11),
        ('for Auto-retopology', 'Paint mesh in 3D-Coat using per-pixel painting', 9),

        (' - Misc', None, None),
        ('Perform UV-mapping in 3D-Coat', 'Perform UV-mapping in 3D-Coat', 3),
        ('Drop reference mesh to 3D-Coat', 'Drop reference mesh to 3D-Coat', 4),
        ('  Drop retopo mesh as new layer in 3D-Coat  ', 'Drop retopo mesh as new layer in 3D-Coat', 5),

        ('', None, None),
        ('[ Import ]', 'Import object into Maya', None))

    WORLD = 'world'
    NAMESPACE = 'coat:'
    OBJ_EXPORT_FLAGS = 'groups=1;ptgroups=1;materials=1;smoothing=1;normals=1'
    EXPORT_MODES = ('[ppp]', '[mv]', '[ptex]', '[uv]', '[ref]', '[retopo]', '[vox]',
                    '[alpha]', '[prim]', '[autopo]', '[voxcombine]', '[curv]')

    def __init__(self):
        QtGui.QMainWindow.__init__(self, parent=self.get_maya_window())
        self.setWindowFlags((self.windowFlags() | QtCore.Qt.CustomizeWindowHint) & ~QtCore.Qt.WindowMaximizeButtonHint)
        self.setWindowTitle('3D-Coat applink %s' % PLUGIN_VERSION)
        self.setFixedSize(self.sizeHint())
        self._presets = {}
        config = Config()

        # io layout
        io_layout = QtGui.QVBoxLayout()
        io_layout.setSpacing(2)
        io_tab = QtGui.QWidget()
        io_tab.setLayout(io_layout)

        # export controls
        for text, ann, mode in self.IO_CONTROLS:
            if ann is None:
                ctl = QtGui.QLabel(text)
                height = 18 if text else 10
                ctl.setFixedHeight(height)
            else:
                ctl = ExportButton(text, ann, mode)
                if mode is None:
                    ctl.setFixedHeight(32)
                    ctl.clicked.connect(self.on_import)
                else:
                    ctl.clicked.connect(self.on_export)
            io_layout.addWidget(ctl)

        # options tab
        options_layout = QtGui.QVBoxLayout()
        options_layout.setSpacing(4)
        options_layout.setAlignment(QtCore.Qt.AlignTop)
        options_tab = QtGui.QWidget()
        options_tab.setLayout(options_layout)

        # coat path & exchange dir
        self._path_edit = EditPath('3D-Coat Path', Config.COAT_PATH, self.on_set_path, options_layout)
        self._exchange_edit = EditPath('Exchange Dir', Config.COAT_EXCH, self.on_set_exch, options_layout)

        # -- export group
        export_group = QtGui.QGroupBox('Export')

        # slots
        self._radio_slots = QtGui.QRadioButton('Use Manual Settings')
        self._radio_slots.clicked.connect(lambda: self.on_export_method_change(0))
        self._button_slots = QtGui.QPushButton('Show')
        self._button_slots.clicked.connect(self.on_show_options)

        slots_layout = QtGui.QHBoxLayout()
        slots_layout.addWidget(self._radio_slots)
        slots_layout.addWidget(self._button_slots)

        # presets
        self._radio_presets = QtGui.QRadioButton('Preset')
        self._radio_presets.setFixedWidth(54)
        self._radio_presets.clicked.connect(lambda: self.on_export_method_change(1))
        self._radio_presets.setEnabled(False)  # ??? disable this for now
        self._sel_preset = QtGui.QComboBox()
        self._sel_preset.setFixedWidth(140)
        self.reset_presets(True)
        self._sel_preset.currentIndexChanged.connect(self.on_preset_changed)

        presets_layout = QtGui.QHBoxLayout()
        presets_layout.addWidget(self._radio_presets)
        presets_layout.addWidget(self._sel_preset)

        self.on_export_method_change(config.get_opt(Config.TEXSET_METHOD), force=True)

        export_layout = QtGui.QVBoxLayout()
        export_layout.addLayout(slots_layout)
        export_layout.addLayout(presets_layout)
        export_layout.addWidget(OptionsFrame(self.MISC_EXP_BUTTONS))
        export_group.setLayout(export_layout)
        options_layout.addWidget(export_group)

        # -- import group
        import_group = QtGui.QGroupBox('Import')

        import_layout = QtGui.QVBoxLayout()
        combox_width = (50, None)
        self._renderer = ComboBox('Renderer', Config.RENDERER, import_layout, combox_width, None, self.reset_shaders)
        self._shader = ComboBox('Shader', Config.SHADER, import_layout, combox_width)

        shader_index = config.get_opt(Config.SHADER)
        self.reset_shaders(self._renderer.current_text())
        self._shader.set_current_index(shader_index)

        import_layout.addWidget(OptionsFrame(self.MISC_IMP_BUTTONS))
        import_group.setLayout(import_layout)
        options_layout.addWidget(import_group)

        # tabs
        tabs = QtGui.QTabWidget()
        tabs.setStyleSheet('QTabWidget {background-color: #3E3E40}')
        tabs.addTab(io_tab, 'I/O')
        tabs.addTab(options_tab, 'Options')
        self.setCentralWidget(tabs)

    @staticmethod
    def get_maya_window():
        ptr = omui.MQtUtil.mainWindow()
        if ptr is not None:
            return wrapinstance(long(ptr), QtGui.QMainWindow)

    # @staticmethod
    # def is_coat_running():
    #     def win_exec():
    #         win_cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
    #         return subprocess.Popen(win_cmd, shell=True, stdout=subprocess.PIPE)
    #
    #     def nix_exec():
    #         return subprocess.Popen("ps aux", shell=True, stdout=subprocess.PIPE)
    #
    #     proc = win_exec if 'win32' in sys.platform else nix_exec
    #     with proc().stdout as f:
    #         for line in f:
    #             if line.startswith('3D-Coat'):
    #                 return True
    #
    #     return False

    # mid fix: 2019/08/14 darwin always return false
    @staticmethod
    def is_coat_running():
        def win_exec():
            win_cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
            res = subprocess.Popen(win_cmd, shell=True, stdout=subprocess.PIPE)
            with res.stdout as f:
                for line in f:
                    if line.startswith('3D-Coat'):
                        return True
            return False

        # def nix_exec():
        #     return subprocess.Popen("ps aux", shell=True, stdout=subprocess.PIPE)
        #
        # proc = win_exec if 'win32' in sys.platform else nix_exec
        # with proc().stdout as f:
        #     for line in f:
        #         if line.startswith('3D-Coat'):
        #             return True

        ### Mid
        def nix_exec():
            res = subprocess.Popen("ps axco pid,command | grep -i 3d-coat", shell=True, stdout=subprocess.PIPE)
            with res.stdout as f:
                for line in f:
                    if line.rfind('3D-Coat') != -1:
                        return True
            return False

        return win_exec() if 'win32' in sys.platform else nix_exec()

    @staticmethod
    def prune_mtl(mtl_path):
        if os.path.exists(mtl_path):
            with open(mtl_path, 'r+') as f:
                res = [x for x in f.readlines() if x.startswith('newmtl')]
                f.seek(0)
                f.truncate()
                f.writelines(res)

    @staticmethod
    def get_selected():
        res = []
        for item in set([x.node() for x in pmc.selected()]):
            shape = item.getShape() if isinstance(item, pmc.nt.Transform) else item
            if isinstance(shape, pmc.nt.Mesh):
                res.append(item)
        return tuple(res)

    @staticmethod
    def get_sg_pairs(prefix):
        res = []
        sgs = pmc.ls(typ=pmc.nt.ShadingEngine)

        for imp_sg in [x for x in sgs if x.startswith(prefix)]:
            name, old_sg = imp_sg.split(prefix)[-1], None
            if name in sgs:
                old_sg = sgs[sgs.index(name)]
            else:
                imp_sg.rename(name)  # rename imported sg with non-prefix name
            res.append((old_sg, imp_sg))
        return res

    @staticmethod
    def get_object_shaderset(obj):
        shaders, sg = [], None
        sgs = obj.shadingGroups()
        if sgs:
            sg = sgs[0]
            for atrname in Renderer.SG_SURFACE_PINS:
                atr = getattr(sg, atrname, None)
                shaders.extend(atr.connections()) if atr else None
        return shaders, sg

    @staticmethod
    def get_sg_object(sg, warning=False):
        if sg:
            objects = sg.dagSetMembers.connections()
            if not objects and warning:
                warning_msg('Shading Group <%s> does not have connected mesh(es)!' % sg)
            return objects[0] if objects else None

    @staticmethod
    def remap_shadersets(shadersets):
        res = []
        for obj, ([shader], sg) in shadersets:
            phong = pmc.shadingNode(pmc.nt.Phong, asShader=True, n='%s_temp' % shader)

            for phong_in, shader_in in Renderer.get_phong_shader_pins(phong, shader):
                connections = shader_in.connections()
                node = connections[0] if connections else None
                if isinstance(node, pmc.nt.File):
                    node.outColor.connect(phong_in)

            pin_pairs = Renderer.get_shader_sg_pins(shader, sg)
            [x.disconnect() for _, x in pin_pairs]
            phong.outColor.connect(sg.surfaceShader, f=True)
            res.append((phong, pin_pairs))
        return res

    @staticmethod
    def undo_remap_shadersets(remapped):
        for phong, pin_pairs in remapped:
            for shader_pin, sg_pin in pin_pairs:
                shader_pin.connect(sg_pin, f=True)
            pmc.delete(phong)

    @staticmethod
    def fix_pivot_space(src, dst):
        pmc.makeIdentity(src, a=1, t=1, r=0, s=0, pn=0)
        src.translateBy(-dst.translate.get())
        pmc.makeIdentity(src, a=1, t=1, r=0, s=0, pn=0)
        src.translateBy(dst.translate.get())

    @classmethod
    def restore_transforms(cls, src, dst):
        rp = dst.getScalePivot(om.MSpace.kObject)
        sp = dst.getRotatePivot(om.MSpace.kObject)
        src_center = dst.getBoundingBox(space=cls.WORLD).center()
        dst_center = src.getBoundingBox(space=cls.WORLD).center()
        src.translateBy(src_center - dst_center, space=cls.WORLD)
        src.setParent(dst)
        src.centerPivots()
        pmc.makeIdentity(src, a=1, t=1, r=1, s=1, pn=1)
        src.setRotatePivot(rp, om.MSpace.kObject)
        src.setScalePivot(sp, om.MSpace.kObject)
        src.setParent(dst.getParent())

        # fix different pivot spaces issue
        cls.fix_pivot_space(src, dst)
        cls.fix_pivot_space(dst, src)

    @staticmethod
    def reset_transforms_for_imported(obj):
        obj.centerPivots()
        center = obj.getScalePivot(om.MSpace.kObject)[:-1]  # Point4 -> Vector3
        obj.setTranslation(-center)
        pmc.makeIdentity(obj, a=1, t=1, r=1, s=1, pn=1)
        obj.setTranslation(center)
        pmc.delete(obj, ch=1)

    @classmethod
    def fix_namespace_clashing(cls, delete=False):
        bad_nodes = pmc.ls('%s*' % cls.NAMESPACE)
        if delete:
            try_do(pmc.delete, bad_nodes)
        else:
            for node in bad_nodes:
                try_do(pmc.rename, node, node.lstrip(cls.NAMESPACE))

    @staticmethod
    def copy_mesh(src, dst):
        pmc.delete(dst, ch=True)
        pmc.polyTriangulate(dst, ch=False)  # forced to triangulate (otherwise MayaAPI won't copy mesh data)
        src_shape = src.getShape()
        dst_shape = dst.getShape()
        dst_mfn = dst_shape.__apimfn__()
        dst_mfn.copyInPlace(src_shape.__apimobject__())

    def reset_shaders(self, renderer):
        self._shader.reset(Renderer.get_shaders(renderer))

    def reset_presets(self, init=False):
        self._presets.clear()
        presets_dirs = [(self._path_edit.text(), ('Temp', 'ExportPresets')),
                        (self._exchange_edit.text(), ('Temp', 'TempPresets'))]

        for path_dir, path_suffixes in presets_dirs:
            if not posixpath.exists(path_dir):
                continue

            preset_dir = posixpath.join(posixpath.dirname(path_dir), *path_suffixes)
            if not posixpath.exists(preset_dir):
                continue

            for filename in os.listdir(preset_dir):
                filepath = os.path.join(preset_dir, filename)
                name = os.path.splitext(filename)[0]
                self._presets.setdefault(name, Preset(filepath))

        presets = sorted(self._presets.keys())
        self._sel_preset.clear()
        self._sel_preset.addItems(presets)

        # set per item tooltip
        num_presets = len(presets)
        for i in xrange(num_presets):
            self._sel_preset.setItemData(i, presets[i], QtCore.Qt.ToolTipRole)

        if init:
            current = Config().get_opt(Config.PRESET)
            if current < num_presets:
                self._sel_preset.setCurrentIndex(current)

    def hideEvent(self, *args, **kwargs):
        Config().save()

    def showEvent(self, *args, **kwargs):
        pass  # ??? TODO: update renderer on_show

    def on_show_options(self):
        options = ExportOptionsDialog(self)
        options.exec_()

    def on_export_method_change(self, index, force=False):
        config = Config()
        if force or config.get_opt(Config.TEXSET_METHOD) != index:
            config.set_opt(Config.TEXSET_METHOD, index)
            if index:
                self._button_slots.setEnabled(False)
                self._sel_preset.setEnabled(True)
                self._radio_presets.setChecked(True)
            else:
                self._button_slots.setEnabled(True)
                self._sel_preset.setEnabled(False)
                self._radio_slots.setChecked(True)

    @staticmethod
    def on_preset_changed(index):
        current = Config().get_opt(Config.PRESET)
        if current != index:
            Config().set_opt(Config.PRESET, index)

    def get_preset(self):
        return self._presets[self._sel_preset.currentText()] if self._sel_preset.isEnabled() else None

    def on_set_path(self):
        filename, _ = QtGui.QFileDialog().getOpenFileName(self, caption='3D-Coat executable file location', dir='./')
        if filename:
            self._path_edit.set_text(QtCore.QDir.fromNativeSeparators(filename))
            self.reset_presets()
        return filename

    def on_set_exch(self):
        dirname = QtGui.QFileDialog().getExistingDirectory(self, caption='Exchange directory', dir='./')
        if dirname:
            self._exchange_edit.set_text(QtCore.QDir.fromNativeSeparators(dirname))
            Config().set_exchange()
            self.reset_presets()
        return dirname

    def on_export(self, *args):
        sender = self.sender()
        mode = sender.mode if sender else args[0]
        config = Config()

        # check if project location has changed
        config.set_project()

        # Get selected (meshes only)
        sel = self.get_selected()
        if not sel:
            return warning_msg('Please select polymesh objects and try again')

        shadersets = [(x, self.get_object_shaderset(x)) for x in sel]

        # check shading groups
        bad_sg = [x for x, (s, g) in shadersets if not g]
        if bad_sg:
            pmc.select(bad_sg)
            return warning_msg('Selected objects don\'t have shading groups')

        # sg has multiple shaders
        bad_shaders = [x for x, (s, g) in shadersets if len(s) != 1]
        if bad_shaders:
            pmc.select(bad_shaders)
            return warning_msg('Selected objects have multiple shaders connected to shading group')

        bad_shaders = [x for x, (s, g) in shadersets if not Renderer.shader_exists(s[0])]
        if bad_shaders:
            pmc.select(bad_shaders)
            return warning_msg('Selected objects are connected to unsupported shader')

        # check default shader
        bad_shaders = [g for x, (s, g) in shadersets if g == Renderer.INITIAL_SG]
        if bad_shaders:
            warning_msg('Default shading material will be replaced with a new phong shader.')
            for sg in bad_shaders:
                _, new_sg = pmc.createSurfaceShader('phong', name='Default')
                Renderer.reassign_sg(sg, new_sg)

        remapped = self.remap_shadersets(shadersets)

        export_mode = self.EXPORT_MODES[mode]
        info_msg('Export mode %s' % export_mode)

        self.fix_namespace_clashing()

        undo_state = pmc.undoInfo(q=True, st=True)
        pmc.undoInfo(swf=False)

        objpath = config.maya_project_coat + 'export.obj'
        pmc.exportSelected(objpath, typ='OBJexport', f=1, pr=1, es=1, op=self.OBJ_EXPORT_FLAGS)

        pmc.undoInfo(swf=undo_state)
        self.undo_remap_shadersets(remapped)

        # write information to file
        with open(config.text_export_path, 'w') as f:
            f.write('%s\n%s\n%s\n' % (objpath, objpath, export_mode))
            f.write(config.get_options_dump())

        if self.is_coat_running():  # don't run 3d-coat, if it's already running.
            return

        # need to run it
        if not config.get_coat_path():
            res = warning_dialog('The path to 3D-Coat is not specified yet.', 'Would you like to set it right now?')
            if not res:
                return

            if not self.on_set_path():
                return

        subprocess.Popen([config.get_coat_path()])  # run 3dcoat

    def on_import(self):
        config = Config()
        info = config.get_import_info()
        if not info:
            return warning_msg('No information for processing import')

        self.fix_namespace_clashing()

        undo_state = pmc.undoInfo(q=True, st=True)
        pmc.undoInfo(swf=False)

        preset = self.get_preset()
        shader = self._shader.current_text()

        # process import
        for obj_path, obj_cgs in info.items():
            mtl_path = obj_path.rstrip('.obj') + '.mtl'
            self.prune_mtl(mtl_path)

            try:
                pmc.importFile(obj_path, typ='OBJ', ra=1, op='mo=1', pr=1, mnc=1, ns='coat', lrd='all')
            except:
                warning_msg('Cannot import obj file: %s' % obj_path)
                return pmc.undoInfo(swf=undo_state)
            finally:
                [try_do(os.remove, x) for x in (mtl_path, obj_path)]  # delete import files

            for old_sg, imp_sg in self.get_sg_pairs(self.NAMESPACE):
                old_obj, imp_obj = [self.get_sg_object(x) for x in (old_sg, imp_sg)]

                if old_sg:
                    Renderer.create_shading_network(old_sg, obj_cgs[old_sg.name()], shader, preset)

                    if old_obj and imp_obj:
                        self.restore_transforms(imp_obj, old_obj)

                        if config.get_opt(Config.REPL_SHAPE):
                            Renderer.reassign_sg(imp_sg, old_sg)
                            Renderer.cleanup_shading_network(imp_sg)
                            pmc.delete((old_obj, imp_sg))
                            imp_obj.rename(imp_obj.lstrip(self.NAMESPACE))
                        else:
                            self.copy_mesh(imp_obj, old_obj)
                            Renderer.reassign_sg(old_sg, old_sg)
                            Renderer.cleanup_shading_network(imp_sg)
                            pmc.delete((imp_obj, imp_sg))
                    else:
                        self.reset_transforms_for_imported(imp_obj)
                        imp_obj.rename(imp_obj.lstrip(self.NAMESPACE))
                        Renderer.reassign_sg(imp_sg, old_sg)
                        Renderer.cleanup_shading_network(imp_sg)
                        pmc.delete(imp_sg)

                else:
                    Renderer.create_shading_network(imp_sg, obj_cgs[imp_sg.name()], shader, preset)
                    self.reset_transforms_for_imported(imp_obj)
                    imp_obj.rename(imp_obj.lstrip(self.NAMESPACE))

        # clear selection
        pmc.undoInfo(swf=undo_state)
        pmc.select(cl=1)


class CoatExportCmd(ompx.MPxCommand):
    """ Export command """
    NAME = 'coatExport'

    def __init__(self):
        ompx.MPxCommand.__init__(self)

    def doIt(self, args):
        """ doIt(int iMode[0:11]) """
        try:
            export_mode = args.asInt(0)
        except RuntimeError:
            return warning_msg('Invalid index for export mode. Must be an integer number')

        if not (0 <= export_mode < len(Tool.EXPORT_MODES)):
            return warning_msg('Unknown export mode <%s>' % export_mode)

        TOOL.on_export(export_mode)


class CoatImportCmd(ompx.MPxCommand):
    NAME = 'coatImport'

    def __init__(self):
        ompx.MPxCommand.__init__(self)

    def doIt(*args, **kwargs):
        TOOL.on_import()


class CoatUICmd(ompx.MPxCommand):
    NAME = 'coatUI'

    def __init__(self):
        ompx.MPxCommand.__init__(self)

    def doIt(*args, **kwargs):
        TOOL.show()


def initializePlugin(mobject):
    def reg_cmd(klass):
        def make_ptr():
            return ompx.asMPxPtr(klass())

        try:
            mplugin.registerCommand(klass.NAME, make_ptr)
        except:
            error_msg('Registration failed for <%s> command.' % klass.NAME)

    mplugin = ompx.MFnPlugin(mobject, '3dcoat', PLUGIN_VERSION, 'Any')

    # register command
    reg_cmd(CoatExportCmd)
    reg_cmd(CoatImportCmd)
    reg_cmd(CoatUICmd)

    # ensure that obj plugin is loaded
    pmc.loadPlugin('objExport.mll', qt=True)

    info_msg('3dcoat connector successfully loaded.')


def uninitializePlugin(mobject):
    def dereg_cmd(klass):
        try:
            mplugin.deregisterCommand(klass.NAME)
        except:
            error_msg('Deregistration failed for <%s> command.' % klass.NAME)

    mplugin = ompx.MFnPlugin(mobject)

    # unregister command
    dereg_cmd(CoatExportCmd)
    dereg_cmd(CoatImportCmd)
    dereg_cmd(CoatUICmd)

    TOOL.close()

    info_msg('3dcoat connector successfully unloaded.')


TOOL = Tool()
