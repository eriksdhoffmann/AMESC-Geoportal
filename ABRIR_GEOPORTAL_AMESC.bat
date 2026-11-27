@echo off
title Geoportal Regional da AMESC (15 Municipios)
start "" "http://localhost:8770/index.html"
python -m http.server 8770 --directory "%~dp0"
