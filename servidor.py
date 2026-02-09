import os, subprocess, json, re
from flask import Flask, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def obtener_nombre_playlist(enlace):
    try:
        cmd = f'yt-dlp --flat-playlist --print "%(playlist_title)s" "{enlace}" | head -n 1'
        nombre = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        return nombre if nombre not in ["NA", "None", ""] else None
    except: return None

@app.route('/descargar')
def descargar():
    enlace = request.args.get('url')
    tipo = request.args.get('tipo')
    base_folder = "/data/data/com.termux/files/home/storage/downloads"
    
    nombre_pl = obtener_nombre_playlist(enlace)
    ruta_final = os.path.join(base_folder, nombre_pl) if nombre_pl else base_folder
    if not os.path.exists(ruta_final): os.makedirs(ruta_final)
    
    template = os.path.join(ruta_final, "%(title)s.%(ext)s")

    def generar_progreso():
        if tipo == 'mp3':
            comando = ['yt-dlp', '-x', '--audio-format', 'mp3', '--embed-thumbnail', '--add-metadata', '-o', template, enlace]
        else:
            comando = ['yt-dlp', '-f', 'mp4', '-o', template, enlace]

        # Abrimos el proceso y leemos su salida en tiempo real
        proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for linea in proceso.stdout:
            # Buscamos el porcentaje en la salida de yt-dlp (ejemplo: [download]  10.5% of...)
            match = re.search(r'(\d+\.\d+)%', linea)
            if match:
                progreso = match.group(1)
                yield f"data: {json.dumps({'progreso': progreso})}\n\n"
        
        proceso.wait()
        
        # Limpieza final
        os.system(f'find "{ruta_final}" -name "*.webp" -delete')
        yield f"data: {json.dumps({'finalizado': True, 'mensaje': '¡Completado!'})}\n\n"

    return Response(generar_progreso(), mimetype='text/event-stream')

import os
# ... (resto del código)
if __name__ == '__main__':
    # Esto permite que la nube asigne el puerto automáticamente
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)

