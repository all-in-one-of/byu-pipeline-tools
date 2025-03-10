# Created by a lot of people

import maya.cmds as mc
import os
import shutil
from pymel.core import *

import byuam.pipeline_io as pio
from byuam.environment import Environment
from byuam.body import AssetType
from byuam.project import Project
from byugui import message_gui
import reference_selection as rs

def abcExport(selected, path):
	if not os.path.exists(path):
		os.makedirs(path)

	abcfiles = []

	loadPlugin('AbcExport')
	for geo in selected:
		chop = geo.rfind('|')
		parent_geo = geo[:chop]
		abcFile = geo[(chop+1):]
		abcFile = formatFilename(abcFile) + '.abc'
		abcFilePath = os.path.join(path, abcFile)
		print abcFilePath
		command = 'AbcExport -j "-frameRange 1 1 -stripNamespaces -root '+parent_geo+' -nn -uv -as -file '+abcFilePath+'";'
		print command
		Mel.eval(command)
		abcfiles.append(abcFilePath)

	return abcfiles

def abcExportLoadedReferences(path):
	if not os.path.exists(path):
		os.makedirs(path)

	abcfiles = []

	loadPlugin('AbcExport')
	loadedRefs = rs.getLoadedReferences()
	for i, ref in enumerate(loadedRefs):
		print ref
		refNodes = mc.referenceQuery(unicode(ref), nodes=True)
		rootNode = ls(refNodes[0])
		roots_string = ''
		#TODO check if the root has been tagged
		# if not check to see if its children have been tagged
		# At this point we have a node that is ready for export
		for alem_obj in rootNode:
			roots_string += (' -root %s'%(alem_obj))

		print 'roots_string: ' + roots_string

		abcFile = formatFilename(ref) + '.abc'
		abcFilePath = os.path.join(path, abcFile)
		print 'The file path: ' + str(abcFilePath)
		command = 'AbcExport -j "%s -frameRange 1 1 -stripNamespaces -writeVisibility -noNormals -uvWrite -worldSpace -autoSubd -file %s"'%(roots_string, abcFilePath)
		print 'The command: ' + command
		Mel.eval(command)
		print 'Export successful! ' + str(i) + ' of ' + str(len(loadedRefs))
		abcfiles.append(abcFilePath)

	print 'all exports complete'
	return abcfiles

def abcExportAll(name, path):
	if not os.path.exists(path):
		os.makedirs(path)

	abcFile = name + '.abc'
	abcFilePath = os.path.join(path, abcFile)

	loadPlugin('AbcExport')

	command = 'AbcExport -j "-stripNamespaces -writeVisibility -noNormals -uvWrite -worldSpace -autoSubd -file ' + abcFilePath + '";'
	Mel.eval(command)

	abcFiles = []

	abcFiles.append(abcFilePath)

	return abcFiles

def formatFilename(filename):
	filename = filename.replace('Shape', '')
	filename = filename.replace('RN', '')
	filename = pio.alphanumeric(filename)
	return filename

def checkFiles(files):
	'''
		Checks the list of output files against which files were actually created

		@param: files - a list of strings representing full paths

		@return: a list of paths to files that do not exist
	'''

	missingFiles = []

	for filename in files:
		print 'CHECKING********** ' + filename
		if not os.path.exists(filename):
			missingFiles.append(filename)

	if not len(missingFiles) == 0:
		errorMessage = ''
		for f in missingFiles:
			errorMessage += 'MISSING FILE: ' + f + '\n'
		print(errorMessage)
		errorMessage = str(len(missingFiles)) + ' Files Missing:\n\n' + errorMessage
		#mc.confirmDialog(title='Error exporting files', message=errorMessage)
		#ui.infoWindow(errorMessage, wtitle='Error exporting files', msev=messageSeverity.Error)

	return missingFiles

def getElementCacheDirectory(path, element=None):

	if element is None:
		proj = Project()
		checkout = proj.get_checkout(path)
		if checkout is None:
			message_gui.error('There was a problem exporting the alembic to the correct location. Checkout the asset again and try one more time.')
			return None
		body = proj.get_body(checkout.get_body_name())
		element = body.get_element(checkout.get_department_name(), checkout.get_element_name())

	return element.get_cache_dir()

def installGeometry(path='',element=None):

	'''
		Function to install the geometry into the PRODUCTION asset directory

		@return: True if the files were moved successfully
		@throws: a shutil exception if the move failed
	'''

	print 'install newly created geo in files'
	path=os.path.dirname(mc.file(q=True, sceneName=True))

	#srcOBJ = os.path.join(path, 'cache', 'objFiles')
	#destOBJ = os.path.join(os.environ['ASSETS_DIR'], assetName, 'cache', 'objFiles')
	#destABC = os.path.join(os.environ['ASSETS_DIR'], assetName, 'cache', 'abcFiles')

	srcABC = os.path.join(path, 'cache', 'abcFiles')
	destABC = getElementCacheDirectory(path, element)
	if destABC is None:
		return False

	#if os.path.exists(destOBJ):
	#	shutil.rmtree(destOBJ)
	if os.path.exists(destABC):
		try:
			shutil.rmtree(destABC)
		except Exception as e:
			print 'Couldn\'t delete old abc files:'
			print e

	#print 'Copying '+srcOBJ+' to '+destOBJ
	#try:
	#	os.system('chmod 774 -R ' + srcOBJ)
	#	shutil.copytree(srcOBJ, destOBJ)
	#	os.system('chmod 774 -R '+ destOBJ)
	#except Exception as e:
	#	print e

	#treat alembic special so we don't mess up concurrent houdini reading . . .
	srcABC = os.path.join(srcABC, '*');
	if not os.path.exists(destABC):
		os.mkdir(destABC);
		os.system('chmod 774 -R ' + destABC)

	print 'Copying '+srcABC+' to '+destABC
	try:
		os.system('chmod 774 -R '+srcABC)
		result = os.system('mv -f '+srcABC+' '+destABC)
		print result
		# shutil.copytree(src=srcABC, dst=destABC)
	except Exception as e:
		print 'Couldn\'t copy newly generated abc files:'
		print e

	print 'Removing '+os.path.join(path, 'cache')
	shutil.rmtree(os.path.join(path, 'cache'))

	return True

def generateGeometry(path='',element=None):
	'''

		Function for generating geometry for Maya files.

		Creates the following output formats:
			.obj

		@return: True if all files were created successfully
				False if some files were not created

		@post: Missing filenames are printed out to both the Maya terminal as well
				as presented in a Maya confirm dialog.
	'''

	path = os.path.dirname(mc.file(q=True, sceneName=True))
	print 'generateGeometry start'
	if not os.path.exists (os.path.join(path, 'cache')):
		os.makedirs(os.path.join(path, 'cache'))

	#OBJPATH = os.path.join(path, 'cache', 'objFiles')
	ABCPATH = os.path.join(path, 'cache', 'abcFiles')

	#if os.path.exists(OBJPATH):
	#	shutil.rmtree(OBJPATH)
	if os.path.exists(ABCPATH):
		shutil.rmtree(ABCPATH)

	filePath = cmds.file(q=True, sceneName=True)
	fileDir = os.path.dirname(filePath)
	print 'This is the fileDir in question: ', fileDir

	abcFilePath = getElementCacheDirectory(fileDir, element)
	if abcFilePath is None:
		return False

	selection = mc.ls(geometry=True, visible=True)
	selection_long = mc.ls(geometry=True, visible=True, long=True)

	# Temporarily disabled obj support (might not be needed)
	#objs = objExport(selection, OBJPATH)

	# Check to see if all .obj files were created
	#if not len(checkFiles(objs)) == 0:
	#	return False
	proj = Project()
	if element is None:
		checkout = proj.get_checkout(path)
		if checkout is None:
			message_gui.error('There was a problem exporting the alembic to the correct location. Checkout the asset again and try one more time.')
			return None
		body = proj.get_body(checkout.get_body_name())
		element = body.get_element(checkout.get_department_name(), checkout.get_element_name())
	else:
		body = proj.get_body(element.get_parent())

	# We decided to try exporting all the geo into one alembic file instead of many. This is the line that does many
	# abcs = abcExport(selection_long, ABCPATH)
	if body.is_asset():
		if body.get_type() == AssetType.SET:
			abcs = abcExportLoadedReferences(ABCPATH)
		else:
			abcs = abcExportAll(element.get_long_name(), ABCPATH)
	else:
		abcs = abcExportAll(element.get_long_name(), ABCPATH)
	print str(body.is_asset()) + ' it is an asset'
	print 'The type is ' + body.get_type()
	if not len(checkFiles(abcs)) == 0:
		return False

	return True

def go(element=None):
	if generateGeometry(element=element):
		installGeometry(element=element)

if __name__ == '__main__':
	# Uncomment this line if you want to read in a new destination from
	# command line. Intended to be a new destination for files to go.
	#dest = sys.argv[1]
	go()
