# -*- coding: utf-8 -*-
"""
BitZero Bot - Полная стабильная версия с разделением по функциям.
Поддержка чанков: от 100 KiB до 1024 MiB.
"""

# ==============================================================================
# 1. КОНФИГУРАЦИЯ И КОНСТАНТЫ
# ==============================================================================
USERS = [1552965219]  # Первый ID — главный администратор
CLOUD_SPACE_GB = 10
SPACE_CONTROL = True
SPACE_LOCAL_GB = 5
COLA_DOWNLOAD = True
BITZERO = 1

API_ID = 10181262
API_HASH = "f52b5a057b73b9974eaa7403e04907f0"
BOT_TOKEN = "7792120327:AAG4GbQZSNL60E4i6QBOVlbj7k9W_F9JE5o"

START_MSG = "-4116850567"
GHOST = "https://revistatelematica.cujae.edu.cu/index.php/tele"
GUSER = "techdev"
GPASS = "@A1a2a3mo"
GREPO = "634"
ZIPS_DEFAULT = "14m"

# Границы нарезки файлов (100 KiB — 1024 MiB)
MIN_SPLIT_BYTES = 100 * 1024                  # 100 KiB = 102,400 байт
MAX_SPLIT_BYTES = 1024 * 1024 * 1024          # 1024 MiB = 1,073,741,824 байт

BACKUP_FILE = "backup.json"
ACCOUNT_FILE = "account.json"
BACKUP_INTERVAL = 4

# ==============================================================================
# 2. ИМПОРТЫ И ЛОГИРОВАНИЕ
# ==============================================================================
import os
import sys
import time
import json
import base64
import random
import shutil
import zipfile
import asyncio
import logging
import threading
import urllib.parse
from os.path import exists

import aiohttp
import requests
import urllib3
from bs4 import BeautifulSoup
from pytube import YouTube
from telethon.sync import TelegramClient, events, types

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("BitZeroBot")

# ==============================================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (РАЗМЕРЫ, КЛЮЧИ, ФАЙЛОВАЯ СИСТЕМА)
# ==============================================================================
def parse_split_size(valor) -> int:
    """
    Преобразует строку (100k, 14m, 1024m, 1g) или число в байты.
    Строго удерживает значение в диапазоне от 100 KiB до 1024 MiB.
    """
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

def sizeof_fmt(num, suffix="B"):
    """Форматирование байт в человекочитаемый вид."""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi"]:
        if abs(num) < 1024.0:
            return f"{num:3.2f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.2f} Yi{suffix}"

def getsize_path(ruta):
    """Рекурсивный подсчет веса директории."""
    total = 0
    for root, _, files in os.walk(ruta):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total

def unlink(path):
    """Безопасное удаление файла или папки."""
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)

def isuser(u):
    return u in USERS

def make_bitzero_key(ghost_url, user, pwd, repo):
    """Генерация ключа BitZero в формате base64 с заменой символов."""
    def _b64(val):
        return base64.b64encode(str(val).encode("utf-8")).decode("utf-8").replace("==", "@").replace("=", "#")
    return f"{_b64(ghost_url)}-{_b64(user)}-{_b64(pwd)}-{_b64(repo)}"

# ==============================================================================
# 4. СОХРАНЕНИЕ СОСТОЯНИЯ (BACKUP И УЧЕТНАЯ ЗАПИСЬ)
# ==============================================================================
nubes = []

def save_backup_loop():
    global nubes
    while True:
        try:
            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump(nubes, f)
        except Exception as e:
            logger.error(f"Ошибка сохранения backup: {e}")
        time.sleep(BACKUP_INTERVAL)

def load_backup():
    if exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_account_loop():
    global GHOST, GUSER, GPASS, GREPO, BITZERO
    while True:
        try:
            with open(ACCOUNT_FILE, "w", encoding="utf-8") as fa:
                fa.write(f"{GHOST} {GUSER} {GPASS} {GREPO} {BITZERO}")
        except Exception as e:
            logger.error(f"Ошибка сохранения аккаунта: {e}")
        time.sleep(BACKUP_INTERVAL)

def load_account():
    global GHOST, GUSER, GPASS, GREPO, BITZERO
    if exists(ACCOUNT_FILE):
        try:
            with open(ACCOUNT_FILE, "r", encoding="utf-8") as fa:
                parts = fa.read().strip().split(" ")
                if len(parts) >= 4:
                    GHOST, GUSER, GPASS, GREPO = parts[0], parts[1], parts[2], parts[3]
                if len(parts) >= 5:
                    BITZERO = int(parts[4])
        except Exception as e:
            logger.error(f"Ошибка загрузки аккаунта: {e}")

nubes = load_backup()
load_account()

for u in USERS:
    if not any(item.get("user") == u for item in nubes):
        nubes.append({"user": u, "nube": []})

threading.Thread(target=save_backup_loop, daemon=True).start()
threading.Thread(target=save_account_loop, daemon=True).start()

# ==============================================================================
# 5. ОЧЕРЕДЬ ПРОЦЕССОВ
# ==============================================================================
procesos = []

def new_process(pid):
    procesos.append(pid)

def wait_process(pid):
    if len(procesos) > 0 and procesos[0] == pid:
        return True
    return procesos.index(pid) if pid in procesos else 0

def fin_process(pid):
    if pid in procesos:
        procesos.remove(pid)

def rm_process():
    global procesos
    procesos = []

# ==============================================================================
# 6. АРХИВАЦИЯ И НАРЕЗКА ЧАНКОВ (100 KiB - 1024 MiB)
# ==============================================================================
def comprimir_carpeta(nombre_carpeta, nombre_zip):
    with zipfile.ZipFile(nombre_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for raiz, _, archivos in os.walk(nombre_carpeta):
            for archivo in archivos:
                ruta = os.path.join(raiz, archivo)
                zipf.write(ruta, os.path.relpath(ruta, nombre_carpeta))

async def upload_div(ruta_archivo, user_id, msg_id, tamano_parte, cd):
    tamano_parte_bytes = parse_split_size(tamano_parte)
    lista_archivos_divididos = []
    ruta_completa = os.path.join(cd, ruta_archivo)
    tamano_archivo = os.path.getsize(ruta_completa)
    temp_dir = os.path.join(cd, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    if tamano_archivo <= tamano_parte_bytes:
        dest = os.path.join(temp_dir, ruta_archivo)
        shutil.copy(ruta_completa, dest)
        lista_archivos_divididos.append(ruta_archivo)
    else:
        with open(ruta_completa, "rb") as archivo_original:
            numero_parte = 1
            while True:
                contenido_parte = archivo_original.read(tamano_parte_bytes)
                if not contenido_parte:
                    break
                nombre_parte = f"{ruta_archivo}_parte_{numero_parte}"
                with open(os.path.join(temp_dir, nombre_parte), "wb") as archivo_parte:
                    archivo_parte.write(contenido_parte)
                lista_archivos_divididos.append(nombre_parte)
                numero_parte += 1

    return lista_archivos_divididos

async def ziper(file, user_id, msg_id, zips_val):
    file_size = os.path.getsize(file)
    zipy = parse_split_size(zips_val)
    filed = []

    if file_size > zipy:
        mult_file = zipfile.MultiFile(file, zipy)
        zip_obj = zipfile.ZipFile(mult_file, mode="w", compression=zipfile.ZIP_DEFLATED)
        zip_obj.write(file)
        zip_obj.close()
        mult_file.close()

        ti = 1
        await bot.edit_message(user_id, msg_id, "<b>[✓]</b> #seven #local\n\n<code>Dividido</code>", parse_mode="HTML")
        while True:
            file_part = f"{file}.7z.{ti:03d}"
            if exists(file_part):
                filed.append(os.path.basename(file_part))
                ti += 1
            else:
                break
    else:
        filed = [os.path.basename(file)]

    return filed

# ==============================================================================
# 7. СЕТЕВЫЕ ОПЕРАЦИИ (СКАЧИВАНИЕ И ЗАГРУЗКА В ОБЛАКО)
# ==============================================================================
async def download_file(url, bot_instance, user, msg, cd):
    os.makedirs(cd, exist_ok=True)
    size = 0
    timed = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=3600)) as response:
            if response.status == 200:
                file_size = int(response.headers.get("Content-Length", 0))
                try:
                    file_name = response.headers.get("Content-Disposition", "").split('"')[1]
                except Exception:
                    file_name = url.split("/")[-1].split("?")[0] or "downloaded_file"

                if file_name != "":
                    rename = 2
                    filename_o = file_name
                    while os.path.exists(os.path.join(cd, file_name)):
                        file_name = f"c{rename}_{filename_o}"
                        rename += 1

                with open(os.path.join(cd, file_name), "wb") as f:
                    while True:
                        chunk = await response.content.read(1024 * 64)
                        if not chunk:
                            break
                        f.write(chunk)
                        size += len(chunk)
                        if time.time() - timed > 2.0 and file_size > 0:
                            timed = time.time()
                            porcentaje = (size / file_size) * 100
                            barra = "<code>[</code>" + "<b>•</b>" * round(porcentaje / 3.33333) + "<i> </i>" * round((100 - porcentaje) / 3.33333) + "<code>]</code>"
                            await bot_instance.edit_message(
                                user, msg,
                                f"[•] #wget #local #enproceso\n\n<code>{file_name}</code>\n\n<i>{round(porcentaje, 1)}%</i>  <b>{sizeof_fmt(size)}|{sizeof_fmt(file_size)}</b>\n{barra}",
                                parse_mode="HTML"
                            )

async def upload(path, host, username, password, repo, session, chat_id, user_id):
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = host.rstrip("/")

    if BITZERO == 1:
        spypng = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc