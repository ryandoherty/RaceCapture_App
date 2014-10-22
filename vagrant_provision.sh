#!/bin/bash

set -e

# just fuck ubuntu
export DEBIAN_FRONTEND=noninteractive

sudo -E add-apt-repository ppa:kivy-team/kivy
sudo -E apt-get update

## RCP/kivy deps
sudo -E apt-get install -y python-kivy python-virtualenv 

## install gnome desktop
sudo -E apt-get install -y xinit jwm
sudo -E apt-get install -y xorg gnome-core gnome-system-tools gnome-app-install 

sudo -E apt-get install -y linux-headers-3.13.0-37-generic linux-image-extra-virtual

## enable automatic login for Vagrant user
sudo -E sed -i -e '/AutomaticLoginEnable =/c\AutomaticLoginEnable = true' /etc/gdm/custom.conf
sudo -E sed -i -e '/AutomaticLogin =/c\AutomaticLogin = vagrant' /etc/gdm/custom.conf


ve_path=$HOME/devel/venv/kivy
virtualenv --system-site-packages ${ve_path}
. ${ve_path}/bin/activate

pip install https://github.com/Jeff-Ciesielski/ihexpy/archive/master.zip
pip install -r /vagrant/requirements.txt
pip install /vagrant/dependencies/asl_f4_loader-0.0.5.tar.gz

mkdir ~/.config

## ABANDONED ## sudo -E apt-get install -y xinit jwm
## ABANDONED ## 
## ABANDONED ## ## allow "startx" after "vagrant ssh"
## ABANDONED ## sudo -E sed -i -e 's#console#anybody#' /etc/X11/Xwrapper.config
## ABANDONED ## 
## ABANDONED ## >| ~/.xinitrc
## ABANDONED ## echo '#!/bin/bash' >> ~/.xinitrc
## ABANDONED ## echo 'export LANG="en_US.UTF-8"' >> ~/.xinitrc
## ABANDONED ## echo 'export LC_ALL=$LANG' >> ~/.xinitrc
## ABANDONED ## echo 'export LANGUAGE=$LANG' >> ~/.xinitrc
## ABANDONED ## echo 'export LC_CTYPE=$LANG' >> ~/.xinitrc
## ABANDONED ## 
## ABANDONED ## echo ". ${ve_path}/bin/activate" >> ~/.xinitrc
## ABANDONED ## 
## ABANDONED ## echo 'x-terminal-emulator &' >> ~/.xinitrc
## ABANDONED ## echo '(cd /vagrant && python racecapture.py ) &' >> ~/.xinitrc
## ABANDONED ## echo 'exec x-window-manager' >> ~/.xinitrc
## ABANDONED ## 
## ABANDONED ## chmod +x ~/.xinitrc

echo "SUCCESS!"
echo "you must now 'vagrant reload'"
