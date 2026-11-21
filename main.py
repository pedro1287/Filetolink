import os
import sys
import time
import json
import random
import shutil
import base64
import asyncio
import zipfile
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from os.path import exists

import aiohttp
import requests
import urllib3
from bs4 import BeautifulSoup
from telethon.sync import TelegramClient, events, types

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración básica
users = [1552965219]
cloud_space_gb = 10
space_control = True
space_local = 5
cola_download = True
bitzero = 1
api_id = 10181262
api_hash = 'f52b5a057b73b9974eaa7403e04907f0'
bot_token = "7792120327:AAG4GbQZSNL60E4i6QBOVlbj7k9W_F9JE5o"
start_msg = "-4116850567"
key = ""
ghost = "https://revistatelematica.cujae.edu.cu/index.php/tele"
guser = "techdev"
gpass = "@A1a2a3mo"
grepo = 634
zips = 14

MIN_SPLIT_BYTES = 100 * 1024
MAX_SPLIT_BYTES = 1024 * 1024 * 1024

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

# Mini servidor HTTP para satisfacer el Health Check de Render
class RenderHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot activo y funcionando correctamente.")
    def log_message(self, format, *args):
        pass

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), RenderHealthServer)
    print(f"Servidor HTTP de salud corriendo en el puerto {port}")
    server.serve_forever()

http_thread = threading.Thread(target=run_http_server, daemon=True)
http_thread.start()

async def upload_div(ruta_archivo, user_id, msg_id, tamano_parte_mb, cd):
    tamano_parte_bytes = parse_split_size(tamano_parte_mb)
    lista_archivos_divididos = []
    tamano_archivo = os.path.getsize(os.path.join(cd, ruta_archivo))
    temp_dir = os.path.join(cd, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    if tamano_archivo < tamano_parte_bytes:
        shutil.copy(os.path.join(cd, ruta_archivo), os.path.join(temp_dir, ruta_archivo))
        lista_archivos_divididos.append(ruta_archivo)
    else:
        with open(os.path.join(cd, ruta_archivo), 'rb') as archivo_original:
            numero_parte = 1
            while True:
                contenido_parte = archivo_original.read(tamano_parte_bytes)
                if not contenido_parte:
                    break
                nombre_parte = f"{ruta_archivo}_parte_{numero_parte}"
                with open(os.path.join(temp_dir, nombre_parte), 'wb') as archivo_parte:
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
        zip_obj.write(file, os.path.basename(file))
        zip_obj.close()
        mult_file.close()
        ti = 1
        te = True
        await bot.edit_message(user_id, msg_id, "<b>[✓]</b> #seven #local\n\n<code>Dividido</code>", parse_mode='HTML')
        while te:
            file_named = f"{file}.7z.{ti:03d}"
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

async def download_file(url, bot_inst, user, msg, cd):
    size = 0
    t_local = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                file_size = int(response.headers.get('Content-Length', 0))
                try:
                    file_name = response.headers.get('Content-Disposition').split('"')[1]
                except Exception:
                    file_name = url.split('?')[0].split('/')[-1]
                if not file_name:
                    file_name = f"download_{int(time.time())}"
                
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
                        if time.time() - t_local > 1.5 and file_size > 0:
                            t_local = time.time()
                            porcentaje = (size / file_size) * 100
                            barra = "<code>[</code>" + "<b>•</b>" * round(porcentaje / 5) + "<i> </i>" * round((100 - porcentaje) / 5) + "<code>]</code>"
                            await bot_inst.edit_message(
                                user, msg,
                                f"[•] #wget #local #enproceso\n\n<code>{file_name}</code>\n\n<i>{round(porcentaje, 1)}%</i>  <b>{sizeof_fmt(size)}|{sizeof_fmt(file_size)}</b>\n{barra}",
                                parse_mode="HTML"
                            )

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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.4430.72 Safari/537.36"}
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
    with open(path, "rb") as f_to_upload:
        files = {"file": f_to_upload}
        headers["X-Csrf-Token"] = token
        file_upload = session.post(f"{host}/api/v1/submissions/{repo}/files", data=files_data, files=files, headers=headers, verify=False)
        print(file_upload.text)
        file_id = file_upload.text.split('_href":"')[1].split('"')[0].replace(r"\/", "/").split("/")[-1]
        return file_id

async def delete_cloud(fileId, up):
    global ghost, grepo
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.4430.72 Safari/537.36"}
    csrfToken = up.get(f"{ghost}/submission/wizard/2?submissionId={grepo}", headers=headers).text.split('csrfToken":"')[1].split('",')[0]
    up.post(
        f"{ghost}/api/v1/submissions/{repo}/files/{fileId}?stageId=1",
        headers={
            "User-Agent": headers["User-Agent"],
            "x-http-method-override": "DELETE",
            "x-requested-with": "XMLHttpRequest",
            "x-csrf-token": csrfToken
        }
    )

bot = TelegramClient('BitZerOT_session', api_id, api_hash).start(bot_token=bot_token)
os.makedirs("./database", exist_ok=True)

@bot.on(events.NewMessage)
async def techdev_bot(event):
    global users, nubes, cola_download, bitzero, ghost, guser, gpass, grepo, zips, start_msg, cc, timed
    
    text = event.raw_text or ""
    user_id = event.message.chat.id
    msg_id = event.message.id
    username = event.message.chat.username or str(user_id)

    if not isuser(user_id):
        if text == "/report" or text.startswith("/report "):
            msg = text.replace("/report ", "")
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

    if text == '/start':
        local_files = sorted(os.listdir(cd))
        local_files_text = ""
        for idx, item in enumerate(local_files):
            if os.path.isfile(os.path.join(cd, item)):
                local_files_text += f"{idx} 📄 {item}\n"
            else:
                local_files_text += f"<b><i>{idx}</i></b> 📂 <code>{item}</code>\n"
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
            await bot.send_message(
                user_id,
                f"<b><-- BitZero [PkP] --></b>\n\n{start_msg}\n\n<i>Acerca de:</i> /about\n<i>Creado por:</i> @l_tech_dev_l",
                parse_mode="HTML"
            )

    elif sobrepaso and not (text == "/ls" or text.startswith("/rm ") or text.startswith("/up ")):
        await bot.send_message(
            user_id,
            f"<b>⚠️ Almacenamiento lleno:</b> <code>{sizeof_fmt(size_local)} / {sizeof_fmt(space_local * 1024 * 1024 * 1024)}</code>\n<i>Use /rm para liberar espacio.</i>",
            parse_mode="HTML"
        )

    elif text == "/ls":
        size_files = sizeof_fmt(getsize_path(cd))
        local_files = sorted(os.listdir(cd))
        local_files_text = f"<b>Usado: </b><code>{size_files} / {sizeof_fmt(space_local * 1024 * 1024 * 1024)}</code>\n\n"
        for idx, item in enumerate(local_files):
            full_path = os.path.join(cd, item)
            if os.path.isfile(full_path):
                size = os.path.getsize(full_path)
                local_files_text += f"{idx} 📄 <code>{item}</code> | {sizeof_fmt(size)}\n"
            else:
                local_files_text += f"<b><i>{idx}</i></b> 📂 <code>{item}</code>\n"
        if not local_files:
            local_files_text += "🤷🏻‍♂️<i>Sin Archivos</i>\n"
        await bot.send_message(user_id, f"[✓] #ls #local\n\n{local_files_text}", parse_mode="HTML")

    elif text.startswith("/set_cloud ") and user_id == users[0]:
        parts = text.split(" ")
        if len(parts) >= 5:
            ghost = parts[1]
            guser = parts[2]
            gpass = parts[3]
            grepo = parts[4]
            await bot.send_message(user_id, "[✓] #cloud_change #local\n\n<code>Nube configurada con éxito!</code>", parse_mode="HTML")
        else:
            await bot.send_message(user_id, "Formato: /set_cloud <host> <user> <pass> <repo>")

    elif text.startswith("/mkdir"):
        path_name = text.replace("/mkdir", "").strip()
        if path_name:
            os.makedirs(os.path.join(cd, path_name), exist_ok=True)
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
                await bot.send_message(user_id, f"[×] #rm #local\n\n<code>Elemento {r} no encontrado</code>", parse_mode="HTML")
        await bot.send_message(user_id, "[✓] #rm #local\n\n<code>Elementos eliminados</code>", parse_mode="HTML")

    elif text == "/cwd":
        rel = cd.replace(f"database/{user_id}/files", f"${user_id}:")
        await bot.send_message(user_id, f"[✓] #cwd #local\n\n<code>{rel}</code>", parse_mode="HTML")

    elif text.startswith("/zips "):
        zips = text.replace("/zips ", "").strip()
        zips_bytes = parse_split_size(zips)
        await bot.send_message(user_id, f"[✓] #zips #local\n\n<code>Tamaño de zips: {sizeof_fmt(zips_bytes)}</code>", parse_mode="HTML")

    elif text.startswith("/cd "):
        local_files = sorted(os.listdir(cd))
        cdc = text.split(" ")[1].strip()
        if cdc == "..":
            if cd != files_dir:
                cd = os.path.dirname(cd)
                with open(cd_file, "w") as f:
                    f.write(cd)
                await bot.send_message(user_id, "[✓] #cd #local\n\n<code>Directorio anterior</code>", parse_mode="HTML")
            else:
                await bot.send_message(user_id, "[✓] #cd #local\n\n<code>Ya estás en la raíz!</code>", parse_mode="HTML")
        else:
            try:
                cd = os.path.join(cd, local_files[int(cdc)])
                with open(cd_file, "w") as f:
                    f.write(cd)
                await bot.send_message(user_id, "[✓] #cd #local\n\n<code>Directorio cambiado</code>", parse_mode="HTML")
            except Exception:
                await bot.send_message(user_id, "[×] #cd #local\n\n<code>Directorio inexistente</code>", parse_mode="HTML")

    elif (text.startswith("http://") or text.startswith("https://")) and " " not in text.strip():
        url = text.strip()
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply("[•] #wget #local\n\n<code>Generando solicitud...</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        c = 0
        while True:
            w = wait_process(pid)
            if procesos and procesos[0] == pid:
                await bot.edit_message(user_id, msg_id_curr, "[•] #wget #local\n\n<code>Iniciando descarga...</code>", parse_mode="HTML")
                try:
                    await download_file(url, bot, user_id, msg_id_curr, cd)
                    await bot.edit_message(user_id, msg_id_curr, "[✓] #wget #local #finalizado\n\n<code>Descargado con éxito!</code>", parse_mode="HTML")
                except Exception as ex:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #wget #local #error\n\n<code>Error: {str(ex)[:100]}</code>", parse_mode="HTML")
                fin_process(pid)
                break
            else:
                if w != c:
                    c = w
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #wget #local\n\n<code>En cola: {w} esperando</code>", parse_mode="HTML")
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
                    await bot.edit_message(user_id, msg_id_curr, "[•] #file #local\n\n<code>Iniciando descarga...</code>", parse_mode="HTML")
                    filename = ''
                    if event.file and hasattr(event.media, 'document') and event.media.document:
                        for attr in event.media.document.attributes:
                            if isinstance(attr, types.DocumentAttributeFilename):
                                filename = attr.file_name
                    if not filename:
                        filename = f"telegram_file_{int(time.time())}"
                    
                    target_path = os.path.join(cd, filename)
                    
                    async def downprog(cur, total):
                        global timed, cc
                        if cur != cc and (time.time() - timed) > 3.0:
                            timed = time.time()
                            cc = cur
                            pct = (cur / int(total)) * 100
                            barra = "<code>[</code>" + "<b>•</b>" * round(pct / 5) + "<i> </i>" * round((100 - pct) / 5) + "<code>]</code>"
                            await bot.edit_message(
                                user_id, msg_id_curr,
                                f"[•] #file #local #enproceso\n\n<code>{filename}</code>\n\n<i>{round(pct, 1)}%</i> <b>{sizeof_fmt(cur)}|{sizeof_fmt(int(total))}</b>\n{barra}",
                                parse_mode="HTML"
                            )

                    await bot.download_media(event.media, file=target_path, progress_callback=downprog)
                    await bot.edit_message(user_id, msg_id_curr, "[✓] #file #local #finalizado\n\n<code>Descargado!</code>", parse_mode="HTML")
                except Exception as ex:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local #error\n\n<code>Error: {str(ex)[:100]}</code>", parse_mode="HTML")
                fin_process(pid)
                break
            else:
                if w != c:
                    c = w
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local\n\n<code>En cola: {w} esperando</code>", parse_mode="HTML")
                await asyncio.sleep(1)

    elif text.startswith("/split "):
        local_files = sorted(os.listdir(cd))
        parts = text.split(" ")
        try:
            target_file = local_files[int(parts[1])]
            size_part = parts[2]
            pid = random.randint(10000, 99999)
            new_process(pid)
            msg = await event.reply("[•] #split #local\n\n<code>Procesando división...</code>", parse_mode="HTML")
            msg_id_curr = msg.id
            
            while True:
                if procesos and procesos[0] == pid:
                    try:
                        await ziper(os.path.join(cd, target_file), user_id, msg_id_curr, size_part)
                        await bot.edit_message(user_id, msg_id_curr, "[✓] #split #local\n\n<code>Completado!</code>", parse_mode="HTML")
                    except Exception as ex:
                        await bot.edit_message(user_id, msg_id_curr, f"[•] #split #local #error\n\n<code>{str(ex)[:100]}</code>", parse_mode="HTML")
                    fin_process(pid)
                    break
                await asyncio.sleep(1)
        except Exception:
            await bot.send_message(user_id, "Uso: /split <indice> <tamaño_ej_14m>")

    elif text == "/lsc":
        files_cloud = ""
        current = 0
        for nub in nubes[user_nube].get("nube", []):
            files_cloud += f"<code>{current}</code> 📄 <b>{nub.get('filename')}</b>\n"
            current += 1
        if not files_cloud:
            files_cloud = "🤷🏻‍♂️ Sin archivos en la nube"
        await bot.send_message(user_id, f"[✓] #ls #cloud\n\n{files_cloud}", parse_mode="HTML")

    elif text.startswith("/up "):
        total_size = sum(n.get("size", 0) for n in nubes[user_nube].get("nube", []))
        if total_size >= cloud_space:
            await bot.send_message(user_id, "[×] #upload #local #error\n\n<code>Nube llena! Borre archivos.</code>", parse_mode="HTML")
            return
            
        local_files = sorted(os.listdir(cd))
        raw = text.replace("/up ", "").strip()
        if "-" in raw:
            p = raw.split("-")
            indices = list(range(int(p[0].strip()), int(p[1].strip()) + 1))
        elif raw == "all":
            indices = list(range(len(local_files)))
        else:
            indices = [int(x) for x in raw.split() if x.isdigit()]

        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply("[•] #upload #local #enproceso\n\n<code>Iniciando subida...</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        
        while True:
            if procesos and procesos[0] == pid:
                try:
                    temp_dir = os.path.join(cd, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    for f_idx in indices:
                        file_item = local_files[f_idx]
                        file_full = os.path.join(cd, file_item)
                        f_size = os.path.getsize(file_full)
                        
                        if bitzero != 0:
                            div = await upload_div(file_item, user_id, msg_id_curr, zips, cd)
                        else:
                            shutil.copy(file_full, os.path.join(temp_dir, file_item))
                            div = await ziper(os.path.join(temp_dir, file_item), user_id, msg_id_curr, zips)
                            
                        up_session = requests.Session()
                        hdrs = {"User-Agent": "Mozilla/5.0 Chrome/90.0.4430.72 Safari/537.36"}
                        get_tok = up_session.get(f"{ghost}/login", headers=hdrs, verify=False)
                        bs_token = BeautifulSoup(get_tok.text, "html.parser").find('input', {'name': 'csrfToken'})
                        token_val = bs_token['value'] if bs_token else ""
                        
                        up_session.post(
                            f"{ghost}/login/signIn",
                            params={"password": gpass, "remember": 1, "source": "", "username": guser, "csrfToken": token_val},
                            headers=hdrs,
                            verify=False
                        )
                        
                        token_list = []
                        for i_part, d_part in enumerate(div):
                            await bot.edit_message(user_id, msg_id_curr, f"[✓] Subiendo {i_part+1}/{len(div)}: {d_part}", parse_mode="HTML")
                            upid = await upload(os.path.join(temp_dir, d_part), ghost, guser, gpass, grepo, up_session, msg_id_curr, user_id)
                            token_list.append(str(upid))
                            
                        joined_tokens = "-".join(token_list)
                        nubes[user_nube]["nube"].append({"filename": file_item, "token": joined_tokens, "size": f_size})
                        await event.reply(f"[✓] <code>{file_item}</code> subido correctamente!", parse_mode="HTML")

                    unlink(temp_dir)
                    await bot.delete_messages(user_id, msg_id_curr)
                except Exception as ex:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #upload #error: <code>{str(ex)[:120]}</code>", parse_mode="HTML")
                fin_process(pid)
                break
            await asyncio.sleep(1)

    elif text == "/about":
        info = (
            "<b>Comandos disponibles:</b>\n\n"
            "<code>/ls - Listar archivos locales\n"
            "/lsc - Listar archivos en la nube\n"
            "/rm <num> - Eliminar archivo local\n"
            "/up <num> - Subir a la nube\n"
            "/mkdir <nombre> - Crear carpeta\n"
            "/cd <num> - Entrar a carpeta\n"
            "/zips <tamaño> - Cambiar tamaño de partes (ej: 14m, 50m)\n"
            "/split <idx> <size> - Dividir archivo\n"
            "/report <msg> - Enviar reporte al administrador</code>"
        )
        await bot.send_message(user_id, info, parse_mode="HTML")

print("BOT INICIADO Y ESCUCHANDO EVENTOS...")
bot.run_until_disconnected()
