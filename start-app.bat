@echo off
title Lancement de l'Extracteur Video (PyAV)
:: On se place dans le dossier du script
cd /d "%~dp0"

:: Verification de l'existence du venv
if not exist venv (
    echo [ERREUR] Environnement virtuel 'venv' non detecte.
    echo Creation du venv en cours...
    python -m venv venv
)

:: Activation du venv
echo Activation de l'environnement virtuel...
call venv\Scripts\activate

:: Installation des dépendances (au cas où elles manquent)
echo Verification des modules requis (av, gradio, pillow)...
pip install av gradio pillow

:: Lancement du script
echo Lancement de Gradio...
app-video-frame_PyAV.py

pause