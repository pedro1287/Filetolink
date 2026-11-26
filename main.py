# -*- coding: utf-8 -*-
# ==============================================================================
# BOT TELEGRAM BITZERO - ИСПРАВЛЕНА ЗАГРУЗКА НА EDICIONES.UO.EDU.CU
# ==============================================================================

users = [1552965219]
# ПЕРВЫЙ ПОЛЬЗОВАТЕЛЬ — АДМИНИСТРАТОР
cloud_space_gb = 10
space_control = True
space_local = 5
cola_download = True
bitzero = 1
api_id = 10181262
api_hash = 'f52b5a057b73b9974eaa7403e04907f0'
bot_token = "7792120327:AAG4GbQZSNL60E4i6QBOVlbj7k9W_F9JE5o"
start_msg = ""
key = ""
ghost = "https://ediciones.uo.edu.cu/index.php/e1"
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

# Точная 67-байтная сигнатура BitZero 1
PNG_CAMO = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00'
    b'\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'
)

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
        print("BACKUP ИМПОРТИРОВАН")
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
    print("ACCOUNT ИМПОРТИРОВАН")

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
    tamano_parte_bytes = int(tamano_parte_mb) * 1024 * 1024
    lista_archivos_divididos = []
    ruta_completa = os.path.join(cd, ruta_archivo)
    tamano_archivo = os.path.getsize(ruta_completa)
    
    os.makedirs(os.path.join(cd, "temp"), exist_ok=True)

    if tamano_archivo <= tamano_parte_bytes:
        shutil.copy(ruta_completa, os.path.join(cd, "temp", ruta_archivo))
        lista_archivos_divididos.append(ruta_archivo)
    else:
        with open(ruta_completa, 'rb') as archivo_original:
            numero_parte = 1
            while True:
                contenido_parte = archivo_original.read(tamano_parte_bytes)
                if not contenido_parte:
                    break
                nombre_parte = f"{ruta_archivo}_parte_{numero_parte}"
                with open(os.path.join(cd, "temp", nombre_parte), 'wb') as archivo_parte:
                    archivo_parte.write(contenido_parte)
                lista_archivos_divididos.append(nombre_parte)
                numero_parte += 1
    return lista_archivos_divididos

async def ziper(file, user_id, msg_id, zips):
    file_size = os.path.getsize(file)
    zipy = int(zips) * 1024 * 1024
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
                    file_name = f"file_{int(time.time())}"
                
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
                        if time.time() - t_local > 1.2:
                            t_local = time.time()
                            porcentaje = (size / int(file_size)) * 100 if file_size else 0
                            barra = "<code>[</code>" + "<b>•</b>" * round(porcentaje / 5) + "<i> </i>" * round((100 - porcentaje) / 5) + "<code>]</code>"
                            await bot.edit_message(user, msg, f"[•] #wget #local #enproceso\n\n<code>{file_name}</code>\n\n<i>{round(porcentaje, 1)}%</i>  <b>{sizeof_fmt(size)}|{sizeof_fmt(int(file_size)) if file_size else '?'}</b>\n{barra}", parse_mode="HTML")

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
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti']:
        if abs(num) < 1024.0:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.2f Gi%s" % (num, suffix)

def unlink(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

def isuser(u):
    global users
    return u in users

# ==================== ИСПРАВЛЕННАЯ ФУНКЦИЯ UPLOAD ====================
async def upload(path, host, username, password, repo, session, chat_id, user_id):
    global bitzero
    host = host.rstrip("/")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{host}/submission/wizard/2?submissionId={repo}#step-2"
    }

    # Маскировка BitZero
    if bitzero == 1:
        with open(path, "rb") as f_in:
            raw_bytes = f_in.read()
        new_path = path + f"_#{user_id}@bitzero.png"
        with open(new_path, "wb") as f_out:
            f_out.write(PNG_CAMO + raw_bytes)
        if os.path.exists(path):
            os.unlink(path)
        path = new_path
    elif bitzero == 2:
        with open(path, 'rb') as f_in:
            bytes_data = f_in.read()
        base64_data = base64.b64encode(bytes_data).decode('utf-8')
        new_path = path + f"_#{user_id}@bitzero.html"
        with open(new_path, "w", encoding="utf-8") as f_out:
            f_out.write(f'<!DOCTYPE html>\n<html lang="es">\n<bytes>{base64_data}</bytes></html>')
        if os.path.exists(path):
            os.unlink(path)
        path = new_path

    # 1. Получаем CSRF-токен формы отправки
    wizard_url = f"{host}/submission/wizard/2?submissionId={repo}#step-2"
    sub_page = session.get(wizard_url, headers=headers, verify=False, timeout=30)
    
    token = ""
    if '"csrfToken":"' in sub_page.text:
        token = sub_page.text.split('"csrfToken":"')[1].split('"')[0]
    elif 'name="csrfToken"' in sub_page.text:
        soup = BeautifulSoup(sub_page.text, "html.parser")
        inp = soup.find('input', {'name': 'csrfToken'})
        if inp and inp.get('value'):
            token = inp['value']
            
    headers["X-Csrf-Token"] = token
    base_file_name = os.path.basename(path)

    # 2. Поля данных для OJS / OMP
    files_data = {
        "fileStage": "2",
        "name[es_ES]": base_file_name,
        "name[en_US]": base_file_name
    }
    
    # 3. Отправка файла через multipart/form-data
    upload_url = f"{host}/api/v1/submissions/{repo}/files"
    with open(path, "rb") as file_stream:
        files = {
            "file": (base_file_name, file_stream, "application/octet-stream")
        }
        res = session.post(upload_url, data=files_data, files=files, headers=headers, verify=False, timeout=60)

    print(f"[DEBUG UPLOAD RESPONSE]: {res.status_code} | {res.text[:300]}")

    # 4. Надежное извлечение file_id
    file_id = None
    try:
        json_resp = res.json()
        if "id" in json_resp:
            file_id = str(json_resp["id"])
        elif "fileId" in json_resp:
            file_id = str(json_resp["fileId"])
        elif "temporaryFileId" in json_resp:
            file_id = str(json_resp["temporaryFileId"])
    except Exception:
        pass

    if not file_id:
        if '_href":"' in res.text:
            file_id = res.text.split('_href":"')[1].split('"')[0].replace(r"\/", "/").split("/")[-1]
        elif '"id":' in res.text:
            file_id = res.text.split('"id":')[1].split(',')[0].strip()

    if not file_id or not file_id.isdigit():
        raise Exception(f"Сервер отклонил загрузку. Ответ: {res.text[:200]}")

    return file_id

async def delete_cloud(fileId, up):
    global ghost, grepo
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    wizard_url = f"{ghost}/submission/wizard/2?submissionId={grepo}"
    resp = up.get(wizard_url, headers=headers, verify=False, timeout=20)
    csrfToken = ""
    if 'csrfToken":"' in resp.text:
        csrfToken = resp.text.split('csrfToken":"')[1].split('",')[0]
    headers["X-Csrf-Token"] = csrfToken
    headers["X-Http-Method-Override"] = "DELETE"
    up.post(f"{ghost}/api/v1/submissions/{grepo}/files/{fileId}?stageId=2", headers=headers, verify=False, timeout=20)

bot = TelegramClient('BitZerOT_main', api_id, api_hash).start(bot_token=bot_token)
os.makedirs("./database", exist_ok=True)

@bot.on(events.NewMessage)
async def techdev_bot(event):
    global users, nubes, cola_download, bitzero, ghost, guser, gpass, grepo, zips, start_msg
    text = event.raw_text or ""
    user_id = event.message.chat.id
    msg_id = event.message.id
    username = event.message.chat.username or ""

    user_nube = None
    for idx, n in enumerate(nubes):
        if n.get("user") == user_id:
            user_nube = idx
            break

    if user_nube is None:
        nubes.append({"user": user_id, "nube": []})
        user_nube = len(nubes) - 1

    nube = nubes[user_nube]

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

    if '/start' == text and isuser(user_id):
        local_files = sorted(os.listdir(cd))
        local_files_text = ""
        for idx, d in enumerate(local_files):
            if os.path.isfile(os.path.join(cd, d)):
                local_files_text += f"{idx} 📄 {d}\n"
            else:
                local_files_text += f"<b><i>{idx}</i></b> 📂 <code>{d}</code>\n"
        if not local_files:
            local_files_text = "🤷🏻‍♂️<i>Sin Archivos</i>\n"
            
        msg = (
            f"<b><-- BitZero [PkP] --></b>\n\n"
            f"<b>☁️ Nube:</b> <code>{ghost}</code>\n"
            f"<b>👤 Usuario:</b> <code>{guser}</code>\n"
            f"<b>🔐 Contraseña:</b> <i>****</i>\n"
            f"<b>📂 Repo:</b> <code>{grepo}</code>\n"
            f"<b>🔼 BitZero:</b> <code>{bitzero}</code>\n"
            f"📚 <b>Zips:</b> <code>{zips}</code>\n\n"
            f"<i>Acerca de:</i> /about\n<i>Creado por:</i> @l_tech_dev_l"
        ) if not start_msg else f"<b><-- BitZero [PkP] --></b>\n\n{start_msg}\n\n<i>Acerca de:</i> /about"
        await bot.send_message(user_id, msg, parse_mode="HTML")

    elif sobrepaso and isuser(user_id) and not (text == "/ls" or text.startswith("/rm ") or text.startswith("/up ")):
        await bot.send_message(user_id, f"<b>⚠️ Almacenamiento lleno:</b> <code>{sizeof_fmt(size_local)} / {sizeof_fmt(space_local*1024*1024*1024)}</code>\n<i>Use /rm para eliminar.</i>", parse_mode="HTML")

    elif "/ls" == text and isuser(user_id):
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
            ghost = parts[1].rstrip("/")
            guser = parts[2]
            gpass = parts[3]
            grepo = parts[4]
            await bot.send_message(user_id, "[✓] #cloud_change #local #creado\n\n<code>Nube cambiada exitosamente!</code>", parse_mode="HTML")

    elif text.startswith("/up ") and isuser(user_id):
        total_size = sum(nub["size"] for nub in nubes[user_nube]["nube"])
        if total_size >= cloud_space:
            await bot.send_message(user_id, "[×] #upload #local #error\n\n<code>Nube llena! Borre archivos.</code>", parse_mode="HTML")
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
                    
                    for f_idx in indices:
                        file_name = local_files[f_idx]
                        file_full = os.path.join(cd, file_name)
                        file_size = os.path.getsize(file_full)
                        
                        await bot.edit_message(user_id, msg_id_curr, f"[•] #upload #local #enproceso\n\n<code>Dividiendo {file_name}...</code>", parse_mode="HTML")
                        
                        if bitzero != 0:
                            div = await upload_div(file_name, user_id, msg_id_curr, zips, cd)
                        else:
                            shutil.copy(file_full, os.path.join(temp_dir, file_name))
                            div = await ziper(os.path.join(temp_dir, file_name), user_id, msg_id_curr, zips)
                        
                        total_parts = len(div)
                        current_part = 0
                        
                        # Авторизация в OJS
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
                        }
                        up_session = requests.Session()
                        login_page = up_session.get(f"{ghost}/login", headers=headers, verify=False, timeout=30)
                        
                        soup = BeautifulSoup(login_page.text, "html.parser")
                        csrf_inp = soup.find('input', {'name': 'csrfToken'})
                        token_csrf = csrf_inp['value'] if csrf_inp and csrf_inp.get('value') else ""
                        if not token_csrf and '"csrfToken":"' in login_page.text:
                            token_csrf = login_page.text.split('"csrfToken":"')[1].split('"')[0]

                        login_data = {
                            "password": gpass,
                            "remember": 1,
                            "source": "",
                            "username": guser,
                            "csrfToken": token_csrf
                        }
                        up_session.post(f"{ghost}/login/signIn", data=login_data, headers=headers, verify=False, timeout=30)
                        
                        tokens_list = []
                        for part in div:
                            current_part += 1
                            ruta_parte = os.path.join(temp_dir, part)
                            pct = round((current_part / total_parts) * 100, 1)
                            await bot.edit_message(user_id, msg_id_curr, f"[✓] #upload #local #enproceso\n\n<i>{part}</i>\n\n<code>Subiendo {current_part}/{total_parts} ({pct}%)</code>", parse_mode="HTML")
                            
                            fid = await upload(ruta_parte, ghost, guser, gpass, grepo, up_session, msg_id_curr, user_id)
                            tokens_list.append(str(fid))
                            if os.path.exists(ruta_parte):
                                os.unlink(ruta_parte)
                        
                        tokens_str = "-".join(tokens_list)
                        nubes[user_nube]["nube"].append({"filename": file_name, "size": file_size, "token": tokens_str})
                        
                        key_enc = (
                            base64.b64encode(ghost.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(guser.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(gpass.encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#") + "-" +
                            base64.b64encode(str(grepo).encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#")
                        )
                        
                        if bitzero != 0:
                            download_link = f"bitzero https://bitzero.techdev.cu/{file_size}-{grepo}/{tokens_str}/{bitzero}/{key_enc}/{urllib.parse.quote(file_name.replace(' ', '_'))}"
                            await bot.send_message(
                                user_id,
                                f"<b>[✓] #upload #finalizado</b>\n\n"
                                f"📄 <b>Archivo:</b> <code>{file_name}</code>\n"
                                f"📦 <b>Tamaño:</b> <code>{sizeof_fmt(file_size)}</code>\n\n"
                                f"🔗 <b>Comando:</b>\n<code>{download_link}</code>",
                                parse_mode="HTML"
                            )
                        else:
                            txt_content = ""
                            for fileID in tokens_list:
                                txt_content += f"{ghost}/$$$call$$$/api/file/file-api/download-file?submissionFileId={fileID}&submissionId={grepo}&stageId=2\n"
                            txt_name = file_name.rsplit(".", 1)[0] + ".txt"
                            with open(txt_name, "w") as f_txt:
                                f_txt.write(txt_content.strip())
                            await bot.send_file(user_id, txt_name, caption=f"Enlaces directos para: <code>{file_name}</code>", parse_mode="HTML")
                            if os.path.exists(txt_name):
                                os.unlink(txt_name)

                    unlink(temp_dir)
                    await bot.delete_messages(user_id, msg_id_curr)
                except Exception as e:
                    await bot.edit_message(user_id, msg_id_curr, f"[×] #upload #local #error\n\n<code>Error: {e}</code>", parse_mode="HTML")
                    
                fin_process(pid)
                break
            await asyncio.sleep(1)

    elif text.startswith("/zips "):
        zips = int(text.replace("/zips ", "").strip())
        await bot.send_message(user_id, f"[✓] #zips #local\n\n<code>Tamaño de zips cambiado a {zips} MB!!</code>", parse_mode="HTML")

    elif text.startswith("/bitzero ") and user_id == users[0]:
        bitzero = int(text.replace("/bitzero ", "").strip())
        await bot.send_message(user_id, f"[✓] #on_bitzero #local\n\n<code>BitZero configurado en: {bitzero}</code>", parse_mode="HTML")

    elif "/about" == text and isuser(user_id):
        await bot.send_message(user_id, "[✓] #about #local\n\n<code>Comandos disponibles:\n/ls - Listar archivos\n/up - Subir archivo\n/set_cloud - Configurar nube\n/zips - Cambiar partes\n/bitzero - Cambiar modo</code>", parse_mode="HTML")

print("BOT INICIADO Y FUNCIONANDO")
bot.run_until_disconnected()
