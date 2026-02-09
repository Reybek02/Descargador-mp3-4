import os, subprocess, json, re
from flask import Flask, request, Response, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 1. FUNCIÓN DE AYUDA
def obtener_nombre_playlist(enlace):
    try:
        cmd = f'yt-dlp --flat-playlist --print "%(playlist_title)s" "{enlace}" | head -n 1'
        nombre = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        return nombre if nombre not in ["NA", "None", ""] else None
    except: 
        return None

# 2. RUTA PARA MOSTRAR LA PÁGINA (INDEX)
@app.route('/')
def index():
    # Esto busca el archivo index.html en la carpeta principal
    return send_from_directory('.', 'index.html')

# 3. RUTA DE DESCARGA
@app.route('/descargar')
def descargar():
    enlace = request.args.get('url')
    tipo = request.args.get('tipo')
    
    # IMPORTANTE: En Render no existe la carpeta de Termux. 
    # Usamos /tmp que es la carpeta temporal permitida en la nube.
    base_folder = "/tmp/downloads"

    nombre_pl = obtener_nombre_playlist(enlace)
    ruta_final = os.path.join(base_folder, nombre_pl) if nombre_pl else base_folder
    
    if not os.path.exists(ruta_final): 
        os.makedirs(ruta_final)
    
    template = os.path.join(ruta_final, "%(title)s.%(ext)s")

    def generar_progreso():
        if tipo == 'mp3':
            comando = ['yt-dlp', '-x', '--audio-format', 'mp3', '--embed-thumbnail', '--add-metadata', '-o', template, enlace]
        else:
            comando = ['yt-dlp', '-f', 'mp4', '-o', template, enlace]

        proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for linea in proceso.stdout:
            match = re.search(r'(\d+\.\d+)%', linea)
            if match:
                progreso = match.group(1)
                yield f"data: {json.dumps({'progreso': progreso})}\n\n"
        
        proceso.wait()
        
        # Limpieza
        os.system(f'find "{ruta_final}" -name "*.webp" -delete')
        os.system(f'find "{ruta_final}" -name "*.jpg" -delete')
        
        yield f"data: {json.dumps({'finalizado': True, 'mensaje': '¡Completado en el servidor!'})}\n\n"

    return Response(generar_progreso(), mimetype='text/event-stream')

# 4. ARRANQUE DEL SERVIDOR
if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)
