import gradio as gr
import ffmpeg
import os
import threading
import shutil
import time
from datetime import datetime, timedelta

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PARENT = os.path.join(BASE_DIR, "extracted_frames")
TEMP_DIR = os.path.join(BASE_DIR, "temp_gradio")

os.makedirs(OUTPUT_PARENT, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = TEMP_DIR

process_event = threading.Event()

def get_video_info(path):
    if not path: return 0, 0
    try:
        probe = ffmpeg.probe(path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        
        duration = float(probe['format'].get('duration', 0))
        
        # Calcul du FPS auto
        fps = 0
        if video_stream and 'avg_frame_rate' in video_stream:
            num, den = map(int, video_stream['avg_frame_rate'].split('/'))
            fps = num / den if den > 0 else 0
            
        return duration, round(fps, 3)
    except: return 600.0, 0

def generate_preview(video_path, time_pos):
    if not video_path: return None
    preview_path = os.path.join(TEMP_DIR, f"preview_live.jpg")
    try:
        (ffmpeg.input(video_path, ss=time_pos)
               .output(preview_path, vframes=1, qscale=5)
               .overwrite_output()
               .run(capture_stdout=True, capture_stderr=True))
        return f"{preview_path}?v={time.time()}"
    except: return None

def extract_logic(video_path, start, end, interval_val, fps_val, use_fps, single_mode, current_pos, img_format):
    if not video_path: return "Erreur : Aucune vidéo", []
    process_event.set()
    
    # Calcul de l'intervalle si mode FPS activé
    actual_interval = (1.0 / fps_val) if use_fps and fps_val > 0 else interval_val
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = os.path.join(OUTPUT_PARENT, f"session_{timestamp}")
    os.makedirs(session_folder, exist_ok=True)
    
    output_files = []
    ext = ".png" if img_format == "PNG (Sans perte)" else ".jpg"
    quality = 1 if img_format == "PNG (Sans perte)" else 2

    points = [current_pos] if single_mode else []
    if not single_mode:
        curr = start
        while curr <= end + 0.0001:
            if not process_event.is_set(): break
            points.append(curr)
            curr += actual_interval

    for t in points:
        if not process_event.is_set(): break
        clean_time = str(timedelta(seconds=round(t, 3))).replace(":", "-").replace(".", "_")
        out_path = os.path.join(session_folder, f"frame_{clean_time}{ext}")
        try:
            (ffmpeg.input(video_path, ss=t)
                   .output(out_path, vframes=1, qscale=quality)
                   .overwrite_output()
                   .run(capture_stdout=True, capture_stderr=True))
            output_files.append(out_path)
        except: continue
        
    return f"Terminé : {len(output_files)} images (Intervalle réel: {round(actual_interval, 4)}s)", output_files

# --- Interface ---
with gr.Blocks(title="Extracteur FPS Pro") as demo:
    gr.Markdown("# 🎬 Extracteur de Frames - Mode FPS & Auto-Détection")
    
    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.Video(label="Source Vidéo")
            preview_img = gr.Image(label="Aperçu de la position", interactive=False)
            btn_clear = gr.Button("🗑️ Nettoyer le dossier TEMP", variant="secondary")
            
        with gr.Column(scale=1):
            status = gr.Textbox(label="Statut / Infos Vidéo", value="Prêt", interactive=False)
            
            with gr.Tab("Navigation"):
                main_pos = gr.Slider(label="Position Lecture (Visualisation)", minimum=0, maximum=100, step=0.01)
                btn_single = gr.Button("📸 Extraire cette image unique", variant="primary")
            
            with gr.Tab("Réglages Plage"):
                with gr.Row():
                    range_start = gr.Slider(label="Début (sec)", minimum=0, maximum=100, step=0.01)
                    range_end = gr.Slider(label="Fin (sec)", minimum=0, maximum=100, step=0.01)
                
                with gr.Row():
                    use_fps = gr.Checkbox(label="Utiliser réglage Img/s (FPS)", value=True)
                    img_format = gr.Radio(["PNG (Sans perte)", "JPG"], label="Format", value="PNG (Sans perte)", scale=1)
                
                # Double interface Intervalle / FPS
                interval_slider = gr.Slider(label="Intervalle Manuel (sec)", minimum=0.01, maximum=10, step=0.01, value=1.0, visible=False)
                fps_input = gr.Number(label="Réglage Images par seconde (FPS)", value=24, precision=3, visible=True)
                
                btn_range = gr.Button("🎞️ Lancer l'extraction groupée", variant="secondary")

            with gr.Row():
                btn_cancel = gr.Button("🛑 Annuler", variant="stop")
                btn_reset = gr.Button("🔄 Reset")
                
            gallery = gr.Gallery(label="Galerie Session", columns=3)

    # --- Logique d'interface ---

    # Basculer visibilité entre FPS et Intervalle
    def toggle_input_mode(is_fps):
        return gr.update(visible=not is_fps), gr.update(visible=is_fps)
    
    use_fps.change(toggle_input_mode, use_fps, [interval_slider, fps_input])

    def on_load(path):
        if not path: return [gr.update()]*3 + ["Prêt", None, 24]
        dur, fps = get_video_info(path)
        msg = f"Vidéo chargée | Durée: {dur}s | FPS détecté: {fps}"
        # On met à jour le champ FPS avec la détection auto
        return (gr.update(maximum=dur, value=0), 
                gr.update(maximum=dur, value=0), 
                gr.update(maximum=dur, value=dur), 
                msg, 
                generate_preview(path, 0),
                fps if fps > 0 else 24)

    video_input.change(on_load, video_input, [main_pos, range_start, range_end, status, preview_img, fps_input])
    main_pos.change(generate_preview, [video_input, main_pos], preview_img)

    # Extraction
    btn_single.click(
        fn=lambda v, rs, re, i, fps, u, f, p: extract_logic(v, rs, re, i, fps, u, True, p, f),
        inputs=[video_input, range_start, range_end, interval_slider, fps_input, use_fps, img_format, main_pos],
        outputs=[status, gallery]
    )

    btn_range.click(
        fn=lambda v, rs, re, i, fps, u, f, p: extract_logic(v, rs, re, i, fps, u, False, p, f),
        inputs=[video_input, range_start, range_end, interval_slider, fps_input, use_fps, img_format, main_pos],
        outputs=[status, gallery]
    )

    btn_clear.click(lambda: shutil.rmtree(TEMP_DIR) or os.makedirs(TEMP_DIR) or "Temp vidé", outputs=status)
    btn_cancel.click(lambda: process_event.clear())
    btn_reset.click(lambda: [None, None, 0, 0, 100, 1.0, 24, "Prêt", []], None, [video_input, preview_img, main_pos, range_start, range_end, interval_slider, fps_input, status, gallery])

if __name__ == "__main__":
    demo.launch()