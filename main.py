# -*- coding: utf-8 -*-
# ==============================================================================
# BOT TELEGRAM BITZERO - TODAS LAS FUNCIONES ORIGINALES RESTAURADAS
# SUBIDA CORREGIDA PARA EDICIONES.UO.EDU.CU
# ==============================================================================

users = [1552965219]
# EL PRIMER USUARIO ES EL ADMIN, LOS USUARIOS VAN SEPARADOS POR , EN FORMA QUE QUEDA [0000000,0000000,0000000]
cloud_space_gb = 10
# ALMACENAMIENTO EN NUBE POR USUARIO
space_control = True
# SI SE VA A CONTROLAR EL ALMACENAMIENTO LOCAL
space_local = 5
# ALMACENAMIENTO LOCAL POR USUARIO EN GB
cola_download = True
bitzero = 1
api_id = 10181262
api_hash = 'f52b5a057b73b9974eaa7403e04907f0'
bot_token = "7792120327:AAG4GbQZSNL60E4i6QBOVlbj7k9W_F9JE5o"
start_msg = ""
key = ""
ghost = "https://ediciones.uo.edu.cu/index.php/e1"
guser = "pepe"
gpass = "Lianet123*#"
grepo = 1921
zips = 14

import subprocess
try:
    import requests
except:
    subprocess.run(["pip", "install", "requests"])
    import requests
try:
    from bs4 import BeautifulSoup
except:
    subprocess.run(["pip", "install", "bs4"])
    from bs4 import BeautifulSoup
import random
try:
    from telethon.sync import TelegramClient, events, Button, types
except:
    subprocess.run(["pip", "install", "telethon"])
    from telethon.sync import TelegramClient, events, Button, types
from os.path import exists
import os
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
from pytube import YouTube
import zipfile

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Byte limpio de camuflaje PNG de BitZero
PNG_CAMO = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00'
    b'\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'
)

nube = []
backup_file = "backup.json"
account_file = "account.json"
backup_interval = 3

def save_backup():
    global nubes
    while True:
        with open(backup_file, 'w') as f:
            json.dump(nubes, f)
        time.sleep(backup_interval)

def load_backup():
    with open(backup_file, 'r') as f:
        return json.load(f)

if exists(backup_file):
    nubes = load_backup()
    print("BACKUP IMPORTADO")
else:
    nubes = []

def save_account():
    global ghost, guser, gpass, grepo, bitzero
    while True:
        with open(account_file, 'w') as fa:
            fa.write(f"{ghost} {guser} {gpass} {grepo} {bitzero}")
        time.sleep(backup_interval)

def load_account():
    global ghost, guser, gpass, grepo, bitzero
    with open(account_file, 'r') as fa:
        sta = fa.read()
        ghost = sta.split(" ")[0]
        guser = sta.split(" ")[1]
        gpass = sta.split(" ")[2]
        grepo = sta.split(" ")[3]

if exists(account_file):
    load_account()
    print("ACCOUNT IMPORTADO")

backup_thread = threading.Thread(target=save_backup)
backup_thread.daemon = True
backup_thread.start()

account_thread = threading.Thread(target=save_account)
account_thread.daemon = True
account_thread.start()

procesos = []
for u in users:
    nubes.append({"user": u, "nube": []})

cc = 0
cloud_space = cloud_space_gb * 1024 * 1024 * 1024
timed = time.time()

# ── RANGO EXACTO DE PARTICIÓN (100 KiB a 1024 MiB) ──
MIN_SPLIT_BYTES = 100 * 1024
MAX_SPLIT_BYTES = 1024 * 1024 * 1024

def parse_split_size(valor) -> int:
    try:
        if isinstance(valor, str):
            v = valor.strip().lower()
            if v.endswith(('kib', 'kb', 'k')):
                tamano = int(float(v.rstrip('kib').rstrip('kb').rstrip('k')) * 1024)
            elif v.endswith(('mib', 'mb', 'm')):
                tamano = int(float(v.rstrip('mib').rstrip('mb').rstrip('m')) * 1024 * 1024)
            elif v.endswith(('gib', 'gb', 'g')):
                tamano = int(float(v.rstrip('gib').rstrip('gb').rstrip('g')) * 1024 * 1024 * 1024)
            else:
                tamano = int(float(v) * 1024 * 1024)
        else:
            tamano = int(float(valor) * 1024 * 1024)
    except:
        tamano = 14 * 1024 * 1024
    return max(MIN_SPLIT_BYTES, min(tamano, MAX_SPLIT_BYTES))

async def upload_div(ruta_archivo, user_id, msg_id, tamano_parte_mb, cd):
    tamano_parte_bytes = parse_split_size(tamano_parte_mb)
    lista_archivos_divididos = []
    tamano_archivo = os.path.getsize(cd + "/" + ruta_archivo)
    os.makedirs(cd + "/temp", exist_ok=True)
    if tamano_archivo <= tamano_parte_bytes:
        open(cd + "/temp/" + ruta_archivo, "wb").write(open(cd + "/" + ruta_archivo, "rb").read())
        lista_archivos_divididos.append(ruta_archivo)
    else:
        with open(cd + "/" + ruta_archivo, 'rb') as archivo_original:
            numero_parte = 1
            while True:
                contenido_parte = archivo_original.read(tamano_parte_bytes)
                if not contenido_parte:
                    break
                nombre_parte = f"{ruta_archivo}_parte_{numero_parte}"
                with open(cd + "/temp/" + nombre_parte, 'wb') as archivo_parte:
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
        zip = zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        ti = 1
        te = True
        await bot.edit_message(user_id, msg_id, "<b>[✓]</b> #seven #local\n\n<code>Dividido</code>", parse_mode='HTML')
        while te:
            file_named = file + '.7z.{:03d}'.format(ti)
            if exists(file_named):
                ti += 1
                filed.append(file_named.split("/")[-1])
            else:
                te = False
    else:
        filed = [file.split("/")[-1]]
    return filed

def new_process(pid):
    global procesos
    procesos.append(pid)

def wait_process(pid):
    global procesos
    if len(procesos) > 0 and procesos[0] == pid:
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

def o85ea6(eu6363):
    return base64.b64decode(eu6363.encode()).decode()

def gptd(value):
    nonce = requests.get("https://chatgpt.ch/")
    wpnonce = nonce.text.split('data-nonce="')[1].split('"')[0]
    a73664 = "aHR0cHM6Ly9jaGF0Z3B0LmNoL3dwLWFkbWluL2FkbWluLWFqYXgucGhw"
    e657674 = "X3dwbm9uY2U="
    chatGPT = requests.post(o85ea6(a73664), data={
        o85ea6(e657674): wpnonce,
        o85ea6("dXJs"): o85ea6(e657674),
        o85ea6("bWVzc2FnZQ=="): value,
        o85ea6("cG9zdF9pZA=="): 106,
        o85ea6("YWN0aW9u"): o85ea6("d3BhaWNnX2NoYXRfc2hvcnRjb2RlX21lc3NhZ2U="),
        o85ea6("Ym90X2lk"): 0
    })
    data_dict = json.loads(chatGPT.text)
    return data_dict['data']

async def download_file(url, bot, user, msg, cd):
    size = 0
    timed = time.time()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, allow_redirects=True) as response:
            if response.status == 200:
                file_size = response.headers.get('Content-Length')
                try:
                    file_name = response.headers.get('Content-Disposition').split('filename=')[1].replace('"', '').strip()
                except:
                    file_name = url.split('/')[-1].split('?')[0]
                if not file_name:
                    file_name = f"descarga_{int(time.time())}"
                
                rename = 2
                filename_o = file_name
                while os.path.exists(cd + "/" + file_name):
                    file_name = f"c{rename}_" + filename_o
                    rename += 1

                with open(cd + "/" + file_name, 'wb') as f:
                    while True:
                        chunk = await response.content.read(64 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        size += len(chunk)
                        if time.time() - timed > 1.2:
                            timed = time.time()
                            porcentaje = (size / int(file_size)) * 100 if file_size else 0
                            barra = "<code>[</code>" + "<b>•</b>" * round(porcentaje / 3.33333) + "<i> </i>" * round((100 - porcentaje) / 3.33333) + "<code>]</code>"
                            total_fmt = sizeof_fmt(int(file_size)) if file_size else "?"
                            await bot.edit_message(user, msg, f"[•] #wget #local #enproceso\n\n<code>{file_name}</code>\n\n<i>{round(porcentaje, 1)}%</i>  <b>{sizeof_fmt(size)}|{total_fmt}</b>\n{barra}", parse_mode="HTML")

def comprimir_carpeta(nombre_carpeta, nombre_zip):
    with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for raiz, directorios, archivos in os.walk(nombre_carpeta):
            for archivo in archivos:
                ruta_archivo = os.path.join(raiz, archivo)
                zipf.write(ruta_archivo, os.path.relpath(ruta_archivo, nombre_carpeta))

def getsize_path(ruta):
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
    for user in users:
        if user == u:
            return True
    return False

# ── FUNCIÓN DE SUBIDA ADAPTADA A EDICIONES.UO.EDU.CU ──
async def upload(path, host, username, password, repo, session, chat_id, user_id):
    global bitzero
    host = host.rstrip("/")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{host}/submission/wizard/2?submissionId={repo}#step-2"
    }
    
    if bitzero == 1:
        new_path = path + f"_#{user_id}@bitzero.png"
        open(new_path, "wb").write(PNG_CAMO + open(path, "rb").read())
        os.unlink(path)
        path = new_path
    elif bitzero == 2:
        spypng = '<!DOCTYPE html>\n<html lang="es">\n<bytes>'
        spypng2 = '</bytes></html>'
        with open(path, 'rb') as file:
            bytes_data = file.read()
        base64_data = base64.b64encode(bytes_data).decode('utf-8')
        new_path = path + f"_#{user_id}@bitzero.html"
        open(new_path, "w", encoding="utf-8").write(spypng + base64_data + spypng2)
        os.unlink(path)
        path = new_path

    # Obtener el CSRF Token del formulario
    submission_page = session.get(f"{host}/submission/wizard/2?submissionId={repo}#step-2", headers=headers, verify=False, timeout=30)
    token = submission_page.text.split('"csrfToken":"')[1].split('"')[0]
    headers["X-Csrf-Token"] = token

    base_name = os.path.basename(path)
    files_data = {
        "fileStage": "2",
        "name[es_ES]": base_name,
        "name[en_US]": base_name
    }
    
    with open(path, "rb") as f_obj:
        files = {
            "file": (base_name, f_obj, "application/octet-stream")
        }
        file_upload = session.post(f"{host}/api/v1/submissions/{repo}/files", data=files_data, files=files, headers=headers, verify=False, timeout=60)
        
    print(file_upload.text)
    
    # Extraer ID del archivo
    file_id = None
    try:
        j = file_upload.json()
        file_id = str(j.get("id") or j.get("fileId"))
    except:
        pass
    if not file_id:
        file_id = file_upload.text.split('_href":"')[1].split('"')[0].replace(r"\/", "/").split("/")[-1]
        
    return file_id

async def delete_cloud(fileId, up):
    global ghost, grepo
    host = ghost.rstrip("/")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    csrfToken = up.get(f"{host}/submission/wizard/2?submissionId={grepo}", headers=headers, verify=False).text.split('csrfToken":"')[1].split('",')[0]
    up.post(f"{host}/api/v1/submissions/{grepo}/files/{fileId}?stageId=1", headers={"User-Agent": headers["User-Agent"], "x-http-method-override": "DELETE", "x-requested-with": "XMLHttpRequest", "x-csrf-token": csrfToken}, verify=False)

bot = TelegramClient('BitZerOT', api_id, api_hash).start(bot_token=bot_token)
if not os.path.exists("./database"):
    os.mkdir("./database")

@bot.on(events.NewMessage)
async def techdev_bot(event):
    global users, nubes, cola_download, bitzero, ghost, guser, gpass, grepo, zips, start_msg, cc, timed
    text = event.raw_text or ""
    user_id = event.message.chat.id
    msg_id = event.message.id
    username = event.message.chat.username or ""
    
    current = 0
    user_nube = 0
    for n in nubes:
        if n["user"] == user_id:
            user_nube = current
            break
        else:
            current += 1
            
    if user_nube >= len(nubes):
        nubes.append({"user": user_id, "nube": []})
        user_nube = len(nubes) - 1
    nube = nubes[user_nube]
    
    if not os.path.exists("./database/" + str(user_id)):
        os.mkdir("./database/" + str(user_id))
        os.mkdir("./database/" + str(user_id) + "/files")
        open("./database/" + str(user_id) + "/log", "w").write("[!] USUARIO CREADO\n")
        open("./database/" + str(user_id) + "/cd", "w").write("./database/" + str(user_id) + "/files")
    
    open("./database/" + str(user_id) + "/log", "w").write(f"[!] {msg_id} | {text}\n")
    cd = os.path.normpath(open("./database/" + str(user_id) + "/cd", "r").read())
    size_local = getsize_path(cd)
    sobrepaso = (size_local >= space_local * 1024 * 1024 * 1024) if space_control else False

    # 1. COMANDO /START
    if '/start' == text and isuser(user_id):
        local_files = sorted(os.listdir(cd))
        local_files_text = ""
        listar = 0
        cloud_size = 0
        for nub in nubes[user_nube]["nube"]:
            cloud_size += nub["size"]
        for dir in local_files:
            if os.path.isfile(cd + "/" + dir):
                local_files_text += str(listar) + " 📄 " + dir + "\n"
            else:
                local_files_text += "<b><i>" + str(listar) + "</i></b> 📂 <code>" + dir + "</code>\n"
            listar += 1
        if len(local_files) == 0:
            local_files_text += "🤷🏻‍♂️<i>Sin Archivos</i>\n"
        if start_msg == "":
            await bot.send_message(user_id, f"<b><-- BitZero [PkP] --></b>\n\n<b>☁️ Nube:</b> <code>{ghost}</code>\n<b>👤 Usuario:</b> <code>{guser}</code>\n<b>🔐 Contraseña:</b> <i>********</i>\n<b>📂 Repo:</b> <code>{grepo}</code>\n<b>🔼 BitZero:</b> <code>{bitzero}</code>\n📚 <b>Zips:</b> <code>{zips}</code>\n\n<i>Acerca de:</i> /about\n<i>Creado por:</i> @l_tech_dev_l", parse_mode="HTML")
        else:
            await bot.send_message(user_id, f"<b><-- BitZero [PkP] --></b>\n\n{start_msg}\n\n<i>Acerca de:</i> /about\n<i>Creado por:</i> @l_tech_dev_l", parse_mode="HTML")
    
    elif (sobrepaso and isuser(user_id)) and not ("/ls" == text or "/rm " in text or "/up " in text):
        await bot.send_message(user_id, f"<b>⚠️Almacenamiento lleno:</b><code>{sizeof_fmt(size_local)} / {sizeof_fmt(space_local*1024*1024*1024)}</code>\n<i>Use el comando /rm para eliminar.</i>", parse_mode="HTML")
    
    # 2. COMANDO /LS
    elif "/ls" == text and isuser(user_id):
        size_files = sizeof_fmt(getsize_path(cd))
        local_files = sorted(os.listdir(cd))
        local_files_text = f"<b>Usado: </b><code>{size_files} / {sizeof_fmt(space_local*1024*1024*1024)}</code>\n\n"
        listar = 0
        for dir in local_files:
            if os.path.isfile(cd + "/" + dir):
                size = os.path.getsize(cd + "/" + dir)
                local_files_text += str(listar) + " 📄 <code>" + dir + f"</code> | {sizeof_fmt(size)}\n"
            else:
                local_files_text += "<b><i>" + str(listar) + "</i></b> 📂 <code>" + dir + "</code>\n"
            listar += 1
        if len(local_files) == 0:
            local_files_text += "🤷🏻‍♂️<i>Sin Archivos</i>\n"
        await bot.send_message(user_id, f"[✓] #ls #local\n\n{local_files_text}", parse_mode="HTML")
    
    # 3. COMANDO /SET_CLOUD
    elif "/set_cloud " in text and user_id == users[0]:
        ghost = text.split(" ")[1].rstrip("/")
        guser = text.split(" ")[2]
        gpass = text.split(" ")[3]
        grepo = text.split(" ")[4]
        await bot.send_message(user_id, f"[✓] #cloud_change #local #creado\n\n<code>Editado!!</code>", parse_mode="HTML")
    
    elif "/mkdir" in text and isuser(user_id):
        path = text.replace("/mkdir ", "")
        os.mkdir(cd + "/" + path)
        await bot.send_message(user_id, f"[✓] #mkdir #local\n\n<code>Directorio generado</code>", parse_mode="HTML")
    
    elif "/rm " in text and isuser(user_id):
        local_files = sorted(os.listdir(cd))
        if "-" in text:
            lisc = list(range(int(text.split("-")[0].split(" ")[1]), int(text.split("-")[1].split(" ")[0]) + 1))
            text = "/rm " + ' '.join(map(str, lisc))
        elif "all" in text:
            text = "/rm " + ' '.join(map(str, list(range(0, len(local_files)))))
        rm = text.replace("/rm ", "").split(" ")
        for r in rm:
            try:
                unlink(cd + "/" + local_files[int(r)])
            except:
                await bot.send_message(user_id, f"[×] #rm #local\n\n<code>Directorio {r} inexistente</code>", parse_mode="HTML")
        await bot.send_message(user_id, f"[✓] #rm #local\n\n<code>Directorio/s eliminado/s</code>", parse_mode="HTML")
    
    elif "/cwd" == text:
        await bot.send_message(user_id, "[✓] #cwd #local\n\n<code>" + cd.replace('database/' + str(user_id) + '/files', '$' + str(user_id) + ':') + "</code>", parse_mode="HTML")
    
    elif "/zips " in text:
        tam = text.replace("/zips ", "").strip()
        zips = tam
        await bot.send_message(user_id, f"[✓] #zips #local\n\n<code>Tamaño de zips cambiado a {sizeof_fmt(parse_split_size(tam))}!!</code>", parse_mode="HTML")
    
    elif "/cd " in text and isuser(user_id):
        local_files = sorted(os.listdir(cd))
        cdc = text.split(" ")[1]
        if cdc == "..":
            if not f"database/{user_id}/files" == cd:
                cd = os.path.dirname(cd)
                open("./database/" + str(user_id) + "/cd", "w").write(cd)
                await bot.send_message(user_id, f"[✓] #cd #local\n\n<code>Directorio cambiado</code>", parse_mode="HTML")
            else:
                await bot.send_message(user_id, f"[✓] #cd #local\n\n<code>Ya está en root!</code>", parse_mode="HTML")
        else:
            try:
                cd = cd + "/" + local_files[int(cdc)]
                open("./database/" + str(user_id) + "/cd", "w").write(cd)
                await bot.send_message(user_id, f"[✓] #cd #local\n\n<code>Directorio cambiado</code>", parse_mode="HTML")
            except:
                await bot.send_message(user_id, f"[×] #cd #local\n\n<code>No existe el directorio!</code>", parse_mode="HTML")
    
    # 4. DESCARGA DE ENLACES HTTP / HTTPS DIRECTOS
    elif ("http://" in text or "https://" in text) and not (" https://" in text or " http://" in text) and isuser(user_id):
        url = text.strip()
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply(f"[•] #wget #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        c = 0
        msg_id_curr = msg.id
        while True:
            w = wait_process(pid)
            if procesos[0] == pid:
                await bot.edit_message(user_id, msg_id_curr, f"[•] #wget #local\n\n<code>Iniciando solicitud</code>", parse_mode="HTML")
                try:
                    await download_file(url, bot, user_id, msg_id_curr, cd)
                    await bot.edit_message(user_id, msg_id_curr, f"[✓] #wget #local #finalizado\n\n<code>Espere 3 segundos...</code>", parse_mode="HTML")
                    await asyncio.sleep(3)
                    await bot.edit_message(user_id, msg_id_curr, f"[✓] #wget #local #finalizado\n\n<code>Descargado!</code>", parse_mode="HTML")
                    fin_process(pid)
                except Exception as e:
                    fin_process(pid)
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #wget #local #error\n\n<code>Error: {e}</code>", parse_mode="HTML")
                break
            else:
                if not w == c:
                    c = w
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #wget #local\n\n<code>Esperando por {w} procesos</code>", parse_mode="HTML")
                await asyncio.sleep(1)
    
    # 5. DESCARGA DE YOUTUBE
    elif "/yt " in text and isuser(user_id):
        url = text.split(" ")[1]
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply(f"[•] #yt #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        c = 0
        while True:
            w = wait_process(pid)
            if procesos[0] == pid:
                try:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #yt #local\n\n<code>Iniciando solicitud</code>", parse_mode="HTML")
                    async def progress_func(vid, chunk, bytes_remaining):
                        size = vid.filesize
                        title = vid.title
                        p = ((size - bytes_remaining) / size) * 100
                        p_str = str(round(p, 1)) + '%'
                        await bot.edit_message(user_id, msg_id_curr, f"[•] #yt #local #enproceso\n\n<code>{title}</code>\n<code>{p_str} | {sizeof_fmt(size-bytes_remaining)}/{sizeof_fmt(size)}</code>", parse_mode="HTML")
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #yt #local #enproceso\n\n<code>Descargando</code>", parse_mode="HTML")
                    yt = YouTube(url, on_progress_callback=progress_func)
                    filename = yt.title + ".mp4"
                    yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()
                    os.rename(filename, cd + "/" + filename)
                    await bot.edit_message(user_id, msg_id_curr, f"[✓] #yt #local #finalizado\n\n<code>{yt.title}</code>\n<code>Finalizado!!</code>", parse_mode="HTML")
                    fin_process(pid)
                except Exception as e:
                    fin_process(pid)
                    await bot.edit_message(user_id, msg_id_curr, f"[×] #yt #local #error\n\n<code>Error: {e}</code>", parse_mode="HTML")
                break
            else:
                if not w == c:
                    c = w
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #yt #local\n\n<code>Esperando por {w} procesos</code>", parse_mode="HTML")
                await asyncio.sleep(1)

    # 6. DESCARGA DE ARCHIVOS REENVIADOS O SUBIDOS DIRECTAMENTE EN TELEGRAM
    elif event.media and isuser(user_id):
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply(f"[•] #file #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        c = 0
        while True:
            w = wait_process(pid)
            if not cola_download or procesos[0] == pid:
                try:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local\n\n<code>Iniciando solicitud</code>", parse_mode="HTML")
                    filename = ''
                    if hasattr(event.media, 'document') and event.media.document:
                        for attr in event.media.document.attributes:
                            if isinstance(attr, types.DocumentAttributeFilename):
                                filename = attr.file_name
                    if not filename:
                        filename = f"archivo_{int(time.time())}"
                        
                    rename = 2
                    filename_o = filename
                    while os.path.exists(cd + "/" + filename):
                        filename = f"c{rename}_" + filename_o
                        rename += 1
                        
                    file_path = os.path.join(cd, filename)

                    async def downprog(cur_b, tot_b):
                        global timed, cc
                        if cur_b != cc and (time.time() - timed) > 2.5:
                            timed = time.time()
                            cc = cur_b
                            porcentaje = (cur_b / int(tot_b)) * 100
                            barra = "<code>[</code>" + "<b>•</b>" * round(porcentaje / 3.33333) + "<i> </i>" * round((100 - porcentaje) / 3.33333) + "<code>]</code>"
                            await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local #enproceso\n\n<code>{filename}</code>\n\n<i>{round(porcentaje, 1)}%</i>  <b>{sizeof_fmt(cur_b)}|{sizeof_fmt(int(tot_b))}</b>\n{barra}", parse_mode="HTML")

                    await bot.download_media(event.media, file=file_path, progress_callback=downprog)
                    await bot.edit_message(user_id, msg_id_curr, f"[✓] #file #local #finalizado\n\n<code>Espere 3 segundos</code>", parse_mode="HTML")
                    await asyncio.sleep(3)
                    await bot.edit_message(user_id, msg_id_curr, f"[✓] #file #local #finalizado\n\n<code>Descargado!</code>", parse_mode="HTML")
                    fin_process(pid)
                except Exception as e:
                    fin_process(pid)
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local #error\n\n<code>Error: {e}</code>", parse_mode="HTML")
                break
            else:
                if not w == c:
                    c = w
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #file #local\n\n<code>Esperando por {w} procesos</code>", parse_mode="HTML")
                await asyncio.sleep(1)

    # 7. COMANDO /SPLIT
    elif "/split " in text and isuser(user_id):
        local_files = sorted(os.listdir(cd))
        file = local_files[int(text.split(" ")[1])]
        tamano_deseado = text.split(" ")[2]
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply(f"[•] #split #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        while True:
            if procesos[0] == pid:
                try:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #split #local #enproceso #allpower\n\n<code>Dividiendo su archivo...</code>", parse_mode="HTML")
                    await ziper(cd + "/" + file, user_id, msg_id_curr, tamano_deseado)
                    fin_process(pid)
                except Exception as e:
                    fin_process(pid)
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #split #local #error\n\n<code>Error: {e}</code>", parse_mode="HTML")
                break
            await asyncio.sleep(1)

    elif "/mv " in text and isuser(user_id):
        local_files = sorted(os.listdir(cd))
        try:
            file = text.split(" ")[1]
            if "-" in file:
                files = list(range(int(file.split("-")[0]), int(file.split("-")[1]) + 1))
            else:
                files = [file]
            try:
                if text.split(" ")[2] == "..":
                    carpeta = str(os.path.normpath(cd + "/..")) + "/{file_name}"
                else:
                    carpeta = cd + "/" + local_files[int(text.split(" ")[2])] + "/{file_name}"
            except:
                carpeta = cd + "/" + text.split(" ")[2]
            number = 1
            for f in files:
                file_name = local_files[int(f)]
                os.rename(cd + "/" + file_name, carpeta.replace("{file_name}", file_name).replace("##", "{:03d}".format(number)))
                number += 1
            await bot.send_message(user_id, f"[✓] #mv #local\n\n<code>Movido satisfactoriamente!</code>", parse_mode="HTML")
        except:
            await bot.send_message(user_id, f"[×] #mv #local #error\n\n<code>Algún directorio no existe!</code>", parse_mode="HTML")

    elif "/savec" in text and isuser(user_id):
        open("./database/" + str(user_id) + "/cloud_state", "w").write(str(nube))
        await bot.send_message(user_id, f"[✓] #save #cloud\n\n<code>Base de datos guardada!</code>", parse_mode="HTML")

    elif "/url " in text and isuser(user_id):
        if "-" in text:
            lisc = list(range(int(text.split("-")[0].split(" ")[1]), int(text.split("-")[1].split(" ")[0]) + 1))
            text = "/url " + ' '.join(map(str, lisc))
        elif "all" in text:
            text = "/url " + ' '.join(map(str, list(range(0, len(nubes[user_nube]['nube'])))))
        try:
            indexs = text.replace("/url ", "").split(" ")
        except:
            indexs = [text.replace("/url ", "")]
        try:
            if not bitzero == "0":
                msg = ""
                key = base64.b64encode(ghost.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" + base64.b64encode(guser.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" + base64.b64encode(gpass.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" + base64.b64encode(str(grepo).encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#")
                for index in indexs:
                    url = f"bitzero https://bitzero.techdev.cu/{nubes[user_nube]['nube'][int(index)]['size']}-{grepo}/{nubes[user_nube]['nube'][int(index)]['token']}/{bitzero}/{key}/{urllib.parse.quote(nubes[user_nube]['nube'][int(index)]['filename'].replace(' ','_'))}"
                    msg += url + " && "
                msg += "/"
                msg = msg.replace(" && /", "")
                await event.reply(f"[✓] #token #cloud\n\n<code>{msg}</code>", parse_mode="HTML")
            else:
                msg = ""
                for index in indexs:
                    tokens = nubes[user_nube]['nube'][int(index)]['token'].split("-")
                    for fileID in tokens:
                        url = f"{ghost}/$$$call$$$/api/file/file-api/download-file?submissionFileId={fileID}&submissionId={grepo}&stageId=1"
                        msg += url + "\n"
                msg += "/"
                msg = msg.replace("\n/", "")
                name = nubes[user_nube]['nube'][int(index)]["filename"]
                name = name.replace("." + name.split(".")[-1], ".txt")
                open(name, "w").write(msg)
                await bot.send_file(user_id, name)
                os.unlink(name)
        except Exception as e:
            await bot.send_message(user_id, f"[×] #token #cloud #error\n\n<code>Error: {e}</code>", parse_mode="HTML")

    elif "/ziper " in text and isuser(user_id):
        if "-" in text:
            lisc = list(range(int(text.split("-")[0].split(" ")[1]), int(text.split("-")[1].split(" ")[0]) + 1))
            text = "/ziper " + ' '.join(map(str, lisc))
        elif "all" in text:
            text = "/ziper " + ' '.join(map(str, list(range(0, len(local_files)))))
        index = int(text.replace("/ziper ", ""))
        local_files = sorted(os.listdir(cd))
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply("[•] #zip #local\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        while True:
            if procesos[0] == pid:
                try:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #zip #local\n\n<code>COMPRIMIENDO....</code>", parse_mode="HTML")
                    comprimir_carpeta(cd + "/" + local_files[int(index)], cd + "/" + local_files[int(index)] + ".zip")
                    fin_process(pid)
                    await bot.edit_message(user_id, msg_id_curr, f"[✓] #zip #local\n\n<code>{local_files[int(index)]+'.zip'}\n\nComprimido</code>", parse_mode="HTML")
                except Exception as e:
                    fin_process(pid)
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #zip #local #error\n\n<code>Error: {e}</code>", parse_mode="HTML")
                break
            await asyncio.sleep(1)

    elif "/lsc" in text and isuser(user_id):
        files_cloud = ""
        current = 0
        for nub in nubes[user_nube]["nube"]:
            files_cloud += "<code>" + str(current) + "</code> 📄 <b>" + nub["filename"] + "</b>\n"
            current += 1
        if len(nubes[user_nube]["nube"]) == 0:
            files_cloud += "🤷🏻‍♂️Sin archivos"
        await bot.send_message(user_id, f"[✓] #ls #cloud\n\n{files_cloud}", parse_mode="HTML")

    # 8. SUBIDA A LA NUBE (/UP)
    elif "/up " in text and isuser(user_id):
        total_size = sum(nub["size"] for nub in nubes[user_nube]["nube"])
        if total_size >= cloud_space:
            await bot.send_message(user_id, f"[×] #upload #local #error\n\n<code>Nube llena! Borre!</code>", parse_mode="HTML")
            return
        local_files = sorted(os.listdir(cd))
        if "-" in text:
            lisc = list(range(int(text.split("-")[0].split(" ")[1]), int(text.split("-")[1].split(" ")[0]) + 1))
            text = "/up " + ' '.join(map(str, lisc))
        elif "all" in text:
            text = "/up " + ' '.join(map(str, list(range(0, len(local_files)))))
        files = text.replace("/up ", "").split(" ")
        pid = random.randint(10000, 99999)
        new_process(pid)
        msg = await event.reply(f"[•] #upload #local #enproceso\n\n<code>Generando solicitud</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        while True:
            if procesos[0] == pid:
                try:
                    os.makedirs(cd + "/temp", exist_ok=True)
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #upload #local #enproceso\n\n<code>Iniciando solicitud</code>", parse_mode="HTML")
                    for file_idx in files:
                        file_name = local_files[int(file_idx)]
                        size = os.path.getsize(cd + "/" + file_name)
                        await bot.edit_message(user_id, msg_id_curr, f"[•] #upload #local #enproceso\n\n<code>Dividiendo archivo...</code>", parse_mode="HTML")
                        if not bitzero == 0:
                            div = await upload_div(file_name, user_id, msg_id_curr, zips, cd)
                        else:
                            shutil.copy(cd + "/" + file_name, cd + "/temp/" + file_name)
                            div = await ziper(cd + "/temp/" + file_name, user_id, msg_id_curr, zips)
                        
                        fileids = ""
                        total = len(div)
                        current = 0
                        
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
                        up = requests.Session()
                        login_page = up.get(ghost + "/login", headers=headers, verify=False, timeout=30)
                        token_login = BeautifulSoup(login_page.text, "html.parser").find('input', {'name': 'csrfToken'})['value']
                        login_data = {"password": gpass, "remember": 1, "source": "", "username": guser, "csrfToken": token_login}
                        up.post(f"{ghost}/login/signIn", data=login_data, headers=headers, verify=False, timeout=30)

                        for d in div:
                            porcentaje = round((current / total) * 100, 1)
                            current += 1
                            await bot.edit_message(user_id, msg_id_curr, f"[✓] #upload #local #enproceso #allpower\n\n<i>{d}</i>\n\n<code>Subiendo {current}/{total} {porcentaje}%</code>", parse_mode="HTML")
                            upid = await upload(cd + "/temp/" + d, ghost, guser, gpass, grepo, up, msg_id_curr, user_id)
                            fileids += str(upid) + "-"

                        fileids = fileids.rstrip("-")
                        nubes[user_nube]["nube"].append({"filename": file_name, "token": fileids, "size": size})
                        
                        key_enc = (
                            base64.b64encode(ghost.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(guser.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(gpass.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(str(grepo).encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#")
                        )

                        if not bitzero == 0:
                            await event.reply(
                                f"[✓] #upload #local #finalizado\n\n"
                                f"<code>Subido a la nube!\n\n{file_name}</code>\n\n"
                                f"<b>Comando: </b><code>bitzero https://bitzero.techdev.cu/{size}-{grepo}/{fileids}/{bitzero}/{key_enc}/{urllib.parse.quote(file_name.replace(' ', '_'))}</code>",
                                parse_mode="HTML"
                            )
                        else:
                            await event.reply(f"[✓] #upload #local #finalizado\n\n<code>Subido a la nube!\n\n{file_name}</code>", parse_mode="HTML")
                            msg_links = ""
                            for fileID in fileids.split("-"):
                                msg_links += f"{ghost}/$$$call$$$/api/file/file-api/download-file?submissionFileId={fileID}&submissionId={grepo}&stageId=2\n"
                            
                            txt_name = file_name.rsplit(".", 1)[0] + ".txt"
                            open(txt_name, "w").write(msg_links.strip())
                            await bot.send_file(user_id, txt_name)
                            os.unlink(txt_name)

                    await bot.delete_messages(user_id, msg_id_curr)
                    unlink(cd + "/temp")
                    fin_process(pid)
                except Exception as e:
                    fin_process(pid)
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #upload #local #error\n\n<code>Error: {e}</code>", parse_mode="HTML")
                break
            await asyncio.sleep(1)

    elif "/rmc " in text and isuser(user_id):
        msg = await event.reply(f"[•] #rm #cloud #enproceso\n\n<code>Conectando nube...</code>", parse_mode="HTML")
        msg_id_curr = msg.id
        if "-" in text:
            lisc = list(range(int(text.split("-")[0].split(" ")[1]), int(text.split("-")[1].split(" ")[0]) + 1))
            text = "/rmc " + ' '.join(map(str, lisc))
        elif "all" in text:
            text = "/rmc " + ' '.join(map(str, list(range(0, len(nubes[user_nube]['nube'])))))
        files = text.replace("/rmc ", "").split(" ")
        menos = 0
        for f in files:
            try:
                fids_split = nubes[user_nube]['nube'][int(f) - menos]['token'].split("-")
                total = len(fids_split)
                current = 0
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
                up = requests.Session()
                login_page = up.get(ghost + "/login", headers=headers, verify=False)
                token_csrf = BeautifulSoup(login_page.text, "html.parser").find('input', {'name': 'csrfToken'})['value']
                login_data = {"password": gpass, "remember": 1, "source": "", "username": guser, "csrfToken": token_csrf}
                up.post(f"{ghost}/login/signIn", data=login_data, headers=headers, verify=False)
                for t in fids_split:
                    await bot.edit_message(user_id, msg_id_curr, f"[•] #rm #cloud #enproceso\n\n<code>Eliminando {round((current/total)*100,1)}%</code>", parse_mode="HTML")
                    await delete_cloud(t, up)
                    current += 1
                nubes[user_nube]["nube"].pop(int(f) - menos)
                menos += 1
                await bot.edit_message(user_id, msg_id_curr, f"[✓] #rm #cloud #finalizado\n\n<code>Eliminado</code>", parse_mode="HTML")
            except:
                await bot.edit_message(user_id, msg_id_curr, f"[✓] #rm #cloud #error\n\n<code>Error desconocido</code>", parse_mode="HTML")

    elif "/adduser " in text and user_id == users[0]:
        new_u = int(text.split(" ")[1])
        users.append(new_u)
        nubes.append({"user": new_u, "nube": []})
        us = '\n'.join([str(u) for u in users])
        await bot.send_message(user_id, f"[✓] #adduser #local\n\n<code>Usuario añadido</code>\n\n" + us, parse_mode="HTML")

    elif "/rmuser " in text and user_id == users[0]:
        rem_u = int(text.split(" ")[1])
        if rem_u in users:
            users.remove(rem_u)
        nubes = [nb for nb in nubes if nb["user"] != rem_u]
        us = '\n'.join([str(u) for u in users])
        await bot.send_message(user_id, f"[✓] #adduser #local\n\n<code>Usuario eliminado</code>\n\n" + us, parse_mode="HTML")

    elif not isuser(user_id):
        await bot.send_message(user_id, f"[×] #nouser #local #error\n\n<code>Usted no es un usuario de este bot.</code>", parse_mode="HTML")

    elif "/rmp" in text and user_id == users[0]:
        rm_process()
        await bot.send_message(user_id, f"[✓] #rmp #local #eliminado\n\n<code>Eliminados</code>", parse_mode="HTML")

    elif "/off_cola" == text and user_id == users[0]:
        cola_download = False
        await bot.send_message(user_id, f"[✓] #off_cola #local #eliminado\n\n<code>Cola de descarga apagada</code>", parse_mode="HTML")

    elif "/on_cola" == text and user_id == users[0]:
        cola_download = True
        await bot.send_message(user_id, f"[✓] #on_cola #local #creado\n\n<code>Cola de descarga encendida</code>", parse_mode="HTML")

    elif "/bitzero " in text and user_id == users[0]:
        bitzero = int(text.replace("/bitzero ", ""))
        await bot.send_message(user_id, f"[✓] #on_bitzero #local #creado\n\n<code>BitZero {bitzero}</code>", parse_mode="HTML")

    elif "/start_edit " in text and user_id == users[0]:
        start_msg = text.replace("/start_edit ", "")
        await bot.send_message(user_id, f"[✓] #start_edit #local #creado\n\n<code>Editado!!</code>", parse_mode="HTML")

    elif "/about" == text and isuser(user_id):
        await bot.send_message(user_id, f"[✓] #about #local\n\n<b>Comandos:</b>\n\n<code>ls - Ver archivos\nlsc - Ver archivos [Nube]\nrm - Eliminar archivo\nrmc - Eliminar archivo [Nube]\nup - Subir a la nube\nurl - Obtener comando o txt de descarga\nmv - Mover archivo a carpeta\nmkdir - Crear carpeta\nzip - Comprimir carpeta\nsplit - Dividir archivo en partes\nadduser - Añadir usuario [Admin]\nrmuser - Eliminar usuario [Admin]\noff_bitzero - Subida normal\non_bitzero - Subida bitzero\nstart_edit - Editar mensaje de inicio [Admin]\nset_cloud - Cambiar nube [Admin]\nsend - Enviar mensaje a los usuarios [Admin]\nreport - Reportar error al administrador</code>", parse_mode="HTML")

    elif "/send " in text and user_id == users[0]:
        for u in users:
            await bot.send_message(u, text.replace("/send ", ""), parse_mode="HTML")

    elif "/report " in text:
        msg = text.replace("/report ", "")
        await bot.send_message(users[0], f"<b>Nuevo reporte</b>\n<i>Usuario: </i>@{username}\n<i>ID: </i>{user_id}\n\n" + msg, parse_mode="HTML")

# INICIANDO EL CÓDIGO
print("BOT INICIADO")
bot.run_until_disconnected()