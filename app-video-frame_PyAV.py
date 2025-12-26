import gradio as gr
import av
import os
import threading
import shutil
import time
from datetime import datetime, timedelta
from PIL import Image

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PARENT = os.path.join(BASE_DIR, "extracted_frames")
TEMP_DIR = os.path.join(BASE_DIR, "temp_gradio")
LEGACY_SAFE_DIR = os.path.join(BASE_DIR, "safe_work_zone")

os.makedirs(OUTPUT_PARENT, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = TEMP_DIR

process_event = threading.Event()

# --- NETTOYAGE ---
if os.path.exists(LEGACY_SAFE_DIR):
    try: shutil.rmtree(LEGACY_SAFE_DIR)
    except: pass

def clean_temp_files():
    msg = []
    try:
        if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR)
        msg.append("Temp vidé")
    except Exception as e: msg.append(f"Erreur Temp: {e}")
    return " | ".join(msg)

# --- MOTEUR PYAV ---

def get_video_info(path):
    """
    Récupère la durée.
    Si échec détection -> Retourne 24 HEURES (86400s) pour ne pas bloquer l'utilisateur.
    """
    FALLBACK_DURATION = 10800.0 # 3 Heures par défaut si illisible
    
    if not path: return 0, 0
    try:
        with av.open(path) as container:
            stream = container.streams.video[0]
            fps = float(stream.average_rate)
            
            # 1. Essai via Container
            duration = float(container.duration) / av.time_base if container.duration else 0
            
            # 2. Essai via Stream
            if duration <= 0 and stream.duration:
                duration = float(stream.duration * stream.time_base)
            
            # 3. Smart Seek (Tentative ultime)
            if duration <= 1:
                try:
                    container.seek(1 << 60, stream=stream, backward=True, any_frame=False)
                    for frame in container.decode(stream):
                        duration = float(frame.pts * stream.time_base)
                        break
                except:
                    pass # On garde 0 si ça plante
            
            # Si après tout ça on est toujours proche de 0, on met le MAX
            if duration <= 10:
                print("⚠️ Durée non détectée : Passage en mode manuel (Max 24h)")
                duration = FALLBACK_DURATION
            
            return duration, round(fps, 3)
            
    except Exception as e:
        print(f"Erreur critique info: {e} -> Passage en mode manuel")
        return FALLBACK_DURATION, 24.0

def fast_preview(video_path, time_pos):
    if not video_path: return None
    preview_path = os.path.join(TEMP_DIR, "preview_live.jpg")
    try:
        with av.open(video_path) as container:
            stream = container.streams.video[0]
            target_pts = int(time_pos / stream.time_base)
            container.seek(target_pts, stream=stream, any_frame=False, backward=True)
            for frame in container.decode(stream):
                img = frame.to_image()
                img.thumbnail((480, 270)) 
                img.save(preview_path, format="JPEG", quality=70)
                return f"{preview_path}?v={time.time()}"
    except: return None

def extract_native(video_path, start, end, interval_val, fps_val, use_fps, single_mode, single_pos, img_format):
    if not video_path: return "Erreur : Aucune vidéo", []
    process_event.set()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = "single" if single_mode else "batch"
    session_folder = os.path.join(OUTPUT_PARENT, f"{folder_name}_{timestamp}")
    os.makedirs(session_folder, exist_ok=True)
    
    is_png = "PNG" in img_format
    ext = ".png" if is_png else ".jpg"
    output_files = []

    target_interval = (1.0 / fps_val) if use_fps and fps_val > 0 else interval_val
    target_timestamps = [single_pos] if single_mode else []
    
    if not single_mode:
        curr = start
        # Sécurité : on s'arrête si l'utilisateur demande une fin au delà de la fin réelle
        # Mais comme on ne connait pas la fin réelle, on fait confiance à l'utilisateur
        # On ajoute juste une sécurité anti-boucle infinie (max 100 000 images)
        while curr <= end + 0.0001:
            target_timestamps.append(curr)
            curr += target_interval
            if len(target_timestamps) > 100000: break 
            
    if not target_timestamps: return "Rien à extraire", []

    count = 0
    t_start = time.time()

    try:
        with av.open(video_path) as container:
            stream = container.streams.video[0]
            stream.thread_type = "AUTO"
            tb = stream.time_base
            
            if single_mode:
                target = target_timestamps[0]
                pts = int(target / tb)
                container.seek(pts, stream=stream, any_frame=False, backward=True)
                for frame in container.decode(stream):
                    if frame.pts >= pts:
                        img = frame.to_image()
                        clean_time = str(timedelta(seconds=round(target, 3))).replace(":", "-").replace(".", "_")
                        out_path = os.path.join(session_folder, f"frame_{clean_time}{ext}")
                        if is_png: img.save(out_path, "PNG", compress_level=1)
                        else: img.save(out_path, "JPEG", quality=95)
                        return f"Image sauvegardée : {out_path}", [out_path]

            else:
                start_pts = int(target_timestamps[0] / tb)
                container.seek(start_pts, stream=stream, any_frame=False, backward=True)
                target_idx = 0
                total = len(target_timestamps)
                
                for frame in container.decode(stream):
                    if not process_event.is_set(): break
                    if target_idx >= total: break
                    
                    t_curr = float(frame.pts * tb)
                    t_target = target_timestamps[target_idx]
                    
                    if t_curr < t_target - (target_interval * 0.5): continue
                    while target_idx < total and t_curr > target_timestamps[target_idx] + (target_interval * 0.5):
                        target_idx += 1
                    if target_idx >= total: break

                    img = frame.to_image()
                    clean_time = str(timedelta(seconds=round(target_timestamps[target_idx], 3))).replace(":", "-").replace(".", "_")
                    out_path = os.path.join(session_folder, f"frame_{clean_time}{ext}")
                    
                    if is_png: img.save(out_path, "PNG", compress_level=1)
                    else: img.save(out_path, "JPEG", quality=95)
                    
                    output_files.append(out_path)
                    count += 1
                    target_idx += 1

    except Exception as e:
        return f"Erreur : {e}", []

    dur = round(time.time() - t_start, 2)
    return f"Terminé : {count} images en {dur}s ({session_folder})", output_files

# --- INTERFACE ---
DEFAULT_MAX = 10800.0 # 3h par défaut

with gr.Blocks(title="Extracteur Video Pro V7") as demo:
    gr.Markdown("# 🚀 Extracteur de Frames")
    
    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.Video(label="Source Vidéo")
            preview_img = gr.Image(label="Aperçu Rapide", interactive=False, height=300)
            btn_clear = gr.Button("🗑️ Nettoyer Temp", variant="secondary")
            
        with gr.Column(scale=1):
            status = gr.Textbox(label="Statut", value="Prêt", interactive=False)
            
            with gr.Tab("Navigation"):
                main_pos = gr.Slider(label="Position (sec)", minimum=0, maximum=DEFAULT_MAX, step=0.01, value=0)
                btn_single = gr.Button("📸 Extraire cette image", variant="primary")
            
            with gr.Tab("Extraction par Lot"):
                with gr.Row():
                    range_start = gr.Slider(label="Début", minimum=0, maximum=DEFAULT_MAX, step=0.1, value=0)
                    range_end = gr.Slider(label="Fin", minimum=0, maximum=DEFAULT_MAX, step=0.1, value=100)
                
                with gr.Row():
                    use_fps = gr.Checkbox(label="Mode FPS", value=True)
                    img_format = gr.Radio(["PNG (Lent)", "JPG (Rapide)"], label="Format", value="PNG (Lent)")
                
                interval_slider = gr.Slider(label="Intervalle (sec)", minimum=0.01, maximum=10, step=0.01, value=1.0, visible=False)
                fps_input = gr.Number(label="FPS Cible", value=24, visible=True)
                
                btn_range = gr.Button("🎞️ Lancer l'extraction", variant="secondary")
            
            with gr.Row():
                btn_cancel = gr.Button("🛑 Stop", variant="stop")
                btn_reset = gr.Button("🔄 Reset")

            gallery = gr.Gallery(label="Galerie", columns=4, height=250)

    # --- LOGIQUE ---

    def on_load(path):
        if not path: return [gr.update()]*3 + ["Pas de vidéo", 24]
        
        dur, fps = get_video_info(path)
        
        # Info texte
        if dur >= 86000:
            msg = f"Chargé | Durée : Inconnue -> Limite fixée à 24h | FPS: {fps}"
        else:
            msg = f"Chargé | Durée: {round(dur, 2)}s | FPS: {fps}"
        
        return (
            gr.update(maximum=dur, value=0),           
            gr.update(maximum=dur, value=0),           
            gr.update(maximum=dur, value=dur if dur < 86000 else 600), # Par défaut fin à 10mn si durée inconnue   
            msg,
            fps if fps > 0 else 24
        )

    video_input.change(on_load, video_input, [main_pos, range_start, range_end, status, fps_input])
    main_pos.release(fast_preview, [video_input, main_pos], preview_img)
    use_fps.change(lambda x: (gr.update(visible=not x), gr.update(visible=x)), use_fps, [interval_slider, fps_input])

    btn_single.click(
        fn=lambda v, rs, re, i, f, u, fmt, p: extract_native(v, rs, re, i, f, u, True, p, fmt),
        inputs=[video_input, range_start, range_end, interval_slider, fps_input, use_fps, img_format, main_pos],
        outputs=[status, gallery]
    )

    btn_range.click(
        fn=lambda v, rs, re, i, f, u, fmt, p: extract_native(v, rs, re, i, f, u, False, p, fmt),
        inputs=[video_input, range_start, range_end, interval_slider, fps_input, use_fps, img_format, main_pos],
        outputs=[status, gallery]
    )

    btn_clear.click(clean_temp_files, outputs=status)
    btn_cancel.click(lambda: process_event.clear())
    btn_reset.click(lambda: [None, None, 0, 0, DEFAULT_MAX, 1.0, 24, "Prêt", []], None, [video_input, preview_img, main_pos, range_start, range_end, interval_slider, fps_input, status, gallery])

if __name__ == "__main__":
    demo.launch()