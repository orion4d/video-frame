# 🎬 Video Frame Extractor Pro (V7)

Un outil professionnel basé sur **Python 3.12**, **Gradio** et **FFmpeg** conçu pour extraire des images de vidéos (MP4, MKV, AVI, etc.) avec une précision chirurgicale et une fidélité maximale.

<img width="1635" height="1281" alt="image" src="https://github.com/user-attachments/assets/ff682a73-3be5-4151-b7ff-db7e421beaae" />
<img width="1850" height="947" alt="image" src="https://github.com/user-attachments/assets/33cdd50d-78e5-4642-832b-d0f75d026cc3" />

## 🚀 Caractéristiques principales

* **Qualité Master** : Extraction directe via FFmpeg sans recompression. Support des formats **PNG (Lossless)** et **JPG (High Quality)**.
* **Synchronisation en Temps Réel** : Lecteur vidéo synchronisé avec un curseur haute précision (pas de 0.01s) pour une navigation fluide.
* **Intelligence Intégrée** : Auto-détection du nombre d'images par seconde (FPS) de la vidéo source lors de l'importation.
* **Mode Hybride FPS/Intervalle** : 
    * Saisie manuelle ou automatique du FPS (ex: 24 pour capturer chaque frame d'un film).
    * Basculement vers un mode "Intervalle en secondes" pour des captures espacées.
* **Gestion de Sessions** : Création automatique d'un sous-dossier horodaté pour chaque nouvelle extraction afin d'organiser parfaitement vos projets.
* **Outils de Maintenance** : Boutons dédiés pour vider le cache temporaire et ouvrir directement le dossier de sortie dans l'explorateur Windows.

## 🛠️ Installation

### 1. Prérequis
* **Python 3.12** ou supérieur.
* **FFmpeg** : Doit être installé et accessible dans votre variable d'environnement `PATH`.

### 2. Configuration de l'environnement
Ouvrez un terminal dans le dossier du projet :

```bash
# Création de l'environnement virtuel
python -m venv venv

# Activation (Windows)
venv\Scripts\activate

# Installation des dépendances
pip install gradio ffmpeg-python
```
## 🚦 Lancement

Vous pouvez lancer l'application de deux manières :

1.  **Via le script Windows** : Double-cliquez sur `start-app.bat`.
2.  **Via le terminal dans le dossier du venv** : `venv\Scripts\activate puis python app-video-imag.py`
