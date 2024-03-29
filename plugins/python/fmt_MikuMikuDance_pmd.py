# Modified from: https://github.com/atrzaska/noesis_py/blob/master/lib/plugins/fmt_MikuMikuDance_pmd.py
# (Latest commit 08a638a on Nov 23, 2017)
# *Update 2022/08/13: Merge library
# *Update 2022/07/19: Rotate model to front, and fix textures not displaying

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''

    handle = noesis.register("Miku Miku Dance", ".pmd")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    return 1

def noepyLoadModel(data, mdlList):
    '''Load the model'''

    ctx = rapi.rpgCreateContext()
    parser = MikuMikuDance_PMD(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdlList.append(mdl)
    return 1

class MikuMikuDance_PMD(object):

    def __init__(self, data):
        self.inFile = NoeBitStream(data)
        self.matList = []
        self.texList = []
    
    def read_string(self, size):
        return self.inFile.readBytes(size)

    def read_name(self, n):

        string = self.inFile.readBytes(n)
        index = string.find(b"\x00")
        if index != -1:
            return string[0:index]
        return string

    def encode_utf8(self, string):

        return string.decode('shift_jis').encode('UTF-8')

    def parse_vertices(self, numVerts):

        vertBuff = self.inFile.readBytes(38*numVerts)
        
        # rotate model to front
        trans = NoeMat43((NoeVec3((1.0, 0.0, 0.0)), NoeVec3((0.0, 1.0, 0.0)), NoeVec3((0.0, 0.0, -1.0)), NoeVec3((0.0, 0.0, 0.0))))
        rapi.rpgSetTransform(trans)
        rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
        
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 38, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 38, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 38, 24)

    def parse_faces(self, numIdx):

        if numIdx % 3 == 0:
            return self.inFile.readBytes(2*numIdx)
        else:
            print("Quads")

    def parse_materials(self, numMat):

        matInfo = []
        for i in range(numMat):
            rgba = self.inFile.readBytes(16)
            shine = self.inFile.readFloat()
            specular = self.inFile.read('3f')
            ambient = self.inFile.read('3f')
            toon_tex = self.inFile.readUByte()
            toon_edge = self.inFile.readUByte()
            numIdx = self.inFile.readUInt()
            texName = self.read_name(20)
            print(texName)
            texNames = texName.split(b'*')
            print(texNames)
            spa = ''

            if len(texNames) > 1:
                texName = texNames[0]
                spa = texNames[1]

            matName = "material%d" %i
            material = NoeMaterial(matName, "")
            if texName:
                folderName = rapi.getDirForFilePath(rapi.getInputName())
                folderName = folderName.replace('\\', '/')
                material.setTexture(folderName + texName.decode(("utf-8")))
            else:
                color = NoeVec4.fromBytes(rgba)
                material.setDiffuseColor(color)
            self.matList.append(material)

            matInfo.append([matName, numIdx, rgba])
        return matInfo

    def assign_materials(self, idxBuff, matInfo):

        start = 0
        for mat in matInfo:
            matName = mat[0]
            numIdx = mat[1]
            end = start + numIdx*2
            buff = idxBuff[start:end]

            rapi.rpgSetMaterial(matName)

            rapi.rpgCommitTriangles(buff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
            start += numIdx*2

    def parse_file(self):

        idstring = self.read_string(3)
        version = self.inFile.readUInt()
        name = self.read_name(20)
        comment = self.read_name(256)

        numVerts = self.inFile.readUInt()
        self.parse_vertices(numVerts)

        numIdx = self.inFile.readUInt()
        idxBuff = self.parse_faces(numIdx)

        numMat = self.inFile.readUInt()
        matInfo = self.parse_materials(numMat)

        self.assign_materials(idxBuff, matInfo)
