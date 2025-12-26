# 🎬 Video Frame Extractor Pro (V7)

Un outil professionnel basé sur **Python 3.12**, **Gradio** et **FFmpeg** conçu pour extraire des images de vidéos (MP4, MKV, AVI, etc.) avec une précision chirurgicale et une fidélité maximale.

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

## 🚦 Lancement

Vous pouvez lancer l'application de deux manières :

1.  **Via le script Windows** : Double-cliquez sur `Lancer_Extracteur.bat`.
2.  **Via le terminal** :
    ```bash
    python app-video-imag.py
    ```

Une fois lancé, accédez à l'interface via `http://127.0.0.1:7860` dans votre navigateur.

## 📖 Guide d'utilisation

### Extraction d'une image unique
1.  Importez votre vidéo.
2.  Déplacez le curseur **Position Lecture** pour trouver l'image souhaitée.
3.  Vérifiez le rendu dans le cadre **Aperçu FFmpeg**.
4.  Cliquez sur **Extraire l'instant de lecture**.

### Extraction d'une plage (Batch)
1.  Réglez les curseurs **DÉBUT** et **FIN** de la plage.
2.  Choisissez votre mode : **FPS** (Images/s) ou **Intervalle** (Secondes).
    * *Note technique* : Pour une vidéo à 24 FPS, laissez le réglage sur 24 pour extraire chaque image. Le script calculera l'intervalle exact ($1/24 \approx 0.0416s$).
3.  Cliquez sur **Lancer l'extraction de la plage**.

## 📁 Organisation des fichiers
* `app-video-imag.py` : Code source principal.
* `extracted_frames/` : Contient vos images triées par sessions (`session_YYYYMMDD_HHMMSS`).
* `temp_gradio/` : Cache temporaire pour les prévisualisations.
* `Lancer_Extracteur.bat` : Script de lancement rapide pour Windows.

## ⚖️ Licence
Ce projet est sous licence MIT. Libre à vous de l'utiliser et de le modifier.
