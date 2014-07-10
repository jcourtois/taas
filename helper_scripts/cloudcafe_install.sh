#!/bin/sh
sudo apt-get update
sudo apt-get install -y git make python-pip vim

git clone https://github.com/jcourtois/taas.git ~/taas
sudo pip install virtualenv

wget https://www.python.org/ftp/python/2.7.8/Python-2.7.8.tar.xz ~/.
tar -xf ~/Python-2.7.8.tar.xz
cd ~/Python-2.7.8
./configure --prefix /usr/local/bin/python-2.7.8
make && sudo make install
cd ~ && rm -rf Python-2.7.8*

virtualenv -p /usr/local/bin/python-2.7.8/bin/python ./.venv
source ~/taas/.venv/bin/activate

sudo git clone https://github.com/stackforge/opencafe.git /opt/opencafe
sudo git clone https://github.com/stackforge/cloudcafe.git /opt/cloudcafe
sudo git clone https://github.com/stackforge/cloudroast.git /opt/cloudroast

sudo pip install --upgrade /opt/opencafe
sudo pip install --upgrade /opt/cloudcafe
sudo pip install --upgrade /opt/cloudroast
