#!/bin/sh

python txbra_calendar.py
git commit -m "updated" ics/*
git push origin master
