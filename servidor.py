import os, subprocess, json, re, glob
from flask import Flask, request, Response, send_from_directory, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_FOLDER = "/tmp/downloads"

def obtener_nombre_playlist(enlace):
    try:
        cmd = f'yt-dlp --flat-playlist --print "%(playlist_title)s" "{enlace}" | head -n 1'
        nombre = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        return nombre if nombre not in ["NA", "None", ""] else None
    except: 
        return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/descargar')
def descargar():
    enlace = request.args.get('url')
    tipo = request.args.get('tipo')
    
    nombre_pl = obtener_nombre_playlist(enlace)
    ruta_final = os.path.join(BASE_FOLDER, nombre_pl) if nombre_pl else BASE_FOLDER
    
    if not os.path.exists(ruta_final): 
        os.makedirs(ruta_final)
    
    # Template para el archivo
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
        
        # Buscamos el nombre del archivo real que se creó para enviarlo después
        archivos = glob.glob(os.path.join(ruta_final, "*"))
        ultimo_archivo = max(archivos, key=os.path.getctime) if archivos else None
        nombre_archivo = os.path.basename(ultimo_archivo) if ultimo_archivo else ""

        yield f"data: {json.dumps({'finalizado': True, 'archivo': nombre_archivo, 'ruta': nombre_pl if nombre_pl else ''})}\n\n"

    return Response(generar_progreso(), mimetype='text/event-stream')

@app.route('/get_file')
def get_file():
    nombre = request.args.get('nombre')
    subcarpeta = request.args.get('ruta')
    directorio = os.path.join(BASE_FOLDER, subcarpeta) if subcarpeta else BASE_FOLDER
    return send_from_directory(directorio, nombre, as_attachment=True)

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)
