# 🎬 Video Frame Extractor Pro (PyAV Engine)

Un outil professionnel basé sur **Python 3.12**, **Gradio** et **PyAV** conçu pour extraire des images de vidéos (MP4, MKV, AVI, etc.) avec une vitesse fulgurante et une précision chirurgicale.

<img width="1635" height="1281" alt="image" src="https://github.com/user-attachments/assets/ff682a73-3be5-4151-b7ff-db7e421beaae" />
<img width="1850" height="947" alt="image" src="https://github.com/user-attachments/assets/33cdd50d-78e5-4642-832b-d0f75d026cc3" />

## 🚀 Caractéristiques principales

* **Moteur Turbo PyAV** : Utilise les bindings directs FFmpeg (PyAV) pour une extraction **séquentielle ultra-rapide**, éliminant les lenteurs des méthodes traditionnelles (CLI).
* **Extraction Intelligente** : Ne décode que les images nécessaires via une lecture séquentielle du flux. Support du **PNG optimisé** (compression rapide) et du **JPG** haute qualité.
* **Précision "Frame-Perfect"** : Navigation et extraction basées sur le *Presentation Timestamp* (PTS) pour garantir que l'image extraite correspond exactement au moment voulu.
* **Synchronisation en Temps Réel** : Lecteur vidéo synchronisé avec un curseur haute précision et génération d'aperçus fluides.
* **Auto-Détection** : Analyse automatique de la durée et du FPS réel de la vidéo à l'importation.
* **Mode Hybride FPS/Intervalle** : 
    * Saisie manuelle ou automatique du FPS (ex: 24 pour capturer chaque frame d'un film).
    * Basculement vers un mode "Intervalle en secondes" pour des captures espacées.
* **Gestion de Sessions** : Organisation automatique des extractions dans des sous-dossiers horodatés.

## 🛠️ Installation

### 1. Prérequis
* **Python 3.12** (ou supérieur).
* Pas besoin d'installer FFmpeg manuellement : le moteur PyAV inclut ses propres binaires optimisés.

### 2. Configuration de l'environnement
Ouvrez un terminal dans le dossier du projet :

### Création de l'environnement virtuel
`python -m venv venv`

### Activation (Windows)
`venv\Scripts\activate`

### Installation des dépendances (PyAV, Gradio, Pillow)
`pip install gradio av pillow`

## 🚦 Lancement

Vous pouvez lancer l'application de deux manières :

1.  **Via le script Windows** : Double-cliquez sur `start-app.bat`.
2.  **Via le terminal dans le dossier du venv** : `venv\Scripts\activate` puis `python app-video-frame_PyAV.py`
