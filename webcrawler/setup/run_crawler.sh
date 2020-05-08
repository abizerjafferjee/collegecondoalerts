#!/bin/bash
cd /home/abizer/collegecondoalerts/webcrawler
PATH=$PATH:/home/abizer/.local/bin
export PATH
scrapy crawl places4students
#echo "Hello"
