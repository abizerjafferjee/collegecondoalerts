#!/bin/sh
sudo apt install virtualenv
virtualenv cca
source cca/bin/activate
pip install -r requirements.txt