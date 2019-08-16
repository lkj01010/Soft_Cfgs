import shutil
import ma_workflow.fbx_utils as fu
import ma_workflow.com as com


# def run_export_ani():
#     full, dir, name = com.get_scene_name()
#     name += '.fbx'
#     fu.export_fbx_ani_bip(kDir + name)
#     shutil.copy(kDir + name, kCutVerDir + com.cut_ver_string(name))
#
#
# def run_export_model():
#     full, dir, name = com.get_scene_name()
#     name += '.fbx'
#     fu.export_fbx_model(kDir + name)
#     shutil.copy(kDir + name, kCutVerDir + com.cut_ver_string(name))


def run_export(dir, cut_ver_dir):
    full, dirname, filename = com.get_scene_name()
    filename += '.fbx'

    final = dir + filename
    if filename.find('@') != -1:
        fu.export_fbx_ani_bip(final)
    else:
        fu.export_fbx_model(final)

    filename_no_ver = com.cut_ver_string(filename)
    final_no_ver = cut_ver_dir + filename_no_ver
    shutil.copy(final, final_no_ver)

    print 'finish ------>    ' + filename + '    ' + filename_no_ver

# kDir = '/Users/Midstream/Documents/Temp/testConvert/out/'
# kCutVerDir = '/Users/Midstream/Documents/Temp/testConvert/cut/'

# run_export(kDir, kCutVerDir)
