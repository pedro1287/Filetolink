# ==============================================================================
# BOT TELEGRAM BITZERO - INTEGRADO COMPLETO
# CORREGIDO: ENVÍO AUTOMÁTICO DE ENLACE DE DESCARGA / TXT AL FINALIZAR SUBIDA
# SOPORTE DE PARTICIÓN DESDE 100 KiB HASTA 1024 MiB + SERVIDOR RENDER PORT
# ==============================================================================

users = [5692000351]
# EL PRIMER USUARIO ES EL ADMIN, LOS USUARIOS VAN SEPARADOS POR , EN FORMA QUE QUEDA [0000000,0000000,0000000]
cloud_space_gb = 10
# ALMACENAMIENTO EN NUBE POR USUARIO
space_control = True
# SI SE VA A CONTROLAR EL ALMACENAMIENTO LOCAL
space_local = 5
# ALMACENAMIENTO LOCAL POR USUARIO EN GB
cola_download = True
bitzero = 1
api_id = 9024532
api_hash = '131b576240be107210aace99a5f5c5b0'
bot_token = "6446287319:AAHCl-e2ShbqlOM90t2pwqI71LHvsjHntzI"
start_msg = ""
key = ""
ghost = "https://revistatelematica.cujae.edu.cu/index.php/tele"
guser = "techdev"
gpass = "@A1a2a3mo"
grepo = 634
zips = 14

import subprocess
import os
import sys
import asyncio
import urllib
import threading
import time
import json
import urllib3
import shutil
import aiohttp
import base64
import urllib.parse
import zipfile
import random
from os.path import exists
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"])
    import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "bs4"])
    from bs4 import BeautifulSoup

try:
    from telethon.sync import TelegramClient, events, Button, types
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "telethon"])
    from telethon.sync import TelegramClient, events, Button, types

try:
    from pytube import YouTube
except ImportError:
    pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Mini Servidor HTTP en segundo plano para evitar que Render desconecte el servicio
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot activo y funcionando.")
    def log_message(self, format, *args):
        pass

def run_render_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

render_thread = threading.Thread(target=run_render_server, daemon=True)
render_thread.start()

# ── RANGO EXACTO DE PARTICIÓN (100 KiB hasta 1024 MiB) ─────────────────────
MIN_SPLIT_BYTES = 100 * 1024                  # 100 KiB  = 102,400 bytes
MAX_SPLIT_BYTES = 1024 * 1024 * 1024          # 1024 MiB = 1,073,741,824 bytes

def parse_split_size(valor) -> int:
    try:
        if isinstance(valor, str):
            v = valor.strip().lower()
            if v.endswith(('kib', 'kb', 'k')):
                num = float(v.rstrip('kib').rstrip('kb').rstrip('k'))
                tamano = int(num * 1024)
            elif v.endswith(('mib', 'mb', 'm')):
                num = float(v.rstrip('mib').rstrip('mb').rstrip('m'))
                tamano = int(num * 1024 * 1024)
            elif v.endswith(('gib', 'gb', 'g')):
                num = float(v.rstrip('gib').rstrip('gb').rstrip('g'))
                tamano = int(num * 1024 * 1024 * 1024)
            else:
                tamano = int(float(v) * 1024 * 1024)
        else:
            tamano = int(float(valor) * 1024 * 1024)
    except Exception:
        tamano = 14 * 1024 * 1024

    return max(MIN_SPLIT_BYTES, min(tamano, MAX_SPLIT_BYTES))

nubes = []
backup_file = "backup.json"
account_file = "account.json"
backup_interval = 3

def save_backup():
    global nubes
    while True:
        try:
            with open(backup_file, 'w') as f:
                json.dump(nubes, f)
        except Exception:
            pass
        time.sleep(backup_interval)

def load_backup():
    with open(backup_file, 'r') as f:
        return json.load(f)

if exists(backup_file):
    try:
        nubes = load_backup()
        print("BACKUP IMPORTADO")
    except Exception:
        nubes = []
else:
    nubes = []

def save_account():
    global ghost, guser, gpass, grepo, bitzero
    while True:
        try:
            with open(account_file, 'w') as fa:
                fa.write(f"{ghost} {guser} {gpass} {grepo} {bitzero}")
        except Exception:
            pass
        time.sleep(backup_interval)

def load_account():
    global ghost, guser, gpass, grepo, bitzero
    try:
        with open(account_file, 'r') as fa:
            sta = fa.read().strip()
            parts = sta.split(" ")
            if len(parts) >= 4:
                ghost = parts[0]
                guser = parts[1]
                gpass = parts[2]
                grepo = parts[3]
            if len(parts) >= 5:
                bitzero = int(parts[4])
    except Exception:
        pass

if exists(account_file):
    load_account()
    print("ACCOUNT IMPORTADO")

backup_thread = threading.Thread(target=save_backup, daemon=True)
backup_thread.start()

account_thread = threading.Thread(target=save_account, daemon=True)
account_thread.start()

procesos = []
for u in users:
    if not any(n.get("user") == u for n in nubes):
        nubes.append({"user": u, "nube": []})

cc = 0
cloud_space = cloud_space_gb * 1024 * 1024 * 1024
timed = time.time()

async def upload_div(ruta_archivo, user_id, msg_id, tamano_parte_mb, cd):
    tamano_parte_bytes = parse_split_size(tamano_parte_mb)
    lista_archivos_divididos = []
    ruta_completa = os.path.join(cd, ruta_archivo)
    tamano_archivo = os.path.getsize(ruta_completa)
    
    os.makedirs(os.path.join(cd, "temp"), exist_ok=True)

    if tamano_archivo <= tamano_parte_bytes:
        ruta_temp = os.path.join(cd, "temp", ruta_archivo)
        shutil.copy(ruta_completa, ruta_temp)
        lista_archivos_divididos.append(ruta_archivo)
    else:
        with open(ruta_completa, 'rb') as archivo_original:
            numero_parte = 1
            while True:
                contenido_parte = archivo_original.read(tamano_parte_bytes)
                if not contenido_parte:
                    break
                nombre_parte = f"{ruta_archivo}_parte_{numero_parte}"
                ruta_parte = os.path.join(cd, "temp", nombre_parte)
                with open(ruta_parte, 'wb') as archivo_parte:
                    archivo_parte.write(contenido_parte)
                lista_archivos_divididos.append(nombre_parte)
                numero_parte += 1
    return lista_archivos_divididos

async def ziper(file, user_id, msg_id, zips):
    file_size = os.path.getsize(file)
    zipy = parse_split_size(zips)
    filed = []
    if file_size > zipy:
        mult_file = zipfile.MultiFile(file, zipy)
        zip_obj = zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED)
        zip_obj.write(file, arcname=os.path.basename(file))
        zip_obj.close()
        mult_file.close()
        ti = 1
        te = True
        await bot.edit_message(user_id, msg_id, "<b>[✓]</b> #seven #local\n\n<code>Dividido</code>", parse_mode='HTML')
        while te:
            file_named = file + f'.7z.{ti:03d}'
            if exists(file_named):
                ti += 1
                filed.append(os.path.basename(file_named))
            else:
                te = False
    else:
        filed = [os.path.basename(file)]
    return filed

def new_process(pid):
    global procesos
    procesos.append(pid)

def wait_process(pid):
    global procesos
    if procesos and procesos[0] == pid:
        return True
    else:
        for w in range(len(procesos)):
            if procesos[w] == pid:
                return w
    return 0

def fin_process(pid):
    global procesos
    if pid in procesos:
        procesos.remove(pid)

def rm_process():
    global procesos
    procesos = []

async def download_file(url, bot, user, msg, cd):
    size = 0
    t_local = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                file_size = response.headers.get('Content-Length')
                try:
                    file_name = response.headers.get('Content-Disposition').split('"')[1]
                except Exception:
                    file_name = url.split('/')[-1]
                if not file_name:
                    file_name = f"descarga_{int(time.time())}"
                
                rename = 2
                filename_o = file_name
                while os.path.exists(os.path.join(cd, file_name)):
                    file_name = f"c{rename}_{filename_o}"
                    rename += 1
                    
                with open(os.path.join(cd, file_name), 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024 * 64)
                        if not chunk:
                            break
                        f.write(chunk)
                        size += len(chunk)
                        if time.time() - t_local > 1.5:
                            t_local = time.time()
                            porcentaje = (size / int(file_size)) * 100 if file_size else 0
                            barra = "<code>[</code>" + "<b>•</b>" * round(porcentaje / 5) + "<i> </i>" * round((100 - porcentaje) / 5) + "<code>]</code>"
                            total_fmt = sizeof_fmt(int(file_size)) if file_size else "?"
                            await bot.edit_message(user, msg, f"[•] #wget #local #enproceso\n\n<code>{file_name}</code>\n\n<i>{round(porcentaje, 1)}%</i>  <b>{sizeof_fmt(size)}|{total_fmt}</b>\n{barra}", parse_mode="HTML")

def comprimir_carpeta(nombre_carpeta, nombre_zip):
    with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for raiz, directorios, archivos in os.walk(nombre_carpeta):
            for archivo in archivos:
                ruta_archivo = os.path.join(raiz, archivo)
                zipf.write(ruta_archivo, os.path.relpath(ruta_archivo, nombre_carpeta))

def getsize_path(ruta):
    if not os.path.exists(ruta):
        return 0
    return sum(os.path.getsize(os.path.join(carpeta_actual, archivo))
               for carpeta_actual, subcarpetas, archivos in os.walk(ruta)
               for archivo in archivos)

def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.2f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.2f%s%s" % (num, 'Yi', suffix)

def unlink(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

def isuser(u):
    global users
    return u in users

async def upload(path, host, username, password, repo, session, chat_id, user_id):
    global bitzero
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36"}
    
    if bitzero == 1:
        spypng = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'
        new_path = path + f"_#{user_id}@bitzero.png"
        with open(new_path, "wb") as f_out:
            f_out.write(spypng)
            with open(path, "rb") as f_in:
                f_out.write(f_in.read())
        os.unlink(path)
        path = new_path
    elif bitzero == 2:
        spypng = '<!DOCTYPE html>\n<html lang="es">\n<bytes>'
        spypng2 = '</bytes></html>'
        with open(path, 'rb') as file:
            bytes_data = file.read()
        base64_data = base64.b64encode(bytes_data).decode('utf-8')
        new_path = path + f"_#{user_id}@bitzero.html"
        with open(new_path, "w") as f_out:
            f_out.write(spypng + base64_data + spypng2)
        os.unlink(path)
        path = new_path

    submission_page = session.get(f"{host}/submission/wizard/2?submissionId={repo}#step-2", headers=headers, verify=False)
    token = submission_page.text.split('"csrfToken":"')[1].split('"')[0]
    
    files_data = {
        "fileStage": "2",
        "name[es_ES]": os.path.basename(path),
        "name[en_US]": os.path.basename(path)
    }
    with open(path, "rb") as f_in:
        files = {"file": f_in}
        headers["X-Csrf-Token"] = token
        file_upload = session.post(f"{host}/api/v1/submissions/{repo}/files", data=files_data, files=files, headers=headers, verify=False)
        print(f"Respuesta subida: {file_upload.text}")
        
        # Extracción robusta de file_id
        try:
            resp_json = file_upload.json()
            file_id = str(resp_json.get("id") or resp_json.get("fileId"))
        except Exception:
            file_id = file_upload.text.split('_href":"')[1].split('"')[0].replace(r"\/", "/").split("/")[-1]
            
        return file_id

async def delete_cloud(fileId, up):
    global bitzero, ghost, guser, gpass, grepo
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36"}
    csrfToken = up.get(f"{ghost}/submission/wizard/2?submissionId={grepo}", headers=headers).text.split('csrfToken":"')[1].split('",')[0]
    up.post(f"{ghost}/api/v1/submissions/{grepo}/files/{fileId}?stageId=1", headers={"User-Agent": headers["User-Agent"], "x-http-method-override": "DELETE", "x-requested-with": "XMLHttpRequest", "x-csrf-token": csrfToken})

bot = TelegramClient('BitZerOT_session', api_id, api_hash).start(bot_token=bot_token)
os.makedirs("./database", exist_ok=True)

@bot.on(events.NewMessage)
async def techdev_bot(event):
    global users, nubes, cola_download, bitzero, ghost, guser, gpass, grepo, zips, start_msg, cc, timed
    text = event.raw_text or ""
    user_id = event.message.chat.id
    msg_id = event.message.id
    username = event.message.chat.username or ""

    if not isuser(user_id):
        if text.startswith("/report"):
            msg = text.replace("/report", "").strip()
            await bot.send_message(users[0], f"<b>Nuevo reporte</b>\n<i>Usuario: </i>@{username}\n<i>ID: </i>{user_id}\n\n{msg}", parse_mode="HTML")
            await event.reply("Reporte enviado.")
            return
        await bot.send_message(user_id, "<b>[×] #nouser #local #error</b>\n\n<code>Usted no es un usuario autorizado de este bot.</code>", parse_mode="HTML")
        return

    user_nube = None
    for idx, n in enumerate(nubes):
        if n.get("user") == user_id:
            user_nube = idx
            break

    if user_nube is None:
        nubes.append({"user": user_id, "nube": []})
        user_nube = len(nubes) - 1

    user_dir = f"./database/{user_id}"
    files_dir = f"{user_dir}/files"
    os.makedirs(files_dir, exist_ok=True)
    
    cd_file = f"{user_dir}/cd"
    if not os.path.exists(cd_file):
        with open(cd_file, "w") as f:
            f.write(files_dir)
            
    with open(f"{user_dir}/log", "a") as f:
        f.write(f"[!] {msg_id} | {text}\n")
        
    with open(cd_file, "r") as f:
        cd = os.path.normpath(f.read().strip())
    if not os.path.exists(cd):
        cd = files_dir
        with open(cd_file, "w") as f:
            f.write(cd)

    size_local = getsize_path(cd)
    sobrepaso = (size_local >= space_local * 1024 * 1024 * 1024) if space_control else False

    if '/start' == text:
        local_files = sorted(os.listdir(cd))
        local_files_text = ""
        for idx, d in enumerate(local_files):
            if os.path.isfile(os.path.join(cd, d)):
                local_files_text += f"{idx} 📄 {d}\n"
            else:
                local_files_text += f"<b><i>{idx}</i></b> 📂 <code>{d}</code>\n"
        if not local_files:
            local_files_text = "🤷🏻‍♂️<i>Sin Archivos</i>\n"
            
        if not start_msg:
            await bot.send_message(
                user_id,
                f"<b><-- BitZero [PkP] --></b>\n\n"
                f"<b>☁️ Nube:</b> <code>{ghost}</code>\n"
                f"<b>👤 Usuario:</b> <code>{guser}</code>\n"
                f"<b>🔐 Contraseña:</b> <i>****</i>\n"
                f"<b>📂 Repo:</b> <code>{grepo}</code>\n"
                f"<b>🔼 BitZero:</b> <code>{bitzero}</code>\n"
                f"📚 <b>Zips:</b> <code>{zips}</code>\n\n"
                f"<i>Acerca de:</i> /about\n<i>Creado por:</i> @l_tech_dev_l",
                parse_mode="HTML"
            )
        else:
            await bot.send_message(user_id, f"<b><-- BitZero [PkP] --></b>\n\n{start_msg}\n\n<i>Acerca de:</i> /about\n<i>Creado por:</i> @l_tech_dev_l", parse_mode="HTML")
    
    elif sobrepaso and not (text == "/ls" or text.startswith("/rm ") or text.startswith("/up ")):
        await bot.send_message(user_id, f"<b>⚠️Almacenamiento lleno:</b><code>{sizeof_fmt(size_local)} / {sizeof_fmt(space_local*1024*1024*1024)}</code>\n<i>Use el comando /rm para eliminar.</i>", parse_mode="HTML")
    
    elif "/ls" == text:
        size_files = sizeof_fmt(getsize_path(cd))
        local_files = sorted(os.listdir(cd))
        local_files_text = f"<b>Usado: </b><code>{size_files} / {sizeof_fmt(space_local*1024*1024*1024)}</code>\n\n"
        for idx, d in enumerate(local_files):
            full_item = os.path.join(cd, d)
            if os.path.isfile(full_item):
                sz = os.path.getsize(full_item)
                local_files_text += f"{idx} 📄 <code>{d}</code> | {sizeof_fmt(sz)}\n"
            else:
                local_files_text += f"<b><i>{idx}</i></b> 📂 <code>{d}</code>\n"
        if not local_files:
            local_files_text = "🤷🏻‍♂️<i>Sin Archivos</i>\n"
        await bot.send_message(user_id, f"[✓] #ls #local\n\n{local_files_text}", parse_mode="HTML")
    
    elif text.startswith("/set_cloud ") and user_id == users[0]:
        parts = text.split(" ")
        if len(parts) >= 5:
            ghost = parts[1]
            guser = parts[2]
            gpass = parts[3]
            grepo = parts[4]
            await bot.send_message(user_id, "[✓] #cloud_change #local #creado\n\n<code>Editado!!</code>", parse_mode="HTML")
    
    elif text.startswith("/mkdir"):
        path = text.replace("/mkdir", "").strip()
        if path:
            os.makedirs(os.path.join(cd, path), exist_ok=True)
            await bot.send_message(user_id, "[✓] #mkdir #local\n\n<code>Directorio generado</code>", parse_mode="HTML")
    
    elif text.startswith("/rm "):
        local_files = sorted(os.listdir(cd))
        payload = text.replace("/rm ", "").strip()
        if "-" in payload:
            p = payload.split("-")
            indices = list(range(int(p[0].strip()), int(p[1].strip()) + 1))
        elif payload == "all":
            indices = list(range(len(local_files)))
        else:
            indices = [int(x) for x in payload.split() if x.isdigit()]
            
        for r in indices:
            try:
                unlink(os.path.join(cd, local_files[r]))
            except Exception:
                await bot.send_message(user_id, f"[×] #rm #local\n\n<code>Directorio {r} inexistente</code>", parse_mode="HTML")
        await bot.send_message(user_id, "[✓] #rm #local\n\n<code>Directorio/s eliminado/s</code>", parse_mode="HTML")
    
    elif "/cwd" == text:
        rel = cd.replace(f"database/{user_id}/files", f"${user_id}:")
        await bot.send_message(user_id, f"[✓] #cwd #local\n\n<code>{rel}</code>", parse_mode="HTML")
    
    elif text.startswith("/zips "):
        tam_str = text.replace("/zips ", "").strip()
        zips_en_bytes = parse_split_size(tam_str)
        zips = tam_str
        await bot.send_message(user_id, f"[✓] #zips #local\n\n<code>Tamaño de zips cambiado a {sizeof_fmt(zips_en_bytes)}!!</code>", parse_mode="HTML")
    
    elif text.startswith("/cd "):
        local_files = sorted(os.listdir(cd))
        cdc = text.split(" ")[1].strip()
        if cdc == "..":
            if cd != files_dir:
                cd = os.path.dirname(cd)
                with open(cd_file, "w") as f:
                    f.write(cd)
                await bot.send_message(user_id, "[✓] #cd #local\n\n<code>Directorio cambiado</code>", parse_mode="HTML")
            else:
                await bot.send_message(user_id, "[✓] #cd #local\n\n<code>Ya está en root!</code>", parse_mode="HTML")
        else:
            try:
                cd = os.path.join(cd, local_files[int(cdc)])
                with open(cd_file, "w") as f:
                    f.write(cd)
                await bot.send_message(user_id, "[✓] #cd #local\n\n<code>Directorio cambiado</code>", parse_mode="HTML")
            except Exception:
                await bot.send_message(user_id, "[×] #cd #local\n\n<code>No existe el directorio!</code>", parse_mode="HTML")
    
    elif (text.startswith("http://") or text.startswith("https://")) and " " not in text.strip():
        url = text.strip()
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply("[•] #wget #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        c = 0
        msg_id_curr = msg.id
        while True:
            w = wait_process(pid)
            if procesos and procesos[0] == pid:
                await bot.edit_message(user_id, msg_id_curr, "[•] #wget #local\n\n<code>Iniciando solicitud</code>", parse_mode="HTML")
                try:
                    await download_file(url, bot, user_id, msg_id_curr, cd)
                    await bot.edit_message(user_id, msg_id_curr, "[✓] #wget #local #finalizado\n\n<code>Descargado!</code>", parse_mode="HTML")
                except Exception as ex:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #wget #local #error\n\n<code>Error: {ex}</code>", parse_mode="HTML")
                fin_process(pid)
                break
            else:
                if w != c:
                    c = w
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #wget #local\n\n<code>Esperando por {w} procesos</code>", parse_mode="HTML")
                await asyncio.sleep(1)
    
    elif event.media:
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply("[•] #file #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        c = 0
        while True:
            w = wait_process(pid)
            if not cola_download or (procesos and procesos[0] == pid):
                try:
                    await bot.edit_message(user_id, msg_id_curr, "[•] #file #local\n\n<code>Iniciando solicitud</code>", parse_mode="HTML")
                    filename = ''
                    if event.file and hasattr(event.media, 'document') and event.media.document:
                        for attr in event.media.document.attributes:
                            if isinstance(attr, types.DocumentAttributeFilename):
                                filename = attr.file_name
                    if not filename:
                        filename = f"archivo_{int(time.time())}"
                        
                    rename = 2
                    filename_o = filename
                    while os.path.exists(os.path.join(cd, filename)):
                        filename = f"c{rename}_{filename_o}"
                        rename += 1
                        
                    file_path = os.path.join(cd, filename)
                    
                    async def downprog(cur_b, tot_b):
                        global timed, cc
                        if cur_b != cc and (time.time() - timed) > 3.0:
                            timed = time.time()
                            cc = cur_b
                            porcentaje = (cur_b / int(tot_b)) * 100
                            barra = "<code>[</code>" + "<b>•</b>" * round(porcentaje / 5) + "<i> </i>" * round((100 - porcentaje) / 5) + "<code>]</code>"
                            await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local #enproceso\n\n<code>{filename}</code>\n\n<i>{round(porcentaje, 1)}%</i>  <b>{sizeof_fmt(cur_b)}|{sizeof_fmt(int(tot_b))}</b>\n{barra}", parse_mode="HTML")
                            
                    await bot.download_media(event.media, file=file_path, progress_callback=downprog)
                    await bot.edit_message(user_id, msg_id_curr, "[✓] #file #local #finalizado\n\n<code>Descargado!</code>", parse_mode="HTML")
                except Exception as ex:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local #error\n\n<code>Error: {ex}</code>", parse_mode="HTML")
                fin_process(pid)
                break
            else:
                if w != c:
                    c = w
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local\n\n<code>Esperando por {w} procesos</code>", parse_mode="HTML")
                await asyncio.sleep(1)
    
    elif text.startswith("/split "):
        local_files = sorted(os.listdir(cd))
        parts = text.split(" ")
        try:
            target_file = local_files[int(parts[1])]
            tamano_solicitado = parts[2]
            pid = random.randint(10000, 99999)
            new_process(pid)
            msg = await event.reply("[•] #split #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
            msg_id_curr = msg.id
            while True:
                if procesos and procesos[0] == pid:
                    try:
                        await bot.edit_message(user_id, msg_id_curr, "[•] #split #local #enproceso #allpower\n\n<code>Dividiendo su archivo...</code>", parse_mode="HTML")
                        await ziper(os.path.join(cd, target_file), user_id, msg_id_curr, tamano_solicitado)
                    except Exception as ex:
                        await bot.edit_message(user_id, msg_id_curr, f"[•] #split #local #error\n\n<code>Error: {ex}</code>", parse_mode="HTML")
                    fin_process(pid)
                    break
                await asyncio.sleep(1)
        except Exception:
            await bot.send_message(user_id, "Uso: /split <indice> <tamaño_ej_14m>")
    
    elif text.startswith("/mv "):
        local_files = sorted(os.listdir(cd))
        try:
            file_arg = text.split(" ")[1]
            if "-" in file_arg:
                files = list(range(int(file_arg.split("-")[0]), int(file_arg.split("-")[1]) + 1))
            else:
                files = [file_arg]
            
            dest_arg = text.split(" ")[2]
            if dest_arg == "..":
                carpeta = str(os.path.normpath(cd + "/..")) + "/{file_name}"
            elif dest_arg.isdigit():
                carpeta = os.path.join(cd, local_files[int(dest_arg)], "{file_name}")
            else:
                carpeta = os.path.join(cd, dest_arg)
                
            number = 1
            for f in files:
                file_name = local_files[int(f)]
                os.rename(os.path.join(cd, file_name), carpeta.replace("{file_name}", file_name).replace("##", f"{number:03d}"))
                number += 1
            await bot.send_message(user_id, "[✓] #mv #local\n\n<code>Movido satisfactoriamente!</code>", parse_mode="HTML")
        except Exception:
            await bot.send_message(user_id, "[×] #mv #local #error\n\n<code>Algún directorio no existe!</code>", parse_mode="HTML")
    
    elif "/savec" in text:
        open(f"./database/{user_id}/cloud_state", "w").write(str(nubes[user_nube]))
        await bot.send_message(user_id, "[✓] #save #cloud\n\n<code>Base de datos guardada!</code>", parse_mode="HTML")
    
    elif text.startswith("/url "):
        if "-" in text:
            lisc = list(range(int(text.split("-")[0].split(" ")[1]), int(text.split("-")[1].split(" ")[0]) + 1))
            text = "/url " + ' '.join(map(str, lisc))
        elif "all" in text:
            text = "/url " + ' '.join(map(str, list(range(0, len(nubes[user_nube]['nube'])))))
            
        try:
            indexs = text.replace("/url ", "").split(" ")
        except Exception:
            indexs = [text.replace("/url ", "")]
            
        try:
            key_enc = (
                base64.b64encode(ghost.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                base64.b64encode(guser.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                base64.b64encode(gpass.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                base64.b64encode(str(grepo).encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#")
            )
            
            if bitzero != 0:
                msg = ""
                for index in indexs:
                    item_c = nubes[user_nube]['nube'][int(index)]
                    url = f"bitzero https://bitzero.techdev.cu/{item_c['size']}-{grepo}/{item_c['token']}/{bitzero}/{key_enc}/{urllib.parse.quote(item_c['filename'].replace(' ','_'))}"
                    msg += url + " && "
                msg = msg.rstrip(" && ")
                await event.reply(f"[✓] #token #cloud\n\n<code>{msg}</code>", parse_mode="HTML")
            else:
                msg = ""
                for index in indexs:
                    tokens = nubes[user_nube]['nube'][int(index)]['token'].split("-")
                    for fileID in tokens:
                        url = f"{ghost}/$$$call$$$/api/file/file-api/download-file?submissionFileId={fileID}&submissionId={grepo}&stageId=1"
                        msg += url + "\n"
                msg = msg.rstrip("\n")
                name = nubes[user_nube]['nube'][int(indexs[0])]["filename"]
                name_txt = name.rsplit(".", 1)[0] + ".txt"
                with open(name_txt, "w") as f:
                    f.write(msg)
                await bot.send_file(user_id, name_txt, caption="Enlaces directos:")
                os.unlink(name_txt)
        except Exception as ex:
            await bot.send_message(user_id, f"[×] #token #cloud #error\n\n<code>Error: {ex}</code>", parse_mode="HTML")
    
    elif text.startswith("/ziper "):
        local_files = sorted(os.listdir(cd))
        index = int(text.replace("/ziper ", "").strip())
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply("[•] #zip #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        while True:
            if procesos and procesos[0] == pid:
                await bot.edit_message(user_id, msg_id_curr, "[•] #zip #local\n\n<code>COMPRIMIENDO....</code>", parse_mode="HTML")
                try:
                    comprimir_carpeta(os.path.join(cd, local_files[index]), os.path.join(cd, local_files[index] + ".zip"))
                    await bot.edit_message(user_id, msg_id_curr, f"[✓] #zip #local\n\n<code>{local_files[index]}.zip\n\nComprimido</code>", parse_mode="HTML")
                except Exception as ex:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #zip #local #error\n\n<code>Error: {ex}</code>", parse_mode="HTML")
                fin_process(pid)
                break
            await asyncio.sleep(1)
    
    elif "/lsc" == text:
        files_cloud = ""
        for current, nub in enumerate(nubes[user_nube]["nube"]):
            files_cloud += f"<code>{current}</code> 📄 <b>{nub['filename']}</b>\n"
        if not files_cloud:
            files_cloud = "🤷🏻‍♂️Sin archivos"
        await bot.send_message(user_id, f"[✓] #ls #cloud\n\n{files_cloud}", parse_mode="HTML")
    
    # ── COMANDO DE SUBIDA CORREGIDO: ENVÍA EL ENLACE DE DESCARGA AUTOMÁTICAMENTE ──
    elif text.startswith("/up "):
        total_size = sum(nub["size"] for nub in nubes[user_nube]["nube"])
        if total_size >= cloud_space:
            await bot.send_message(user_id, "[×] #upload #local #error\n\n<code>Nube llena! Borre archivos antes de continuar.</code>", parse_mode="HTML")
            return
            
        local_files = sorted(os.listdir(cd))
        payload = text.replace("/up ", "").strip()
        if "-" in payload:
            p = payload.split("-")
            indices = list(range(int(p[0].strip()), int(p[1].strip()) + 1))
        elif payload == "all":
            indices = list(range(len(local_files)))
        else:
            indices = [int(x) for x in payload.split() if x.isdigit()]
            
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply("[•] #upload #local #enproceso\n\n<code>Generando solicitud...</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        
        while True:
            if procesos and procesos[0] == pid:
                try:
                    temp_dir = os.path.join(cd, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    await bot.edit_message(user_id, msg_id_curr, "[•] #upload #local #enproceso\n\n<code>Iniciando proceso de subida...</code>", parse_mode="HTML")
                    
                    for f_idx in indices:
                        file_name = local_files[f_idx]
                        file_full = os.path.join(cd, file_name)
                        file_size = os.path.getsize(file_full)
                        
                        await bot.edit_message(user_id, msg_id_curr, f"[•] #upload #local #enproceso\n\n<code>Dividiendo archivo {file_name}...</code>", parse_mode="HTML")
                        
                        if bitzero != 0:
                            div = await upload_div(file_name, user_id, msg_id_curr, zips, cd)
                        else:
                            shutil.copy(file_full, os.path.join(temp_dir, file_name))
                            div = await ziper(os.path.join(temp_dir, file_name), user_id, msg_id_curr, zips)
                        
                        total_parts = len(div)
                        current_part = 0
                        
                        # Iniciar sesión en OJS
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36"}
                        up_session = requests.Session()
                        getToken = up_session.get(f"{ghost}/login", headers=headers, verify=False)
                        bs_token = BeautifulSoup(getToken.text, "html.parser").find('input', {'name': 'csrfToken'})
                        token_csrf = bs_token['value'] if bs_token else ""
                        
                        login_data = {"password": gpass, "remember": 1, "source": "", "username": guser, "csrfToken": token_csrf}
                        up_session.post(f"{ghost}/login/signIn", data=login_data, headers=headers, verify=False)
                        
                        tokens_list = []
                        for part in div:
                            current_part += 1
                            ruta_parte = os.path.join(temp_dir, part)
                            pct = round((current_part / total_parts) * 100, 1)
                            await bot.edit_message(
                                user_id, msg_id_curr,
                                f"[•] #upload #local #enproceso\n\n<i>{part}</i>\n\n<code>Subiendo {current_part}/{total_parts} ({pct}%)</code>",
                                parse_mode="HTML"
                            )
                            fid = await upload(ruta_parte, ghost, guser, gpass, grepo, up_session, msg_id_curr, user_id)
                            tokens_list.append(str(fid))
                            if os.path.exists(ruta_parte):
                                os.unlink(ruta_parte)
                        
                        tokens_str = "-".join(tokens_list)
                        nubes[user_nube]["nube"].append({"filename": file_name, "size": file_size, "token": tokens_str})
                        
                        # Generación de la clave criptográfica para BitZero
                        key_enc = (
                            base64.b64encode(ghost.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(guser.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(gpass.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(str(grepo).encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#")
                        )
                        
                        # ENVÍO INMEDIATO DEL ENLACE DE DESCARGA O ARCHIVO TXT
                        if bitzero != 0:
                            download_link = f"bitzero https://bitzero.techdev.cu/{file_size}-{grepo}/{tokens_str}/{bitzero}/{key_enc}/{urllib.parse.quote(file_name.replace(' ', '_'))}"
                            await bot.send_message(
                                user_id,
                                f"<b>[✓] #upload #finalizado</b>\n\n"
                                f"📄 <b>Archivo:</b> <code>{file_name}</code>\n"
                                f"📦 <b>Tamaño:</b> <code>{sizeof_fmt(file_size)}</code>\n\n"
                                f"🔗 <b>Comando de Descarga:</b>\n<code>{download_link}</code>",
                                parse_mode="HTML"
                            )
                        else:
                            txt_content = ""
                            for fileID in tokens_list:
                                txt_content += f"{ghost}/$$$call$$$/api/file/file-api/download-file?submissionFileId={fileID}&submissionId={grepo}&stageId=1\n"
                            
                            txt_name = file_name.rsplit(".", 1)[0] + ".txt"
                            with open(txt_name, "w") as f_txt:
                                f_txt.write(txt_content.strip())
                            
                            await bot.send_file(
                                user_id,
                                txt_name,
                                caption=f"<b>[✓] #upload #finalizado</b>\n\n📄 <code>{file_name}</code> subido con éxito.\nAquí tienes tus enlaces de descarga directa:",
                                parse_mode="HTML"
                            )
                            if os.path.exists(txt_name):
                                os.unlink(txt_name)

                    unlink(temp_dir)
                    await bot.delete_messages(user_id, msg_id_curr)
                except Exception as e:
                    await bot.edit_message(user_id, msg_id_curr, f"[×] #upload #local #error\n\n<code>Error al subir: {e}</code>", parse_mode="HTML")
                    
                fin_process(pid)
                break
            await asyncio.sleep(1)

    elif text.startswith("/rmc "):
        try:
            local_cloud = nubes[user_nube]["nube"]
            idx = int(text.replace("/rmc ", "").strip())
            tokens = local_cloud[idx]["token"].split("-")
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36"}
            up = requests.Session()
            getToken = up.get(f"{ghost}/login", headers=headers, verify=False)
            token = BeautifulSoup(getToken.text, "html.parser").find('input', {'name': 'csrfToken'})['value']
            login_data = {"password": gpass, "remember": 1, "source": "", "username": guser, "csrfToken": token}
            up.post(f"{ghost}/login/signIn", data=login_data, headers=headers, verify=False)
            for t_id in tokens:
                await delete_cloud(t_id, up)
            del nubes[user_nube]["nube"][idx]
            await bot.send_message(user_id, "[✓] #rmc #cloud\n\n<code>Archivo eliminado de la nube</code>", parse_mode="HTML")
        except Exception:
            await bot.send_message(user_id, "[✓] #rm #cloud #error\n\n<code>Error al eliminar archivo</code>", parse_mode="HTML")

    elif text.startswith("/adduser ") and user_id == users[0]:
        new_u = int(text.split(" ")[1].strip())
        if new_u not in users:
            users.append(new_u)
            nubes.append({"user": new_u, "nube": []})
        us = '\n'.join(str(u) for u in users)
        await bot.send_message(user_id, f"[✓] #adduser #local\n\n<code>Usuario añadido</code>\n\n{us}", parse_mode="HTML")

    elif text.startswith("/rmuser ") and user_id == users[0]:
        rem_u = int(text.split(" ")[1].strip())
        if rem_u in users:
            users.remove(rem_u)
        nubes = [nb for nb in nubes if nb["user"] != rem_u]
        us = '\n'.join(str(u) for u in users)
        await bot.send_message(user_id, f"[✓] #rmuser #local\n\n<code>Usuario eliminado</code>\n\n{us}", parse_mode="HTML")

    elif "/rmp" in text and user_id == users[0]:
        rm_process()
        await bot.send_message(user_id, "[✓] #rmp #local #eliminado\n\n<code>Procesos eliminados</code>", parse_mode="HTML")

    elif "/off_cola" == text and user_id == users[0]:
        cola_download = False
        await bot.send_message(user_id, "[✓] #off_cola #local\n\n<code>Cola de descarga apagada</code>", parse_mode="HTML")

    elif "/on_cola" == text and user_id == users[0]:
        cola_download = True
        await bot.send_message(user_id, "[✓] #on_cola #local\n\n<code>Cola de descarga encendida</code>", parse_mode="HTML")

    elif text.startswith("/bitzero ") and user_id == users[0]:
        bitzero = int(text.replace("/bitzero ", "").strip())
        await bot.send_message(user_id, f"[✓] #on_bitzero #local\n\n<code>BitZero configurado en: {bitzero}</code>", parse_mode="HTML")

    elif text.startswith("/start_edit ") and user_id == users[0]:
        start_msg = text.replace("/start_edit ", "").strip()
        await bot.send_message(user_id, "[✓] #start_edit #local\n\n<code>Mensaje de inicio editado!!</code>", parse_mode="HTML")

    elif text.startswith("/rmc_token ") and user_id == users[0]:
        token1 = text.split(" ")[1]
        try:
            token2 = text.split(" ")[2]
            tokens = list(range(int(token1), int(token2)))
        except Exception:
            tokens = [token1]
        total = len(tokens)
        current = 0
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36"}
        up = requests.Session()
        getToken = up.get(f"{ghost}/login", headers=headers, verify=False)
        token = BeautifulSoup(getToken.text, "html.parser").find('input', {'name': 'csrfToken'})['value']
        login_data = {"password": gpass, "remember": 1, "source": "", "username": guser, "csrfToken": token}
        up.post(f"{ghost}/login/signIn", params=login_data, headers=headers, verify=False)
        await bot.send_message(user_id, "[•] #rmc_token #cloud #eliminando\n\n<code>Iniciando...</code>", parse_mode="HTML")
        addnum = 0
        for tok in tokens:
            current += 1
            if (current - addnum) > 100:
                addnum += 100
                await asyncio.sleep(3)
            await bot.send_message(user_id, f"[•] #rmc_token #cloud\n\n<code>Eliminando {round((current/total)*100, 3)}%</code>", parse_mode="HTML")
            await delete_cloud(tok, up)
        for nub_item in nubes:
            nub_item["nube"] = []
        await bot.send_message(user_id, "[✓] #rmc_token #cloud #finalizado\n\n<code>Eliminado</code>", parse_mode="HTML")

    elif "/about" == text:
        await bot.send_message(
            user_id,
            "<b>[✓] #about #local</b>\n\n"
            "<b>Comandos:</b>\n\n"
            "<code>/ls - Ver archivos locales\n"
            "/lsc - Ver archivos en la nube\n"
            "/rm <idx> - Eliminar archivo local\n"
            "/rmc <idx> - Eliminar archivo en la nube\n"
            "/up <idx> - Subir a la nube y obtener enlace\n"
            "/url <idx> - Regenerar enlace de descarga\n"
            "/mv - Mover archivo\n"
            "/mkdir - Crear carpeta\n"
            "/ziper - Comprimir carpeta en zip\n"
            "/split - Dividir archivo\n"
            "/zips <tamaño> - Configurar tamaño de partes (ej: 100k, 14m, 1024m)\n"
            "/bitzero <modo> - Modo bitzero (0, 1 o 2)\n"
            "/report <mensaje> - Reportar error al admin</code>",
            parse_mode="HTML"
        )

    elif text.startswith("/send ") and user_id == users[0]:
        msg_send = text.replace("/send ", "")
        for u in users:
            await bot.send_message(u, msg_send, parse_mode="HTML")

# INICIANDO EL CÓDIGO
print("BOT INICIADO Y CORRIENDO EXITOSAMENTE")
bot.run_until_disconnected()
