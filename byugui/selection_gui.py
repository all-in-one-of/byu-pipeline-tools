# Author: Ben DeMann
import sys
import os
try:
	from PySide import QtGui as QtWidgets
	from PySide import QtGui as QtGui
	from PySide import QtCore
except ImportError:
	from PySide2 import QtWidgets, QtGui, QtCore
from byuam.project import Project
from byuam.environment import Department, Environment


WINDOW_WIDTH = 650
WINDOW_HEIGHT = 600

class SelectionWindow(QtWidgets.QDialog):

	finished = QtCore.Signal()

	def __init__(self, parent, dept_list=Department.ALL, showWindow=True):
		super(SelectionWindow, self).__init__()
		self.parent = parent
		self.project = Project()
		self.environment = Environment()
		self.initUI(dept_list, showWindow)

	def initUI(self, dept_list, showWindow):
		#define gui elements
		self.resize(WINDOW_WIDTH,WINDOW_HEIGHT)
		self.setWindowTitle('Select Asset')
		self.dept_tabs = QtWidgets.QTabWidget()
		self.dept_list = dept_list
		self.result = None
		self.instructions = QtWidgets.QLabel('Select the asset you would like affect:')

		#create Tabs
		self.createTabs()

		#create buttons
		self.select_button = QtWidgets.QPushButton('Select')
		self.select_button.clicked.connect(self.select)
		self.cancel_button = QtWidgets.QPushButton('Cancel')
		self.cancel_button.clicked.connect(self.close)

		#create button layout
		button_layout = QtWidgets.QHBoxLayout()
		button_layout.addWidget(self.select_button)
		button_layout.addWidget(self.cancel_button)

		self.img = QtWidgets.QLabel()
		image_path = os.path.join(os.environ['BYU_TOOLS_DIR'], 'byugui', 'assets', 'images', 'film-banner.jpg')
		pixmap = QtGui.QPixmap(image_path)
		scaled = pixmap.scaledToWidth(self.size().width())
		self.img.setPixmap(scaled)

		#create main layout
		main_layout = QtWidgets.QVBoxLayout()
		self.setLayout(main_layout)
		main_layout.addWidget(self.img)
		main_layout.setSpacing(5)
		# main_layout.setMargin(6)
		main_layout.addWidget(self.instructions)
		main_layout.addWidget(self.dept_tabs)
		main_layout.addLayout(button_layout)

		if showWindow:
			self.show()

	def createTabs(self):
		#remember the current index so that we can restore it when we create the tabs
		currIndex = self.dept_tabs.currentIndex()
		#clear out the old tabs
		self.dept_tabs.clear()
		#create tabs
		for dept in self.dept_list:
			tab = DepartmentTab(self)
			self.dept_tabs.addTab(tab, dept)
			tab_layout = QtWidgets.QHBoxLayout()
			element_list = QtWidgets.QListWidget()

			if dept in Department.ASSET_DEPTS:
				for asset in self.project.list_assets():
					item = QtWidgets.QListWidgetItem(asset)
					element_list.addItem(item)
					element_list.currentItemChanged.connect(self.set_current_item)
			elif dept in Department.SHOT_DEPTS:
				for shot in self.project.list_shots():
					item = QtWidgets.QListWidgetItem(shot)
					element_list.addItem(item)
					element_list.currentItemChanged.connect(self.set_current_item)
			tab_layout.addWidget(element_list)
			tab.setLayout(tab_layout)

		#restore the previous index
		self.dept_tabs.setCurrentIndex(currIndex)

	def set_current_item(self, index):
		current_dept = self.dept_list[self.dept_tabs.currentIndex()]
		if current_dept in Department.ASSET_DEPTS:
			self.current_item = str(index.text())
		elif current_dept in Department.SHOT_DEPTS:
			self.current_item = str(index.text())

		asset_obj = self.project.get_body(self.current_item)
		element_obj = asset_obj.get_element(current_dept)
		last_publish = element_obj.get_last_publish()
		last_publish_comment = None
		if last_publish is not None:
			last_publish_comment = 'Last published {0} by {1} \n \"{2}\"'.format(last_publish[1], last_publish[0], last_publish[2])
		else:
			last_publish_comment = 'No publishes for this element'
		currentTab = self.dept_tabs.currentWidget()

	def hasPreviousPublish(self, body, department):
		asset_obj = self.project.get_body(body)
		element_obj = asset_obj.get_element(department)
		last_publish = element_obj.get_last_publish()
		if last_publish is None:
			return False
		return True

	def select(self):
		'''
		Selects the currently selected item
		:return:
		'''
		current_user = self.environment.get_current_username()
		current_dept = self.dept_list[self.dept_tabs.currentIndex()]

		asset_obj = self.project.get_body(self.current_item)
		element_obj = asset_obj.get_element(current_dept)
		if element_obj != None:
			self.result = element_obj
			self.close()

	def closeEvent(self, event):
		self.finished.emit()
		event.accept()

def getSelectedElement(parent, deptList=Department.ALL):
	window = SelectionWindow(parent, dept_list=deptList, showWindow=False)
	help(window)
	window.exec_()
	return window.result

class DepartmentTab(QtWidgets.QWidget):
	def __init__(self, parent):
		super(DepartmentTab, self).__init__()
		self.parent = parent

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	ex = SelectionWindow(app)
	sys.exit(app.exec_())
