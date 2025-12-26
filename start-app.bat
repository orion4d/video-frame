@echo off
title Lancement de l'Extracteur Video
:: On se place dans le dossier du script
cd /d "%~dp0"

:: Verification de l'existence du venv
if not exist venv (
    echo [ERREUR] Environnement virtuel 'venv' non detecte.
    pause
    exit
)

:: Activation du venv et lancement du script
echo Activation de l'environnement virtuel...
call venv\Scripts\activate
echo Lancement de Gradio...
python app-video-frame.py
pause