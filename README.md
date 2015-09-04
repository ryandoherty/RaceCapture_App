RaceCapture App
===============

Next Gen version of the RaceCapture App.

Dependencies:
* Python 2.7.x
* Patched Kivy 1.9.x (https://github.com/autosportlabs/kivy/tree/asl_1.9.0_patched) 
* Pyserial 2.6.x
* Pygame
* Included in package right now but ultimately shouldn't be:
  * Graph (via kivy-garden via python-pip)
  * NavigationDrawer (via kivy-garden)
  * ModernMenu (via kivy-garden)
  * asl_f4_loader (in dependencies folder)
  * ihexpy (manual install from https://github.com/Jeff-Ciesielski/ihexpy )

## dev installation (OS X)

1. download patched 1.9.0 kivy from https://github.com/autosportlabs/kivy/tree/asl_1.9.0_patched 
1. Install from source
- > Instructions: http://kivy.org/docs/installation/installation-macosx.html
1. install [virtualenv](http://www.virtualenv.org)
1. create a virtual environment (perhaps in this directory): `virtualenv _ve`
1. activate the virtualenv: `. _ve/bin/activate`
1. install pip requirements: `pip install -r requirements.txt` (you may be required to upgrade your version of setuptools via the provided command)
1. install asl_f4_loader in dependencies folder: pip install asl_f4_loader-X.X.X.tar.gz
1. install pygame (http://www.pygame.org/download.shtml - use correct package for your OSX+Python version)

## Simplified dev install (OS X)
1. download patched 1.9.0 kivy from https://github.com/autosportlabs/kivy/tree/asl_1.9.0_patched 
1. Install from source
 * > make && sudo make install 
1. install Kivy into Applications and run symlink script
1. install [virtualenv](http://www.virtualenv.org)
1. re-enable setup tools for Kivy virtualenv: `sudo virtualenv /Applications/Kivy.app/Contents/Resources/venv/`
1. install pip requirements: `/Applications/Kivy.app/Contents/Resources/venv/bin/pip install -r requirements.txt`
1. run app: `kivy main.py`

## running (OS X)

    /Applications/Kivy.app/Contents/Resources/script main.py


## Building releases (all platforms)
1. Add a .sentry file with the app's platform-specific DSN for Sentry
1. Follow the platform-specific build instructions

## Preparing to build installers (OSX)

1. Make sure all dependencies are installed inside Kivy's venv 
1. `cd /Applications/Kivy.app/Contents/Resources/venv/bin` && `source activate`
1. `cd /path/to/RaceCapture_App` && `pip install -r requirements.txt`
1. If we're using a custom build of Kivy, we need to fix the paths for some libraries, run the install/osx/fix-osx-paths.sh script.


## Creating installer for current version (OSX)
1. `cd install/osx`
1. `./build-osx.sh`

The script will create the .App file and .dmg for distribution.

## installation (Win7)

1. Download [Kivy](http://kivy.org/#download) (current is 1.9.0) - remember to get the py2.7 version
1. Follow Kivy install instructions- install to c:\Kivy-1.9.0
1. Rename kivy27 to kivy27_original (move it out of the way)
1. Pull down patched 1.9.0 from https://github.com/autosportlabs/kivy/tree/asl_1.9.0_patched
 * Place in same installation directory (c:\Kivy-1.9.0)
 * Rename to kivy27
1. Build modified kivy
 * Launch kivy-bash-2.7.bat
 * In the MinGW console, enter kivy27 directory
 * Build by issuing 'make'
 * When complete, there should be a kivy27/build directory - this will be the patched version
1. `my_kivy_install_folder\kivy.bat` (sets path variables for current shell)
1. Install [virtualenv]: `pip install virtualenv`
1. Create a virtual environment (perhaps in this directory): `virtualenv _ve`
1. Activate the virtualenv: `_ve\Scripts\activate`
1. Install pip requirements: `pip install -r requirements.txt` (if this crashes you installed the py3.3 version of Kivy, doughball)

## running (Win7)

    Launch kivy environment by launching kivy-2.7.bat in installation folder
    Navigate to the RaceCapture source directory
    kivy main.py
	Note: If you get an error doing this ("cannot find text provider") then you might be like me and be unable to run RaceCapture inside a virtualenv for some reason. Try performing the above steps without the virtual env part.

## dev installation (Eclipse on Win7, but probably applies to Eclipse on any platform)

1. Do the "installation" instructions above
1. Download [Eclipse] (https://www.eclipse.org/downloads/)
1. Install [PyDev for Eclipse] (http://pydev.org/manual_101_install.html) and use auto-config
1. In Window..Preferences..PyDev..Interpreter..Python Interpreter..Environment, add a variable "PATH" with value c:\kivy;c:\kivy\Python;c:\kivy\gstreamer\bin;c:\kivy\MinGW\bin;%PATH%
1. In Window..Preferences..PyDev..Interpreter..Python Interpreter..Forced Builtins, add "kivy" to the list
1. Make a new project in Eclipse, select "PyDev project" and specify the folder with Racecapture in it
1. Right-click the project...Properties...pyDev-PYTHONPATH...External Libraries - Add source folder, add my_kivy_install_folder\kivy
1. Run the project

## Preparing to build installers (Win7)

1. `kivy` (to get paths set up)
1. activate the virtualenv: `_ve\Scripts\activate`
1. Install [PYInstaller] (http://www.pyinstaller.org) `pip install pyinstaller`
1. Install [PyWin32] (http://sourceforge.net/projects/pywin32/files/) `pip install pywin`
1. Try `pyinstaller --version` - should return "2.1" or similar
1. Install [nullsoft scriptable install system] (http://nsis.sourceforge.net/Download) stable version (currently 2.46)
1. Open (from your Kivy folder) `\Python27\Lib\site-packages\pygments\lexers\__init__.py` and add a line "from pygments.lexers.agile import PythonLexer" near the top. Yes, I know this is bad form. It's to fix an error ("AttributeError: 'module' object has no attribute 'PythonLexer'") where PyInstaller failed to find an import and I couldn't work out how to force it. You would think that this could be forced by creating a hook-pygments.lexers.py file with hiddenimports = ['agile'] in it, but you'd be wrong as this file already exists in the default PyInstaller hooks and it doesn't fix this problem. -CLR 2014-05-29

## Creating installer for current version (Win7)

1. Go into RaceCapture_App folder
1. Activate the virtualenv: `_ve\Scripts\activate`
1. `kivy` (to get paths set up)
1. cd install
1. `buildwininstall.bat` - deletes old build folders, builds installer and tries to run the package (to run manually use `dist\racecapture\racecapture`)

## dev installation (Linux - Ubuntu)

1. Download patched source from https://github.com/autosportlabs/kivy/tree/asl_1.9.0_patched
1. Install from source. From the downloaded kivy source execute:
* > sudo python setup.py install
1. install [virtualenv]: `sudo pip install virtualenv`
1. create a virtual environment (perhaps in this directory): `virtualenv _ve`
1. activate the virtualenv: `. _ve/bin/activate`
1. install pip requirements: `sudo pip install -r requirements.txt` (you may be required to upgrade your version of setuptools via the provided command)
1. install asl_f4_loader in dependencies folder: pip install asl_f4_loader-X.X.X.tar.gz

## running (Linux - Ubuntu)

    python main.py

## Buildozer android APK build/install (Linux only)

1. install buildozer from https://github.com/kivy/buildozer
1. from the root RaceCapture app directory, run ./build_apk.sh . buildozer will download files as necessary and build the apk
1. if buildozer fails with a cython error, install cython from your package manager
1. if buildozer fails with an Android SDK error, enter the ~/.buildozer directoy and run android update sdk -u from the android tools directory.

## Launch android apk
1. Ensure your android device is in developer mode and plug it in via usb
1. install / launch the app using ./launch_apk.sh
1. Console / debug output will appear on screen as app is downloaded, installed and run

