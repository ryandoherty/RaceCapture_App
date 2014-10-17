class AppConfig(object):
    userDir = "."
    
    def setUserDir(self, userDir):
        print('using user storage directory: ' + userDir)
        self.userDir = userDir
        pass
