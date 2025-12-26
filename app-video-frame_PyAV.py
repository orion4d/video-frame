import gradio as gr
import av
import os
import threading
import shutil
import time
from datetime import datetime, timedelta
from PIL import Image

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PARENT = os.path.join(BASE_DIR, "extracted_frames")
TEMP_DIR = os.path.join(BASE_DIR, "temp_gradio")

os.makedirs(OUTPUT_PARENT, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = TEMP_DIR

# Gestion de l'interruption
process_event = threading.Event()

def get_video_info(path):
    """Récupère la durée et le FPS via PyAV"""
    if not path: return 0, 0
    try:
        with av.open(path) as container:
            stream = container.streams.video[0]
            duration = float(container.duration) / av.time_base if container.duration else 0
            fps = float(stream.average_rate)
            return duration, round(fps, 3)
    except Exception as e:
        print(f"Erreur info: {e}")
        return 100.0, 24.0

def generate_preview(video_path, time_pos):
    """Génère un aperçu rapide"""
    if not video_path: return None
    preview_path = os.path.join(TEMP_DIR, "preview_live.jpg")
    
    try:
        with av.open(video_path) as container:
            stream = container.streams.video[0]
            target_pts = int(time_pos / stream.time_base)
            container.seek(target_pts, stream=stream, any_frame=False, backward=True)
            
            for frame in container.decode(stream):
                if frame.pts >= target_pts:
                    img = frame.to_image()
                    img.thumbnail((640, 360)) 
                    img.save(preview_path, format="JPEG", quality=80)
                    return f"{preview_path}?v={time.time()}"
    except: return None

def extract_logic(video_path, start, end, interval_val, fps_val, use_fps, single_mode, current_pos, img_format):
    """Extraction TURBO Séquentielle"""
    if not video_path: return "Erreur : Aucune vidéo", []
    
    process_event.set()
    
    # 1. Configuration
    target_interval = (1.0 / fps_val) if use_fps and fps_val > 0 else interval_val
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = os.path.join(OUTPUT_PARENT, f"session_{timestamp}")
    os.makedirs(session_folder, exist_ok=True)
    
    output_files = []
    is_png = "PNG" in img_format
    ext = ".png" if is_png else ".jpg"

    # 2. Définir la liste chronologique des timestamps voulus
    target_timestamps = []
    if single_mode:
        target_timestamps = [current_pos]
    else:
        curr = start
        while curr <= end + 0.0001:
            target_timestamps.append(curr)
            curr += target_interval
            
    if not target_timestamps: return "Aucune image à extraire", []

    count = 0
    t_start_process = time.time()

    try:
        with av.open(video_path) as container:
            stream = container.streams.video[0]
            stream.thread_type = "AUTO"
            
            # --- LOGIQUE SÉQUENTIELLE OPTIMISÉE ---
            
            # On se place juste avant le premier timestamp
            first_target = target_timestamps[0]
            start_pts = int(first_target / stream.time_base)
            container.seek(start_pts, stream=stream, any_frame=False, backward=True)
            
            target_idx = 0
            total_targets = len(target_timestamps)
            
            # On lit le flux frame par frame (C'est la partie la plus rapide)
            for frame in container.decode(stream):
                if not process_event.is_set(): break
                if target_idx >= total_targets: break # Tout est fini
                
                # Temps actuel de la frame
                current_time = float(frame.pts * stream.time_base)
                
                # Regarder le timestamp cible actuel
                target_time = target_timestamps[target_idx]
                
                # Tolérance (moitié d'une frame environ pour éviter les doublons/ratés)
                # Si on est proche du timestamp voulu (ou qu'on vient de le dépasser légèrement)
                # On capture.
                
                # Si la frame est encore trop tôt, on continue
                if current_time < target_time - (target_interval * 0.5):
                    continue
                
                # Si la frame est trop tard par rapport à la cible, on avance la cible (frame droppée)
                # Cela arrive si le seeking nous a mis trop loin (rare avec backward=True)
                while target_idx < total_targets and current_time > target_timestamps[target_idx] + (target_interval * 0.5):
                     target_idx += 1
                
                if target_idx >= total_targets: break

                # On est dans la fenêtre de tir !
                target_time = target_timestamps[target_idx]
                
                # Capture
                img = frame.to_image()
                clean_time = str(timedelta(seconds=round(target_time, 3))).replace(":", "-").replace(".", "_")
                out_path = os.path.join(session_folder, f"frame_{clean_time}{ext}")
                
                # Sauvegarde (C'est souvent le goulot d'étranglement maintenant)
                if is_png:
                    img.save(out_path, "PNG", compress_level=1) # compress_level=1 pour speed (défaut=6)
                else:
                    img.save(out_path, "JPEG", quality=95)
                
                output_files.append(out_path)
                count += 1
                
                # On passe à la cible suivante
                target_idx += 1
                    
    except Exception as e:
        return f"Erreur critique : {str(e)}", []
        
    duration = round(time.time() - t_start_process, 2)
    status_msg = "Annulé" if not process_event.is_set() else "Terminé"
    return f"{status_msg} : {count} images en {duration}s ({session_folder})", output_files

# --- Interface Gradio ---
with gr.Blocks(title="Extracteur FPS Turbo") as demo:
    gr.Markdown("# 🚀 Extracteur de Frames - PyAV Sequential (Ultra Rapide)")
    
    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.Video(label="Source Vidéo")
            preview_img = gr.Image(label="Aperçu Position", interactive=False, height=300)
            btn_clear = gr.Button("🗑️ Nettoyer Temp", variant="secondary")
            
        with gr.Column(scale=1):
            status = gr.Textbox(label="Statut / Infos", value="Prêt", interactive=False)
            
            with gr.Tab("Navigation"):
                main_pos = gr.Slider(label="Position (sec)", minimum=0, maximum=100, step=0.01)
                btn_single = gr.Button("📸 Extraire cette image", variant="primary")
            
            with gr.Tab("Extraction par Lot"):
                with gr.Row():
                    range_start = gr.Slider(label="Début (sec)", minimum=0, maximum=100, step=0.01)
                    range_end = gr.Slider(label="Fin (sec)", minimum=0, maximum=100, step=0.01)
                
                with gr.Row():
                    use_fps = gr.Checkbox(label="Mode FPS", value=True)
                    img_format = gr.Radio(["PNG (Lent)", "JPG (Rapide)"], label="Format", value="PNG (Lent)")
                
                interval_slider = gr.Slider(label="Intervalle (sec)", minimum=0.01, maximum=10, step=0.01, value=1.0, visible=False)
                fps_input = gr.Number(label="FPS (Images par seconde)", value=24, precision=3, visible=True)
                
                btn_range = gr.Button("🎞️ Lancer l'extraction de la plage", variant="secondary")

            with gr.Row():
                btn_cancel = gr.Button("🛑 Annuler", variant="stop")
                btn_reset = gr.Button("🔄 Reset Interface")
                
            gallery = gr.Gallery(label="Résultat Session", columns=4, height=300)

    # --- Événements ---
    def toggle_input_mode(is_fps):
        return gr.update(visible=not is_fps), gr.update(visible=is_fps)
    
    use_fps.change(toggle_input_mode, use_fps, [interval_slider, fps_input])

    def on_load(path):
        if not path: return [gr.update()]*3 + ["Prêt", None, 24]
        dur, fps = get_video_info(path)
        return (gr.update(maximum=dur, value=0), 
                gr.update(maximum=dur, value=0), 
                gr.update(maximum=dur, value=dur), 
                f"Chargé | Durée: {round(dur, 2)}s | FPS: {fps}", 
                generate_preview(path, 0),
                fps if fps > 0 else 24)

    video_input.change(on_load, video_input, [main_pos, range_start, range_end, status, preview_img, fps_input])
    main_pos.release(generate_preview, [video_input, main_pos], preview_img)

    btn_single.click(lambda v, rs, re, i, fps, u, f, p: extract_logic(v, rs, re, i, fps, u, True, p, f),
                     inputs=[video_input, range_start, range_end, interval_slider, fps_input, use_fps, img_format, main_pos],
                     outputs=[status, gallery])

    btn_range.click(lambda v, rs, re, i, fps, u, f, p: extract_logic(v, rs, re, i, fps, u, False, p, f),
                    inputs=[video_input, range_start, range_end, interval_slider, fps_input, use_fps, img_format, main_pos],
                    outputs=[status, gallery])

    btn_clear.click(lambda: shutil.rmtree(TEMP_DIR) or os.makedirs(TEMP_DIR) or "Temp vidé", outputs=status)
    btn_cancel.click(lambda: process_event.clear())
    btn_reset.click(lambda: [None, None, 0, 0, 100, 1.0, 24, "Prêt", []], None, [video_input, preview_img, main_pos, range_start, range_end, interval_slider, fps_input, status, gallery])

if __name__ == "__main__":
    demo.launch()