from kivy.logger import Logger
class AppConfig(object):
    userDir = "."
    
    def setUserDir(self, userDir):
        Logger.info('AppConfig: using user storage directory: {}'.format(userDir))
        self.userDir = userDir
        pass
