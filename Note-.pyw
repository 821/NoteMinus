import sys,re,os,shutil,datetime,simplenote
from PyQt4.QtGui import *; from PyQt4.QtWebKit import QWebView,QWebPage; from PyQt4.QtCore import Qt,QObject
from conf import * # import settings

# convinience functions
outpath = lambda inpath: outfolder + os.path.basename(inpath) + '.html'
crListItem = lambda: listWidget.currentItem().text()
crTabWidget = lambda: tabWidget.currentWidget()
lastbackup = lambda: os.path.join(zipfolder, max(os.listdir(zipfolder)))
def alldo(func, list):
	for v in list:
		func(v)
# add item to listWidget with format
def add2List(name):
	lItem = QListWidgetItem(name)
	lItem.setBackgroundColor(QColor('black'))
	lItem.setTextColor(QColor('white'))
	lItem.setFont(QFont('serif', 14))
	listWidget.addItem(lItem)
# check existence and create
def foldercreate(path):
	folderexist = os.path.isdir(path)
	if folderexist == False:
		os.mkdir(path)
# create buttons with function and geometry
def pushButton(text, tooltip, func, key):
	button = QPushButton(text)
	button.clicked.connect(func)
	button.setToolTip(tooltip)
	buttonLayout.addWidget(button)
	QShortcut(QKeySequence(key), widget, func)

# open the list
def initialize():
	listWidget.clear()
	global filedict
	alldo(add2List, ['All Notes', 'Style'])
	filedict = {'All Notes': listfile, 'Style': cssjs}
	with open(listfile, 'r', encoding='utf-8') as f:
		for i in f.read().splitlines():
			j = i.split('    ')
			filedict[j[0]] = os.path.normpath(j[1])
			if j[0] != 'MMB':
				add2List(j[0])

# viewing related
def view(name):
	with open(outpath(filedict[name]), 'r', encoding='utf-8') as visit:
		tabWidget.setTabText(tabWidget.currentIndex(), name)
		crTabWidget().setHtml(visit.read())
def newtab():
	tabWidget.addNewTab()
	view(crListItem())

# generate from input files
html = lambda infile, informat: os.system(pandoc + ' ' + infile + ' -f ' + informat + ' -t html --highlight-style=pygments -H ' + cssjs + ' -s -o ' + outpath(infile))
def generate(itempath):
	if itempath[-2:] == 'md' or itempath[-3:] == 'txt':
		html(itempath, 'markdown_github')
	elif itempath[-7:] == 'textile':
		html(itempath, 'textile')
	elif itempath[-3:] == 'tex':
		html(itempath, 'latex')
	elif itempath[-3:] == 'rst':
		html(itempath, 'rst')
	elif itempath[-3:] == 'org':
		html(itempath, 'org')
	else:
		html(itempath, 'html')
def regenerate():
	generate(filedict[crListItem()])
	view(crListItem())
def refresh():
	generate(filedict[tabWidget.tabText(tabWidget.currentIndex())])
	view(tabWidget.tabText(tabWidget.currentIndex()))

# edit selected item and the item being viewed
edit = lambda path: os.system(te + ' ' + path)

# backup
zip = lambda path: os.system(szip + ' a ' + os.path.join(zipfolder, backuptime + '.zip') + ' -p' + password + ' ' + path)
unzip = lambda path: os.system(szip + ' x ' + lastbackup() + ' -o' + os.path.dirname(path) + ' ' + os.path.basename(path) + ' -p' + password + ' -y')
def zipall():
	global backuptime
	backuptime = datetime.datetime.now().strftime("%y%m%d%H%M%S")
	alldo(zip, filedict.values())
ftp = lambda path: os.system(WinSCP + ' /command "open ' + server + '" "put ' + path + ' ' + upfolder + '" "exit"')
def ftpall():
	zipall()
	ftp(lastbackup())
def snote(name):
	sn = simplenote.Simplenote(snname, snpwd)
	snkey = {}
	with open(snkeylist, 'r', encoding='utf-8') as snkl:
		if os.stat(snkeylist).st_size != 0:
			for line in snkl.read().splitlines():
				j = line.split('    ')
				snkey[j[0]] = j[1]
	with open(filedict[name], 'r', encoding='utf-8') as f:
		note = {'content': f.read(), 'tags': name}
		if name in snkey:
			note['key'] = snkey[name]
			sn.update_note(note)
		else:
			snret = sn.add_note(note)
			with open(snkeylist, 'a', encoding='utf-8') as snkl:
				snkl.write('\n' + name + '    ' + snret[0]['key'])

# find next
findnext = lambda: crTabWidget().focusNextChild(crTabWidget().findText(blineEdit.text()))
def finds(func, arg):
	global founditems, foundindex, findtext
	if findtext != llineEdit.text(): # new search words
		initialize() # clear previous highlights
		foundindex = 0; founditems = []; findtext = llineEdit.text() # reset variables
		founditems = func(arg)
		alldo(lambda i: i.setBackgroundColor(QColor('blue')), founditems)
		listWidget.setCurrentItem(founditems[0]) # select the first result
	else: # get next result of the last search
		if foundindex == len(founditems) - 1:
			foundindex = 0
		else:
			foundindex += 1
		listWidget.setCurrentItem(founditems[foundindex])
def byname(text):
	return listWidget.findItems(text, Qt.MatchFlag(16) and Qt.MatchFlag(1)) # 1: partial search, 4:regex, 16: case insensitive
def bycontent(text):
	for index in range(listWidget.count()):
		if open(filedict[listWidget.item(index).text()], 'r', encoding='utf-8').read().find(text) != -1:
			founditems.append(listWidget.item(index))
	return founditems

# apply some changes to QTabWidget
class TabWidget(QTabWidget):
	def __init__(self, parent=None):
		super (TabWidget, self).__init__(parent)
		self.setTabsClosable(True)
		self.tabCloseRequested.connect(self.closeTab)
		self.setMovable(True)
		self.addNewTab()
	def closeTab(self, index):
		self.last_closed_doc = self.widget(index)
		self.removeTab(index)
	def addNewTab(self, title = 'Untitled'):
		self.insertTab(0, QWebView(), title)
		self.setCurrentIndex(0)

# start here
findtext = ''
alldo(foldercreate, [outfolder, zipfolder])
app = QApplication(sys.argv)
widget = QWidget()
widget.setWindowTitle('Note-')
widget.setWindowIcon(QIcon(widget.style().standardIcon(QStyle.SP_DialogSaveButton)))
buttonLayout = QHBoxLayout()
rightHalf = QVBoxLayout()
fullLayout = QHBoxLayout()
tabWidget = TabWidget()
listWidget = QListWidget()
listWidget.setFixedWidth(150)
llineEdit, blineEdit = QLineEdit(), QLineEdit()
pushButton('List C+F1', 'Reload the list', initialize, Qt.CTRL + Qt.Key_F1)
pushButton('Find F1', 'Find the string in given names', lambda: finds(byname, llineEdit.text()), Qt.Key_F1)
pushButton('FIF F2', 'Find the string in files', lambda: finds(bycontent, llineEdit.text()), Qt.Key_F2)
buttonLayout.addWidget(llineEdit)
pushButton('View F3', 'View selected item', lambda: view(crListItem()), Qt.Key_F3)
pushButton('Tab F4', 'View in a new tab', newtab, Qt.Key_F4)
pushButton('F5', 'Regenerate currently viewing item', refresh, Qt.Key_F5)
pushButton('Conv F6', 'Generate selected item to HTML', regenerate, Qt.Key_F6)
pushButton('CA C+F6', 'Generate all items to HTML', lambda:alldo(generate, filedict.values()), Qt.CTRL + Qt.Key_F6)
pushButton('Edit F7', 'Edit selected item', lambda: edit(filedict[crListItem()]), Qt.Key_F7)
pushButton('ET F8', 'Edit item in current tab', lambda: edit(filedict[tabWidget.tabText(tabWidget.currentIndex())]), Qt.Key_F8)
pushButton('FTP F9', 'Upload selected item to FTP/WebDAV', lambda: ftp(filedict[crListItem()]), Qt.Key_F9)
pushButton('FA C+F9', 'Pack all items with password and upload to FTP/WebDAV', ftpall, Qt.CTRL + Qt.Key_F9)
pushButton('SNote F10', 'Backup selected item to SimpleNote', lambda:snote(crListItem()), Qt.Key_F10)
pushButton('Pack F11', 'Pack all items with password', zipall, Qt.Key_F11)
pushButton('Restore C+F11', 'Restore selected item from the latest pack', lambda:unzip(filedict[crListItem()]), Qt.CTRL + Qt.Key_F11)
buttonLayout.addWidget(blineEdit)
pushButton('Find Next F12', 'Find string in currently viewing item', findnext, Qt.Key_F12)
rightHalf.addWidget(tabWidget)
rightHalf.addLayout(buttonLayout)
fullLayout.addWidget(listWidget)
fullLayout.addLayout(rightHalf)
widget.setLayout(fullLayout)
screen = QDesktopWidget().screenGeometry()
widget.setGeometry(0, 70, screen.width(), screen.height()-100)
initialize()
widget.show()
app.exec_()
