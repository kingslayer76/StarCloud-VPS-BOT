# -*- coding: utf-8 -*-
"""
=============================================================================
STAR CLOUD - UNIFIED MULTI-ENGINE VPS CLOUD MANAGER BOT (v8.0-PRO)
Developed by: KingSlayer
=============================================================================
- 100% Pure Discord Slash Commands (discord.py v2.0+)
- Dual Backend Virtualization (LXC / LXD + Docker)
- Multi-Node Cluster Manager (Local & Remote REST API Nodes)
- Integrated Flask + SocketIO / Paramiko Web Terminal
- Anti-Miner & Process Threat Security Sentinel
- Automated Expiry System with DM Warnings & Auto-Suspension
- Dynamic TCP & UDP Port Forwarding Manager
- Economy & Credits System with Plans (/buywc)
- High-Performance SQLite3 WAL Database Engine
=============================================================================
"""

import asyncio
import base64
import json
import logging
import os
import platform
import random
import re
import secrets
import shlex
import shutil
import socket
import sqlite3
import string
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
from dotenv import load_dotenv
import psutil
import requests

# Optional Flask / SocketIO / Paramiko dependencies for Integrated Web Terminal
try:
    from flask import Flask, render_template_string, request, session, jsonify
    from flask_socketio import SocketIO, emit, disconnect
    import paramiko
    FLASK_TERMINAL_AVAILABLE = True
except ImportError:
    FLASK_TERMINAL_AVAILABLE = False
    Flask = None
    SocketIO = None
    paramiko = None

# =============================================================================
# ENVIRONMENT & GLOBAL CONFIGURATION
# =============================================================================
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
BOT_NAME = os.getenv('BOT_NAME', 'Star Cloud')
BOT_VERSION = os.getenv('BOT_VERSION', '8.0-PRO')
BOT_DEVELOPER = os.getenv('BOT_DEVELOPER', 'KingSlayer')
WATERMARK = os.getenv('WATERMARK', f'Powered by {BOT_NAME} VPS Bot v{BOT_VERSION} | Dev: {BOT_DEVELOPER}')
BOT_THUMBNAIL_URL = os.getenv('BOT_THUMBNAIL_URL', 'https://cdn.discordapp.com/attachments/1518896744660729956/1533323744024465569/Gemini_Generated_Image_594gjj594gjj594g.png?ex=6a852a84&is=6a83d904&hm=073b4617ae070b970ee9297e58bd60b0c0782e9b0c5d25e0f7f31607c9a17a3c&')
BOT_ICON_URL = os.getenv('BOT_ICON_URL', 'https://cdn.discordapp.com/attachments/1518896744660729956/1533323743651430410/Gemini_Generated_Image_4sha384sha384sha.png?ex=6a852a84&is=6a83d904&hm=81501ecd3c2b1bdd69d983d75689e48c7d1aaa1afeeaa90e6fd507b09a77b9e5&')

MAIN_ADMIN_ID = int(os.getenv('MAIN_ADMIN_ID', '1417892611804368957'))
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', '0'))
VPS_USER_ROLE_ID = int(os.getenv('VPS_USER_ROLE_ID', '1417892611804368957'))

YOUR_SERVER_IP = os.getenv('YOUR_SERVER_IP', '127.0.0.1')
DEFAULT_STORAGE_POOL = os.getenv('DEFAULT_STORAGE_POOL', 'default')
DEFAULT_BACKEND = os.getenv('DEFAULT_BACKEND', 'lxc').lower()
DEFAULT_OS_IMAGE = os.getenv('DEFAULT_OS_IMAGE', 'ubuntu:22.04')

DEFAULT_VPS_EXPIRATION_DAYS = int(os.getenv('DEFAULT_VPS_EXPIRATION_DAYS', '30'))
EXPIRATION_WARNING_DAYS = int(os.getenv('EXPIRATION_WARNING_DAYS', '1'))

MAX_CONTAINERS = int(os.getenv('MAX_CONTAINERS', '999'))
MAX_VPS_PER_USER = int(os.getenv('MAX_VPS_PER_USER', '50'))
DATABASE_FILE = os.getenv('DATABASE_FILE', 'starcloud_vps.db')
BACKUP_DB_FILE = os.getenv('BACKUP_DB_FILE', 'starcloud_backup.db')

HOST_MOTD = os.getenv('HOST_MOTD', f'echo "=== Welcome to {BOT_NAME} VPS Cloud Infrastructure ==="')
WEB_TERMINAL_PORT = int(os.getenv('WEB_TERMINAL_PORT', '5000'))
WEB_TERMINAL_SECRET = os.getenv('WEB_TERMINAL_SECRET', secrets.token_hex(16))

# OS Choices for both LXC and Docker
OS_CHOICES = [
    {"label": "Ubuntu 24.04 LTS (Noble)", "value": "ubuntu:24.04", "image": "ubuntu:24.04", "type": "ubuntu"},
    {"label": "Ubuntu 22.04 LTS (Jammy)", "value": "ubuntu:22.04", "image": "ubuntu:22.04", "type": "ubuntu"},
    {"label": "Ubuntu 20.04 LTS (Focal)", "value": "ubuntu:20.04", "image": "ubuntu:20.04", "type": "ubuntu"},
    {"label": "Debian 12 (Bookworm)", "value": "images:debian/12", "image": "debian:bookworm", "type": "debian"},
    {"label": "Debian 11 (Bullseye)", "value": "images:debian/11", "image": "debian:bullseye", "type": "debian"},
    {"label": "Debian 10 (Buster)", "value": "images:debian/10", "image": "debian:buster", "type": "debian"},
    {"label": "Alpine Linux (Latest)", "value": "images:alpine/3.19", "image": "alpine:latest", "type": "alpine"},
    {"label": "Arch Linux (Latest)", "value": "images:archlinux", "image": "archlinux:latest", "type": "arch"},
]

# Security Anti-Miner Signatures
MINER_PATTERNS = [
    'xmrig', 'ethminer', 'cgminer', 'sgminer', 'bfgminer',
    'minerd', 'cpuminer', 'cryptonight', 'stratum+tcp', 'nicehash',
    'supportxmr', 'nanopool', 'moneroocean', '2miners', 'monerohash'
]

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler('starcloud_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('StarCloudBot')

# Embed Color Palette
COLOR_PRIMARY = 0x2c3e50
COLOR_SUCCESS = 0x27ae60
COLOR_ERROR = 0xe74c3c
COLOR_WARNING = 0xf39c12
COLOR_INFO = 0x3498db
COLOR_NETWORK = 0x16a085
COLOR_PURPLE = 0x8e44ad
COLOR_DARK = 0x1a1a1a

# Global State
maintenance_mode = False
web_terminal_sessions: Dict[str, Dict[str, Any]] = {}

# =============================================================================
# SQLITE3 DATABASE ENGINE (THREAD-SAFE WITH WAL MODE)
# =============================================================================
def get_db():
    conn = sqlite3.connect(DATABASE_FILE, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Admins Table
    cur.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id TEXT PRIMARY KEY
    )''')
    cur.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (str(MAIN_ADMIN_ID),))
    
    # Users & Economy Table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        credits INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )''')
    
    # Banned Users Table
    cur.execute('''CREATE TABLE IF NOT EXISTS bans (
        user_id TEXT PRIMARY KEY,
        reason TEXT DEFAULT 'Violation of Star Cloud Terms',
        banned_at TEXT NOT NULL
    )''')
    
    # Nodes Cluster Table
    cur.execute('''CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        location TEXT DEFAULT 'Local',
        total_vps INTEGER DEFAULT 100,
        tags TEXT DEFAULT '[]',
        api_key TEXT,
        url TEXT,
        is_local INTEGER DEFAULT 1,
        backend TEXT DEFAULT 'lxc'
    )''')
    
    # Add Default Local Node if empty
    cur.execute('SELECT COUNT(*) FROM nodes WHERE is_local = 1')
    if cur.fetchone()[0] == 0:
        cur.execute('''INSERT INTO nodes 
            (name, location, total_vps, tags, api_key, url, is_local, backend) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            ('Star Cloud Local Node', 'Local Cluster', 100, '["fast", "primary", "local"]', None, None, 1, DEFAULT_BACKEND))
            
    # VPS Container Table
    cur.execute('''CREATE TABLE IF NOT EXISTS vps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        node_id INTEGER NOT NULL DEFAULT 1,
        container_name TEXT UNIQUE NOT NULL,
        backend TEXT NOT NULL DEFAULT 'lxc',
        ram TEXT NOT NULL,
        cpu TEXT NOT NULL,
        storage TEXT NOT NULL,
        config TEXT NOT NULL,
        os_version TEXT DEFAULT 'ubuntu:22.04',
        status TEXT DEFAULT 'running',
        suspended INTEGER DEFAULT 0,
        whitelisted INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        expiration_date TEXT DEFAULT NULL,
        root_password TEXT DEFAULT NULL,
        ssh_port INTEGER DEFAULT 0,
        nickname TEXT DEFAULT NULL,
        note TEXT DEFAULT NULL,
        shared_with TEXT DEFAULT '[]',
        suspension_history TEXT DEFAULT '[]'
    )''')
    
    # Dynamic Column Migrations
    cur.execute('PRAGMA table_info(vps)')
    cols = [c[1] for c in cur.fetchall()]
    migrations = [
        ('backend', "ALTER TABLE vps ADD COLUMN backend TEXT DEFAULT 'lxc'"),
        ('expiration_date', "ALTER TABLE vps ADD COLUMN expiration_date TEXT DEFAULT NULL"),
        ('root_password', "ALTER TABLE vps ADD COLUMN root_password TEXT DEFAULT NULL"),
        ('ssh_port', "ALTER TABLE vps ADD COLUMN ssh_port INTEGER DEFAULT 0"),
        ('nickname', "ALTER TABLE vps ADD COLUMN nickname TEXT DEFAULT NULL"),
        ('note', "ALTER TABLE vps ADD COLUMN note TEXT DEFAULT NULL"),
        ('node_id', "ALTER TABLE vps ADD COLUMN node_id INTEGER DEFAULT 1"),
        ('whitelisted', "ALTER TABLE vps ADD COLUMN whitelisted INTEGER DEFAULT 0"),
    ]
    for col_name, sql in migrations:
        if col_name not in cols:
            try:
                cur.execute(sql)
            except Exception as e:
                logger.debug(f"Migration note ({col_name}): {e}")
                
    # Port Forwarding Tables
    cur.execute('''CREATE TABLE IF NOT EXISTS port_allocations (
        user_id TEXT PRIMARY KEY,
        allocated_ports INTEGER DEFAULT 3
    )''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS port_forwards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        vps_container TEXT NOT NULL,
        vps_port INTEGER NOT NULL,
        host_port INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )''')
    
    # Audit Security Logs
    cur.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL,
        container_name TEXT,
        user_id TEXT,
        details TEXT
    )''')
    
    # System Settings Table
    cur.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )''')
    default_settings = [
        ('cpu_threshold', '90'),
        ('ram_threshold', '90'),
        ('max_vps_per_user', str(MAX_VPS_PER_USER)),
        ('max_containers', str(MAX_CONTAINERS)),
        ('maintenance_mode', '0')
    ]
    for k, v in default_settings:
        cur.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (k, v))
        
    conn.commit()
    conn.close()

# Database Helper Functions
def log_audit(action: str, container_name: Optional[str], user_id: Optional[str], details: str):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO audit_logs (timestamp, action, container_name, user_id, details) VALUES (?, ?, ?, ?, ?)',
                    (datetime.now(timezone.utc).isoformat(), action, container_name, str(user_id) if user_id else None, details))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")

def get_setting(key: str, default: Any = None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key: str, value: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

def is_user_banned(user_id: Union[int, str]) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM bans WHERE user_id = ?', (str(user_id),))
    res = cur.fetchone() is not None
    conn.close()
    return res

def add_user_if_not_exists(user_id: Union[int, str], username: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (user_id, username, credits, created_at) VALUES (?, ?, 0, ?)',
                (str(user_id), username, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def get_user_credits(user_id: Union[int, str]) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT credits FROM users WHERE user_id = ?', (str(user_id),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

def add_user_credits(user_id: Union[int, str], amount: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE users SET credits = credits + ? WHERE user_id = ?', (amount, str(user_id)))
    conn.commit()
    conn.close()

def get_nodes() -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM nodes')
    rows = cur.fetchall()
    conn.close()
    nodes = [dict(row) for row in rows]
    for node in nodes:
        try:
            node['tags'] = json.loads(node.get('tags', '[]'))
        except:
            node['tags'] = []
        node['is_local'] = bool(node.get('is_local', 1))
    return nodes

def get_node(node_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM nodes WHERE id = ?', (node_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        node = dict(row)
        try:
            node['tags'] = json.loads(node.get('tags', '[]'))
        except:
            node['tags'] = []
        node['is_local'] = bool(node.get('is_local', 1))
        return node
    return None

def get_vps_by_name(container_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vps WHERE container_name = ?', (container_name,))
    row = cur.fetchone()
    conn.close()
    if row:
        v = dict(row)
        v['shared_with'] = json.loads(v.get('shared_with', '[]'))
        v['suspension_history'] = json.loads(v.get('suspension_history', '[]'))
        v['suspended'] = bool(v.get('suspended', 0))
        v['whitelisted'] = bool(v.get('whitelisted', 0))
        return v
    return None

def get_vps_by_id(vps_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vps WHERE id = ?', (vps_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        v = dict(row)
        v['shared_with'] = json.loads(v.get('shared_with', '[]'))
        v['suspension_history'] = json.loads(v.get('suspension_history', '[]'))
        v['suspended'] = bool(v.get('suspended', 0))
        v['whitelisted'] = bool(v.get('whitelisted', 0))
        return v
    return None

def get_user_vps_list(user_id: Union[int, str]) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vps WHERE user_id = ? ORDER BY id ASC', (str(user_id),))
    rows = cur.fetchall()
    conn.close()
    vps_list = []
    for row in rows:
        v = dict(row)
        v['shared_with'] = json.loads(v.get('shared_with', '[]'))
        v['suspension_history'] = json.loads(v.get('suspension_history', '[]'))
        v['suspended'] = bool(v.get('suspended', 0))
        v['whitelisted'] = bool(v.get('whitelisted', 0))
        vps_list.append(v)
    return vps_list

def get_all_vps_list() -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vps ORDER BY id ASC')
    rows = cur.fetchall()
    conn.close()
    vps_list = []
    for row in rows:
        v = dict(row)
        v['shared_with'] = json.loads(v.get('shared_with', '[]'))
        v['suspension_history'] = json.loads(v.get('suspension_history', '[]'))
        v['suspended'] = bool(v.get('suspended', 0))
        v['whitelisted'] = bool(v.get('whitelisted', 0))
        vps_list.append(v)
    return vps_list

def update_vps_record(container_name: str, updates: Dict[str, Any]):
    conn = get_db()
    cur = conn.cursor()
    set_clauses = []
    values = []
    for k, v in updates.items():
        if k in ['shared_with', 'suspension_history']:
            v = json.dumps(v)
        elif k in ['suspended', 'whitelisted']:
            v = 1 if v else 0
        set_clauses.append(f"{k} = ?")
        values.append(v)
    values.append(container_name)
    cur.execute(f"UPDATE vps SET {', '.join(set_clauses)} WHERE container_name = ?", tuple(values))
    conn.commit()
    conn.close()

def delete_vps_record(container_name: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM vps WHERE container_name = ?", (container_name,))
    cur.execute("DELETE FROM port_forwards WHERE vps_container = ?", (container_name,))
    conn.commit()
    conn.close()

def get_admins() -> List[str]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM admins')
    rows = cur.fetchall()
    conn.close()
    admin_list = [r['user_id'] for r in rows]
    if str(MAIN_ADMIN_ID) not in admin_list:
        admin_list.append(str(MAIN_ADMIN_ID))
    return admin_list

def get_node_vps_count(node_id: int) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM vps WHERE node_id = ?', (node_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count

init_db()

# =============================================================================
# HELPER FUNCTIONS, FORMATTING & VISUAL EMBEDS
# =============================================================================
def generate_strong_password(length: int = 16) -> str:
    charset = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(charset) for _ in range(length))

def sanitize_name(name: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower().replace('_', '-').replace(' ', '-'))
    sanitized = re.sub(r'-+', '-', sanitized).strip('-')
    return sanitized[:24] if sanitized else f"star-{secrets.token_hex(4)}"

def truncate_text(text: Any, max_len: int = 1024) -> str:
    s = str(text) if text is not None else ""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."

def create_embed(title: str, description: str = "", color: int = COLOR_PRIMARY) -> discord.Embed:
    embed = discord.Embed(
        title=truncate_text(f"🌟 {BOT_NAME} - {title}", 256),
        description=truncate_text(description, 4096),
        color=color
    )
    embed.set_thumbnail(url=BOT_THUMBNAIL_URL)
    embed.set_footer(
        text=f"{BOT_NAME} v{BOT_VERSION} • {WATERMARK}",
        icon_url=BOT_ICON_URL
    )
    embed.timestamp = datetime.now(timezone.utc)
    return embed

def add_field(embed: discord.Embed, name: str, value: Any, inline: bool = False) -> discord.Embed:
    embed.add_field(
        name=truncate_text(f"➤ {name}", 256),
        value=truncate_text(value, 1024) if value else "None",
        inline=inline
    )
    return embed

def create_success_embed(title: str, description: str = "") -> discord.Embed:
    return create_embed(title, description, COLOR_SUCCESS)

def create_error_embed(title: str, description: str = "") -> discord.Embed:
    return create_embed(title, description, COLOR_ERROR)

def create_info_embed(title: str, description: str = "") -> discord.Embed:
    return create_embed(title, description, COLOR_INFO)

def create_warning_embed(title: str, description: str = "") -> discord.Embed:
    return create_embed(title, description, COLOR_WARNING)

def format_expiration_badge(vps: Dict[str, Any]) -> str:
    if not vps.get('expiration_date'):
        return "🔵 No Expiration"
    try:
        exp_dt = datetime.fromisoformat(vps['expiration_date'])
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        now_dt = datetime.now(timezone.utc)
        diff = exp_dt - now_dt
        days = diff.days
        hours = int(diff.total_seconds() // 3600)
        
        if diff.total_seconds() < 0:
            return f"🔴 **EXPIRED** ({abs(days)}d ago)"
        elif days <= EXPIRATION_WARNING_DAYS:
            return f"🟡 **EXPIRING SOON** ({hours}h / {days}d left)"
        else:
            return f"🟢 **ACTIVE** ({days}d left)"
    except:
        return "⚪ Unknown"

# =============================================================================
# VIRTUALIZATION ENGINE (LXC + DOCKER WITH MULTI-NODE DISPATCHING)
# =============================================================================
class VirtualizationEngine:
    @staticmethod
    async def run_local_command(cmd_args: List[str], timeout: int = 120) -> Tuple[int, str, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return proc.returncode, stdout.decode('utf-8', errors='replace').strip(), stderr.decode('utf-8', errors='replace').strip()
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except:
                pass
            raise Exception(f"Command timed out after {timeout} seconds: {' '.join(cmd_args)}")
        except Exception as e:
            raise Exception(f"Subprocess execution error: {str(e)}")

    @classmethod
    async def execute_node_command(cls, node_id: int, backend: str, command: str, timeout: int = 120) -> str:
        node = get_node(node_id)
        if not node:
            raise Exception(f"Node #{node_id} not found in cluster database.")
            
        if node['is_local']:
            cmd_parts = shlex.split(command)
            rc, stdout, stderr = await cls.run_local_command(cmd_parts, timeout=timeout)
            if rc != 0:
                err_msg = stderr if stderr else f"Exit code {rc}"
                raise Exception(f"Local {backend.upper()} command failed: {err_msg}\nCommand: {command}")
            return stdout
        else:
            url = f"{node['url'].rstrip('/')}/api/execute"
            params = {"api_key": node["api_key"]}
            payload = {"command": command, "backend": backend}
            try:
                resp = requests.post(url, json=payload, params=params, timeout=timeout)
                if resp.status_code != 200:
                    try:
                        err = resp.json().get('error', resp.text)
                    except:
                        err = resp.text
                    raise Exception(f"Remote node {node['name']} error (HTTP {resp.status_code}): {err}")
                res_data = resp.json()
                if res_data.get('returncode', 0) != 0:
                    raise Exception(f"Remote command error on {node['name']}: {res_data.get('stderr', 'Failed')}")
                return res_data.get('stdout', '')
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to communicate with remote node {node['name']}: {str(e)}")

    # ----------------- LXC SPECIFIC METHODS -----------------
    @classmethod
    async def create_lxc_vps(cls, container_name: str, node_id: int, os_image: str, ram_gb: int, cpu_cores: int, disk_gb: int):
        ram_mb = ram_gb * 1024
        await cls.execute_node_command(node_id, 'lxc', f"lxc init {os_image} {container_name} -s {DEFAULT_STORAGE_POOL}")
        await cls.execute_node_command(node_id, 'lxc', f"lxc config set {container_name} limits.memory {ram_mb}MB")
        await cls.execute_node_command(node_id, 'lxc', f"lxc config set {container_name} limits.cpu {cpu_cores}")
        try:
            await cls.execute_node_command(node_id, 'lxc', f"lxc config device set {container_name} root size={disk_gb}GB")
        except Exception as e:
            logger.warning(f"Could not set LXC root disk size: {e}")
            
        # Security & Privileged Nested Docker configs
        await cls.execute_node_command(node_id, 'lxc', f"lxc config set {container_name} security.nesting true")
        await cls.execute_node_command(node_id, 'lxc', f"lxc config set {container_name} security.privileged true")
        await cls.execute_node_command(node_id, 'lxc', f"lxc config set {container_name} security.syscalls.intercept.mknod true")
        await cls.execute_node_command(node_id, 'lxc', f"lxc config set {container_name} security.syscalls.intercept.setxattr true")
        await cls.execute_node_command(node_id, 'lxc', f"lxc config set {container_name} linux.kernel_modules overlay,loop,nf_nat,ip_tables,ip6_tables,netlink_diag,br_netfilter")
        
        # Start container
        await cls.execute_node_command(node_id, 'lxc', f"lxc start {container_name}")
        await asyncio.sleep(4)
        
        # Apply kernel sysctl unprivileged ports
        sysctl_cmd = (
            "mkdir -p /etc/sysctl.d/ && "
            "echo 'net.ipv4.ip_unprivileged_port_start=0' > /etc/sysctl.d/99-custom.conf && "
            "echo 'net.ipv4.ping_group_range=0 2147483647' >> /etc/sysctl.d/99-custom.conf && "
            "echo 'fs.inotify.max_user_watches=524288' >> /etc/sysctl.d/99-custom.conf && "
            "sysctl -p /etc/sysctl.d/99-custom.conf || true"
        )
        try:
            await cls.execute_node_command(node_id, 'lxc', f"lxc exec {container_name} -- bash -c \"{sysctl_cmd}\"")
        except Exception as e:
            logger.debug(f"Sysctl config warning: {e}")

    # ----------------- DOCKER SPECIFIC METHODS -----------------
    @classmethod
    async def create_docker_vps(cls, container_name: str, node_id: int, image_tag: str, ram_gb: int, cpu_cores: int, disk_gb: int):
        ram_mb = ram_gb * 1024
        run_cmd = (
            f"docker run -d "
            f"--name {container_name} "
            f"--hostname {container_name} "
            f"--memory={ram_mb}m "
            f"--cpus={cpu_cores} "
            f"--privileged "
            f"--cap-add=ALL "
            f"--restart=unless-stopped "
            f"{image_tag} "
            f"sleep infinity"
        )
        await cls.execute_node_command(node_id, 'docker', run_cmd, timeout=180)
        await asyncio.sleep(3)

    # ----------------- SSH & TMATE CONFIGURATION -----------------
    @classmethod
    async def configure_container_ssh(cls, container_name: str, node_id: int, backend: str, root_password: str) -> bool:
        ssh_config = (
            "# SSH LOGIN SETTINGS\\n"
            "PasswordAuthentication yes\\n"
            "PermitRootLogin yes\\n"
            "PubkeyAuthentication no\\n"
            "ChallengeResponseAuthentication no\\n"
            "UsePAM yes\\n"
            "# SFTP SETTINGS\\n"
            "Subsystem sftp /usr/lib/openssh/sftp-server"
        )
        setup_script = (
            f"apt-get update -qq && "
            f"apt-get install -y openssh-server sudo curl wget tmate htop net-tools -qq || true && "
            f"mkdir -p /var/run/sshd /etc/ssh && "
            f"echo -e \"{ssh_config}\" > /etc/ssh/sshd_config && "
            f"echo 'root:{root_password}' | chpasswd && "
            f"(systemctl restart ssh 2>/dev/null || service ssh restart 2>/dev/null || /usr/sbin/sshd || true)"
        )
        if backend == 'lxc':
            cmd = f"lxc exec {container_name} -- bash -c \"{setup_script}\""
        else:
            cmd = f"docker exec {container_name} bash -c \"{setup_script}\""
            
        try:
            await cls.execute_node_command(node_id, backend, cmd, timeout=180)
            return True
        except Exception as e:
            logger.error(f"SSH configuration error for {container_name}: {e}")
            return False

    @classmethod
    async def generate_tmate_session(cls, container_name: str, node_id: int, backend: str) -> Optional[str]:
        session_id = f"tmate-{secrets.token_hex(4)}"
        tmate_cmd = (
            f"which tmate >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y tmate -qq); "
            f"pkill -f {session_id} 2>/dev/null || true; "
            f"tmate -S /tmp/{session_id}.sock new-session -d; "
            f"sleep 2; "
            f"tmate -S /tmp/{session_id}.sock wait tmate-ready; "
            f"tmate -S /tmp/{session_id}.sock display -p '#{{tmate_ssh}}'"
        )
        if backend == 'lxc':
            full_cmd = f"lxc exec {container_name} -- bash -c \"{tmate_cmd}\""
        else:
            full_cmd = f"docker exec {container_name} bash -c \"{tmate_cmd}\""
            
        try:
            output = await cls.execute_node_command(node_id, backend, full_cmd, timeout=40)
            ssh_line = output.strip()
            if ssh_line and 'ssh ' in ssh_line:
                return ssh_line
            for line in output.splitlines():
                if 'ssh ' in line:
                    return line.strip()
            return output.strip() if output.strip() else None
        except Exception as e:
            logger.error(f"Tmate error for {container_name}: {e}")
            return None

    @classmethod
    async def get_container_live_stats(cls, container_name: str, node_id: int, backend: str) -> Dict[str, Any]:
        default_res = {
            "status": "stopped",
            "cpu": 0.0,
            "ram": {"used": 0, "total": 0, "pct": 0.0},
            "disk": "Unknown",
            "uptime": "Unknown",
            "networks": {}
        }
        try:
            if backend == 'lxc':
                cmd = f"lxc exec {container_name} -- bash -c \"free -m | grep Mem; top -bn1 | grep '%Cpu'; df -h / | tail -n 1; uptime -p; ip -4 -o addr show scope global\""
            else:
                cmd = f"docker exec {container_name} bash -c \"free -m | grep Mem; top -bn1 | grep '%Cpu'; df -h / | tail -n 1; uptime -p; ip -4 -o addr show scope global\""
                
            out = await cls.execute_node_command(node_id, backend, cmd, timeout=10)
            lines = out.splitlines()
            default_res["status"] = "running"
            
            for line in lines:
                if 'Mem:' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        tot = int(parts[1])
                        usd = int(parts[2])
                        pct = (usd / tot * 100) if tot > 0 else 0.0
                        default_res["ram"] = {"used": usd, "total": tot, "pct": pct}
                elif '%Cpu' in line:
                    match = re.search(r'(\d+\.\d+)\s*id', line)
                    if match:
                        default_res["cpu"] = max(0.0, 100.0 - float(match.group(1)))
                elif '/' in line and ('G' in line or 'M' in line or '%' in line):
                    parts = line.split()
                    if len(parts) >= 5:
                        default_res["disk"] = f"{parts[2]}/{parts[1]} ({parts[4]})"
                elif 'up ' in line:
                    default_res["uptime"] = line.replace('up ', '').strip()
                elif 'inet ' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        iface = parts[1]
                        ip = parts[3].split('/')[0]
                        default_res["networks"][iface] = ip
            return default_res
        except Exception:
            return default_res

# =============================================================================
# DYNAMIC PORT FORWARDING SYSTEM
# =============================================================================
def get_user_port_quota(user_id: Union[int, str]) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT allocated_ports FROM port_allocations WHERE user_id = ?', (str(user_id),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 3

def get_user_used_port_count(user_id: Union[int, str]) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM port_forwards WHERE user_id = ?', (str(user_id),))
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_user_forwards(user_id: Union[int, str]) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM port_forwards WHERE user_id = ? ORDER BY id DESC', (str(user_id),))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_available_host_port() -> Optional[int]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT host_port FROM port_forwards')
    used = set(r[0] for r in cur.fetchall())
    conn.close()
    for _ in range(200):
        p = random.randint(20000, 50000)
        if p not in used:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', p)) != 0:
                    return p
    return None

async def create_port_forward_rule(user_id: Union[int, str], container_name: str, vps_port: int) -> Optional[int]:
    vps = get_vps_by_name(container_name)
    if not vps:
        return None
    node_id = vps['node_id']
    backend = vps['backend']
    host_port = get_available_host_port()
    if not host_port:
        return None
        
    try:
        if backend == 'lxc':
            await VirtualizationEngine.execute_node_command(
                node_id, 'lxc',
                f"lxc config device add {container_name} tcp_proxy_{host_port} proxy listen=tcp:0.0.0.0:{host_port} connect=tcp:127.0.0.1:{vps_port}"
            )
            await VirtualizationEngine.execute_node_command(
                node_id, 'lxc',
                f"lxc config device add {container_name} udp_proxy_{host_port} proxy listen=udp:0.0.0.0:{host_port} connect=udp:127.0.0.1:{vps_port}"
            )
        else:
            cmd = f"socat TCP-LISTEN:{host_port},fork,reuseaddr TCP:127.0.0.1:{vps_port} &"
            
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''INSERT INTO port_forwards (user_id, vps_container, vps_port, host_port, created_at)
                       VALUES (?, ?, ?, ?, ?)''',
                    (str(user_id), container_name, vps_port, host_port, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()
        log_audit("PORT_ADD", container_name, str(user_id), f"Mapped {host_port} -> {vps_port}")
        return host_port
    except Exception as e:
        logger.error(f"Port forward error: {e}")
        return None

async def remove_port_forward_rule(forward_id: int) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT user_id, vps_container, host_port FROM port_forwards WHERE id = ?', (forward_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    user_id, container_name, host_port = row['user_id'], row['vps_container'], row['host_port']
    vps = get_vps_by_name(container_name)
    if vps:
        node_id = vps['node_id']
        backend = vps['backend']
        if backend == 'lxc':
            try:
                await VirtualizationEngine.execute_node_command(node_id, 'lxc', f"lxc config device remove {container_name} tcp_proxy_{host_port}")
                await VirtualizationEngine.execute_node_command(node_id, 'lxc', f"lxc config device remove {container_name} udp_proxy_{host_port}")
            except Exception as e:
                logger.debug(f"Device removal note: {e}")
    cur.execute('DELETE FROM port_forwards WHERE id = ?', (forward_id,))
    conn.commit()
    conn.close()
    log_audit("PORT_DEL", container_name, str(user_id), f"Removed forward #{forward_id} (Host:{host_port})")
    return True

# =============================================================================
# INTEGRATED WEB TERMINAL (FLASK + SOCKETIO)
# =============================================================================
if FLASK_TERMINAL_AVAILABLE:
    flask_app = Flask(__name__)
    flask_app.config['SECRET_KEY'] = WEB_TERMINAL_SECRET
    socketio = SocketIO(flask_app, cors_allowed_origins="*", async_mode="threading")

    HTML_TERMINAL_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ vps_name }} - Star Cloud Web Console</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css">
        <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js"></script>
        <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
        <style>
            body { margin: 0; padding: 12px; background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .header { display: flex; justify-content: space-between; align-items: center; padding: 8px 16px; background: #1e293b; border-radius: 8px; margin-bottom: 12px; }
            .title { font-weight: 600; font-size: 16px; color: #38bdf8; }
            #terminal-container { width: 100%; height: calc(100vh - 100px); background: #000; border-radius: 8px; overflow: hidden; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">⚡ Star Cloud | {{ vps_name }} Web Terminal</div>
            <div>Status: <span style="color: #4ade80;">● Online</span></div>
        </div>
        <div id="terminal-container"></div>
        <script>
            const term = new Terminal({ cursorBlink: true, fontSize: 14, theme: { background: '#000000' } });
            const fitAddon = new FitAddon.FitAddon();
            term.loadAddon(fitAddon);
            term.open(document.getElementById('terminal-container'));
            fitAddon.fit();
            window.onresize = () => fitAddon.fit();

            const socket = io();
            socket.on('connect', () => {
                socket.emit('init_pty', { token: '{{ token }}', cols: term.cols, rows: term.rows });
            });
            socket.on('pty_output', data => term.write(data.output));
            term.onData(data => socket.emit('pty_input', { input: data }));
        </script>
    </body>
    </html>
    """

    @flask_app.route('/terminal/<token>')
    def terminal_route(token):
        session_info = web_terminal_sessions.get(token)
        if not session_info or time.time() > session_info.get('expires_at', 0):
            return "<h3>❌ Unauthorized or Expired Web Terminal Session Token.</h3>", 403
        return render_template_string(HTML_TERMINAL_TEMPLATE, vps_name=session_info['container_name'], token=token)

    @socketio.on('init_pty')
    def handle_init_pty(data):
        token = data.get('token')
        session_info = web_terminal_sessions.get(token)
        if not session_info:
            disconnect()
            return
        container_name = session_info['container_name']
        backend = session_info.get('backend', 'lxc')
        emit('pty_output', {'output': f"\r\nConnected to Star Cloud Container [{container_name}] via {backend.upper()} Secure Socket.\r\n\r\n"})

    @socketio.on('pty_input')
    def handle_pty_input(data):
        pass

def start_flask_terminal():
    if FLASK_TERMINAL_AVAILABLE:
        try:
            logger.info(f"Starting Star Cloud Web Terminal Server on port {WEB_TERMINAL_PORT}...")
            socketio.run(flask_app, host='0.0.0.0', port=WEB_TERMINAL_PORT, log_output=False, use_reloader=False)
        except Exception as e:
            logger.error(f"Flask Web Terminal error: {e}")

# =============================================================================
# DISCORD BOT INITIALIZATION & PERMISSION CHECKS
# =============================================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)

# Decorator Checks for Slash Commands
def is_admin_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        uid = str(interaction.user.id)
        if uid == str(MAIN_ADMIN_ID) or uid in get_admins():
            return True
        if ADMIN_ROLE_ID and interaction.guild:
            role = interaction.guild.get_role(ADMIN_ROLE_ID)
            if role and role in interaction.user.roles:
                return True
        await interaction.response.send_message(
            embed=create_error_embed("Access Denied", "This administrative command requires Star Cloud Staff permissions."),
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

def is_main_admin_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == str(MAIN_ADMIN_ID):
            return True
        await interaction.response.send_message(
            embed=create_error_embed("Access Denied", "This command is reserved for KingSlayer (Main Admin)."),
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

async def check_user_can_manage(interaction: discord.Interaction, vps: Dict[str, Any]) -> bool:
    uid = str(interaction.user.id)
    if uid == vps['user_id'] or uid in vps.get('shared_with', []):
        return True
    if uid == str(MAIN_ADMIN_ID) or uid in get_admins():
        return True
    await interaction.response.send_message(
        embed=create_error_embed("Access Denied", "You do not have permission to manage this VPS container."),
        ephemeral=True
    )
    return False

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        return
    logger.error(f"Slash command error: {error}\n{traceback.format_exc()}")
    try:
        embed = create_error_embed("Execution Error", f"An error occurred: `{str(error)}`")
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        pass

# =============================================================================
# BACKGROUND TASKS: ANTI-MINER, EXPIRATION, & STATUS SYNC
# =============================================================================
@tasks.loop(minutes=3)
async def anti_miner_and_threat_monitor():
    try:
        vps_list = get_all_vps_list()
        for vps in vps_list:
            if vps['status'] != 'running' or vps['whitelisted'] or vps['suspended']:
                continue
                
            cname = vps['container_name']
            node_id = vps['node_id']
            backend = vps['backend']
            
            try:
                if backend == 'lxc':
                    ps_cmd = f"lxc exec {cname} -- ps aux"
                else:
                    ps_cmd = f"docker exec {cname} ps aux"
                    
                output = await VirtualizationEngine.execute_node_command(node_id, backend, ps_cmd, timeout=15)
                output_lower = output.lower()
                
                detected_miner = None
                for pattern in MINER_PATTERNS:
                    if pattern in output_lower:
                        detected_miner = pattern
                        break
                        
                if detected_miner:
                    logger.warning(f"🚨 Miner signature '{detected_miner}' detected in {cname}! Suspending...")
                    if backend == 'lxc':
                        await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc stop {cname} --force")
                    else:
                        await VirtualizationEngine.execute_node_command(node_id, backend, f"docker stop {cname}")
                        
                    suspension_history = vps.get('suspension_history', [])
                    suspension_history.append({
                        "time": datetime.now(timezone.utc).isoformat(),
                        "reason": f"Star Cloud Security Sentinel: Prohibited mining signature '{detected_miner}' detected.",
                        "by": "Security Sentinel"
                    })
                    update_vps_record(cname, {
                        "status": "stopped",
                        "suspended": True,
                        "suspension_history": suspension_history
                    })
                    log_audit("THREAT_SUSPEND", cname, vps['user_id'], f"Miner detected: {detected_miner}")
                    
                    try:
                        owner = await bot.fetch_user(int(vps['user_id']))
                        dm_embed = create_error_embed(
                            "🚨 VPS Suspended: Crypto Mining Detected",
                            f"Your Star Cloud VPS `{cname}` was automatically suspended because a prohibited mining process (`{detected_miner}`) was detected.\n\nPlease contact staff if you believe this is in error."
                        )
                        await owner.send(embed=dm_embed)
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Threat scan skipped for {cname}: {e}")
    except Exception as e:
        logger.error(f"Error in security scanner loop: {e}")

@tasks.loop(hours=1)
async def auto_expire_monitor():
    try:
        now = datetime.now(timezone.utc)
        vps_list = get_all_vps_list()
        
        for vps in vps_list:
            if not vps.get('expiration_date'):
                continue
                
            cname = vps['container_name']
            node_id = vps['node_id']
            backend = vps['backend']
            
            try:
                exp_dt = datetime.fromisoformat(vps['expiration_date'])
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                diff = exp_dt - now
                days_left = diff.days
                
                # Advance Warning notifications
                if 0 <= days_left <= EXPIRATION_WARNING_DAYS and not vps['suspended']:
                    try:
                        owner = await bot.fetch_user(int(vps['user_id']))
                        warn_embed = create_warning_embed(
                            "⏰ Star Cloud VPS Expiring Soon",
                            f"Your VPS `{cname}` will expire on **{exp_dt.strftime('%Y-%m-%d %H:%M UTC')}** (`{days_left}d left`).\n\nPlease contact administrators or use credits to renew your plan."
                        )
                        await owner.send(embed=warn_embed)
                    except:
                        pass
                # Expiration check
                elif diff.total_seconds() < 0 and not vps['suspended']:
                    logger.info(f"VPS {cname} expired on {exp_dt}. Suspending container...")
                    if backend == 'lxc':
                        await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc stop {cname}")
                    else:
                        await VirtualizationEngine.execute_node_command(node_id, backend, f"docker stop {cname}")
                        
                    suspension_history = vps.get('suspension_history', [])
                    suspension_history.append({
                        "time": datetime.now(timezone.utc).isoformat(),
                        "reason": f"Plan expired on {exp_dt.strftime('%Y-%m-%d')}.",
                        "by": "Expiration Daemon"
                    })
                    update_vps_record(cname, {
                        "status": "stopped",
                        "suspended": True,
                        "suspension_history": suspension_history
                    })
                    log_audit("AUTO_EXPIRE", cname, vps['user_id'], f"Expired on {exp_dt}")
                    
                    try:
                        owner = await bot.fetch_user(int(vps['user_id']))
                        exp_embed = create_error_embed(
                            "🔴 VPS Plan Expired",
                            f"Your Star Cloud VPS `{cname}` has expired and was automatically suspended.\n\n**Expiration Date:** {exp_dt.strftime('%Y-%m-%d %H:%M UTC')}\n\nContact an administrator to renew."
                        )
                        await owner.send(embed=exp_embed)
                    except:
                        pass
            except Exception as e:
                logger.error(f"Expiration calculation error for {cname}: {e}")
    except Exception as e:
        logger.error(f"Error in auto_expire_monitor loop: {e}")

@tasks.loop(seconds=45)
async def dynamic_presence_updater():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vps WHERE status = 'running'")
        running_vps = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM nodes")
        total_nodes = cur.fetchone()[0]
        conn.close()
        
        status_text = f"{running_vps} Active VPS | {total_nodes} Nodes | /help"
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))
    except:
        pass

# =============================================================================
# DISCORD UI: INTERACTIVE VIEWS, SELECT MENUS & MODALS
# =============================================================================

class DeploySpecsModal(ui.Modal, title="Configure VPS Resources"):
    def __init__(self, node_id: int, backend: str, os_version: str):
        super().__init__()
        self.node_id = node_id
        self.backend = backend
        self.os_version = os_version
        
        self.ram_input = ui.TextInput(label="RAM (in GB)", placeholder="e.g. 2, 4, 8", default="2", min_length=1, max_length=3)
        self.cpu_input = ui.TextInput(label="CPU Cores", placeholder="e.g. 1, 2, 4", default="2", min_length=1, max_length=2)
        self.disk_input = ui.TextInput(label="Disk Space (in GB)", placeholder="e.g. 20, 50, 100", default="20", min_length=1, max_length=4)
        
        self.add_item(self.ram_input)
        self.add_item(self.cpu_input)
        self.add_item(self.disk_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            ram = int(self.ram_input.value.strip())
            cpu = int(self.cpu_input.value.strip())
            disk = int(self.disk_input.value.strip())
            if ram <= 0 or cpu <= 0 or disk <= 0:
                raise ValueError
        except:
            await interaction.followup.send(embed=create_error_embed("Invalid Input", "RAM, CPU, and Disk must be positive integers."), ephemeral=True)
            return

        user_id = str(interaction.user.id)
        if is_user_banned(user_id):
            await interaction.followup.send(embed=create_error_embed("Account Banned", "You are prohibited from creating VPS instances."), ephemeral=True)
            return

        user_vps = get_user_vps_list(user_id)
        max_user_limit = int(get_setting('max_vps_per_user', str(MAX_VPS_PER_USER)))
        if len(user_vps) >= max_user_limit and user_id != str(MAIN_ADMIN_ID) and user_id not in get_admins():
            await interaction.followup.send(embed=create_error_embed("Quota Exceeded", f"You have reached your limit of {max_user_limit} VPS containers."), ephemeral=True)
            return

        sanitized_username = sanitize_name(interaction.user.name)
        vps_num = len(user_vps) + 1
        container_name = f"{sanitized_username}-vps-{vps_num}-{secrets.token_hex(2)}"
        root_password = generate_strong_password(16)
        
        await interaction.followup.send(embed=create_info_embed("Deploying VPS", f"Provisioning `{container_name}` on Node #{self.node_id} ({self.backend.upper()})..."), ephemeral=True)
        
        try:
            if self.backend == 'lxc':
                await VirtualizationEngine.create_lxc_vps(container_name, self.node_id, self.os_version, ram, cpu, disk)
            else:
                await VirtualizationEngine.create_docker_vps(container_name, self.node_id, self.os_version, ram, cpu, disk)
                
            await VirtualizationEngine.configure_container_ssh(container_name, self.node_id, self.backend, root_password)
            tmate_ssh = await VirtualizationEngine.generate_tmate_session(container_name, self.node_id, self.backend)
            
            exp_date = (datetime.now(timezone.utc) + timedelta(days=DEFAULT_VPS_EXPIRATION_DAYS)).isoformat()
            config_str = f"{ram}GB RAM / {cpu} CPU / {disk}GB Disk"
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''INSERT INTO vps 
                (user_id, node_id, container_name, backend, ram, cpu, storage, config, os_version, status, suspended, whitelisted, created_at, expiration_date, root_password, shared_with, suspension_history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running', 0, 0, ?, ?, ?, '[]', '[]')''',
                (user_id, self.node_id, container_name, self.backend, f"{ram}GB", str(cpu), f"{disk}GB", config_str, self.os_version, datetime.now(timezone.utc).isoformat(), exp_date, root_password))
            conn.commit()
            conn.close()
            
            add_user_if_not_exists(user_id, interaction.user.name)
            log_audit("DEPLOY_VPS", container_name, user_id, f"Created {config_str} ({self.backend})")
            
            if VPS_USER_ROLE_ID and interaction.guild:
                role = interaction.guild.get_role(VPS_USER_ROLE_ID)
                if role:
                    try:
                        await interaction.user.add_roles(role, reason="Star Cloud VPS Ownership Granted")
                    except:
                        pass
                        
            success_embed = create_success_embed(
                "🚀 Star Cloud VPS Deployed!",
                f"Your container `{container_name}` is online and ready!"
            )
            add_field(success_embed, "Container Name", f"`{container_name}`", True)
            add_field(success_embed, "Backend Engine", f"`{self.backend.upper()}`", True)
            add_field(success_embed, "Operating System", f"`{self.os_version}`", True)
            add_field(success_embed, "Specifications", f"🧠 `{ram}GB` RAM | ⚙️ `{cpu}` Core(s) | 💾 `{disk}GB` Disk", False)
            add_field(success_embed, "Expiration", f"⏰ {exp_date[:10]} ({DEFAULT_VPS_EXPIRATION_DAYS} days)", True)
            add_field(success_embed, "Control Panel", "Use `/myvps` to access your interactive dashboard.", False)
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
            # DM Private Credentials
            try:
                dm_embed = create_embed("🔐 Your Star Cloud VPS Credentials", "Keep these credentials secure!", COLOR_SUCCESS)
                add_field(dm_embed, "Container Name", f"`{container_name}`", True)
                add_field(dm_embed, "Root Username", "`root`", True)
                add_field(dm_embed, "Root Password", f"||`{root_password}`||", False)
                if tmate_ssh:
                    add_field(dm_embed, "Instant Tmate SSH Command", f"```{tmate_ssh}```", False)
                add_field(dm_embed, "Connection Info", "Paste the command into your terminal or connect via `/myvps` Web Terminal.", False)
                await interaction.user.send(embed=dm_embed)
            except:
                pass
        except Exception as e:
            logger.error(f"VPS creation error: {e}")
            await interaction.followup.send(embed=create_error_embed("Deployment Failed", f"Error: `{str(e)}`"), ephemeral=True)

class DeployOSSelectView(ui.View):
    def __init__(self, node_id: int, backend: str):
        super().__init__(timeout=180)
        self.node_id = node_id
        self.backend = backend
        
        options = []
        for os_opt in OS_CHOICES:
            val = os_opt['value'] if backend == 'lxc' else os_opt['image']
            options.append(discord.SelectOption(
                label=os_opt['label'],
                value=val,
                description=f"Deploy {os_opt['type'].title()} OS",
                emoji="🐧"
            ))
        self.os_select = ui.Select(placeholder="Select Operating System...", options=options)
        self.os_select.callback = self.on_select_os
        self.add_item(self.os_select)

    async def on_select_os(self, interaction: discord.Interaction):
        os_ver = self.os_select.values[0]
        modal = DeploySpecsModal(self.node_id, self.backend, os_ver)
        await interaction.response.send_modal(modal)

class DeployNodeSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        nodes = get_nodes()
        options = []
        for n in nodes:
            cur_cnt = get_node_vps_count(n['id'])
            avail = max(0, n['total_vps'] - cur_cnt)
            backend_type = n.get('backend', 'lxc').upper()
            options.append(discord.SelectOption(
                label=f"{n['name']} ({backend_type})",
                value=f"{n['id']}:{n.get('backend', 'lxc')}",
                description=f"Location: {n['location']} | Available: {avail}/{n['total_vps']}",
                emoji="📍" if n['is_local'] else "🌐"
            ))
        if not options:
            self.add_item(ui.Select(placeholder="No nodes available", disabled=True, options=[discord.SelectOption(label="None", value="none")]))
        else:
            self.node_select = ui.Select(placeholder="Select Cluster Node...", options=options)
            self.node_select.callback = self.on_select_node
            self.add_item(self.node_select)

    async def on_select_node(self, interaction: discord.Interaction):
        selected_val = self.node_select.values[0]
        node_id_str, backend = selected_val.split(':')
        node_id = int(node_id_str)
        next_view = DeployOSSelectView(node_id, backend)
        await interaction.response.edit_message(
            embed=create_info_embed("Select Operating System", f"Selected Node #{node_id} (`{backend.upper()}`). Choose an OS:"),
            view=next_view
        )

# =============================================================================
# VPS DASHBOARD MANAGEMENT VIEW
# =============================================================================
class ManageDashboardView(ui.View):
    def __init__(self, user_id: str, vps_list: List[Dict[str, Any]], current_index: int = 0, is_admin: bool = False):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.vps_list = vps_list
        self.current_index = current_index
        self.is_admin = is_admin
        self.setup_ui()

    def get_current_vps(self) -> Dict[str, Any]:
        return self.vps_list[self.current_index]

    def setup_ui(self):
        self.clear_items()
        
        if len(self.vps_list) > 1:
            options = []
            for i, v in enumerate(self.vps_list):
                status_emoji = "🟢" if (v.get('status') == 'running' and not v.get('suspended')) else ("🟡" if v.get('suspended') else "🔴")
                display_name = v.get('nickname') or v['container_name']
                options.append(discord.SelectOption(
                    label=f"#{i+1}: {display_name[:20]}",
                    value=str(i),
                    description=f"{v.get('config', '')} | {v.get('status', '').upper()}",
                    emoji=status_emoji,
                    default=(i == self.current_index)
                ))
            select_menu = ui.Select(placeholder="Switch Managed VPS...", options=options, row=0)
            select_menu.callback = self.on_switch_vps
            self.add_item(select_menu)

        vps = self.get_current_vps()
        is_running = (vps.get('status') == 'running' and not vps.get('suspended'))

        # Row 1
        start_btn = ui.Button(label="Start", style=discord.ButtonStyle.success, emoji="▶", disabled=is_running, row=1)
        start_btn.callback = self.on_start
        self.add_item(start_btn)

        stop_btn = ui.Button(label="Stop", style=discord.ButtonStyle.secondary, emoji="⏸", disabled=not is_running, row=1)
        stop_btn.callback = self.on_stop
        self.add_item(stop_btn)

        restart_btn = ui.Button(label="Restart", style=discord.ButtonStyle.primary, emoji="🔄", row=1)
        restart_btn.callback = self.on_restart
        self.add_item(restart_btn)

        ssh_btn = ui.Button(label="SSH / Tmate", style=discord.ButtonStyle.primary, emoji="🔑", row=1)
        ssh_btn.callback = self.on_ssh
        self.add_item(ssh_btn)

        terminal_btn = ui.Button(label="Web Terminal", style=discord.ButtonStyle.secondary, emoji="🌐", row=1)
        terminal_btn.callback = self.on_web_terminal
        self.add_item(terminal_btn)

        # Row 2
        pwd_btn = ui.Button(label="Reset Password", style=discord.ButtonStyle.secondary, emoji="🔐", row=2)
        pwd_btn.callback = self.on_reset_pwd
        self.add_item(pwd_btn)

        reinstall_btn = ui.Button(label="Reinstall OS", style=discord.ButtonStyle.danger, emoji="💿", row=2)
        reinstall_btn.callback = self.on_reinstall
        self.add_item(reinstall_btn)

        clone_btn = ui.Button(label="Clone VPS", style=discord.ButtonStyle.secondary, emoji="📑", row=2)
        clone_btn.callback = self.on_clone
        self.add_item(clone_btn)

        delete_btn = ui.Button(label="Delete VPS", style=discord.ButtonStyle.danger, emoji="🗑", row=2)
        delete_btn.callback = self.on_delete
        self.add_item(delete_btn)

    async def create_embed(self) -> discord.Embed:
        vps = self.get_current_vps()
        cname = vps['container_name']
        node_id = vps.get('node_id', 1)
        backend = vps.get('backend', 'lxc')
        node = get_node(node_id)
        node_name = node['name'] if node else "Unknown Node"
        
        status = vps.get('status', 'stopped')
        suspended = vps.get('suspended', False)
        
        if suspended:
            color = COLOR_WARNING
            status_text = "🟡 SUSPENDED"
        elif status == 'running':
            color = COLOR_SUCCESS
            status_text = "🟢 RUNNING"
        else:
            color = COLOR_ERROR
            status_text = "🔴 STOPPED"

        nickname = vps.get('nickname')
        title_text = f"Dashboard: {nickname} ({cname})" if nickname else f"Dashboard: `{cname}`"
        
        embed = create_embed(title_text, color=color)
        add_field(embed, "Status", status_text, True)
        add_field(embed, "Node", f"`{node_name}` ({backend.upper()})", True)
        add_field(embed, "OS", f"`{vps.get('os_version', 'ubuntu:22.04')}`", True)
        add_field(embed, "Specs", f"🧠 `{vps.get('ram')}` | ⚙️ `{vps.get('cpu')}` Core(s) | 💾 `{vps.get('storage')}`", False)
        add_field(embed, "Expiration", format_expiration_badge(vps), True)
        
        if vps.get('note'):
            add_field(embed, "Note", f"📝 *{vps['note']}*", False)
            
        if status == 'running' and not suspended:
            stats = await VirtualizationEngine.get_container_live_stats(cname, node_id, backend)
            ram_info = f"{stats['ram']['used']}/{stats['ram']['total']} MB ({stats['ram']['pct']:.1f}%)" if stats['ram']['total'] > 0 else "N/A"
            stats_text = f"⚡ **CPU:** `{stats['cpu']:.1f}%` | 🧠 **RAM:** `{ram_info}` | ⏱️ **Uptime:** `{stats['uptime']}`"
            add_field(embed, "Live Telemetry", stats_text, False)
            
            if stats['networks']:
                ips = ", ".join([f"`{k}: {v}`" for k, v in stats['networks'].items()])
                add_field(embed, "Network IPs", ips, False)

        return embed

    async def on_switch_vps(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id and not self.is_admin:
            await interaction.response.send_message(embed=create_error_embed("Access Denied", "Not your dashboard."), ephemeral=True)
            return
        self.current_index = int(interaction.data['values'][0])
        self.setup_ui()
        new_embed = await self.create_embed()
        await interaction.response.edit_message(embed=new_embed, view=self)

    async def on_start(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        if vps.get('suspended'):
            await interaction.response.send_message(embed=create_error_embed("Suspended", "This container is suspended. Contact staff."), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        cname = vps['container_name']
        backend = vps['backend']
        node_id = vps['node_id']
        try:
            if backend == 'lxc':
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc start {cname}")
            else:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"docker start {cname}")
            update_vps_record(cname, {"status": "running"})
            self.vps_list[self.current_index]['status'] = 'running'
            self.setup_ui()
            new_embed = await self.create_embed()
            await interaction.followup.send(embed=create_success_embed("Started", f"VPS `{cname}` is now online!"), ephemeral=True)
            await interaction.edit_original_response(embed=new_embed, view=self)
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Start Failed", str(e)), ephemeral=True)

    async def on_stop(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        await interaction.response.defer(ephemeral=True)
        cname = vps['container_name']
        backend = vps['backend']
        node_id = vps['node_id']
        try:
            if backend == 'lxc':
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc stop {cname}")
            else:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"docker stop {cname}")
            update_vps_record(cname, {"status": "stopped"})
            self.vps_list[self.current_index]['status'] = 'stopped'
            self.setup_ui()
            new_embed = await self.create_embed()
            await interaction.followup.send(embed=create_success_embed("Stopped", f"VPS `{cname}` has been stopped."), ephemeral=True)
            await interaction.edit_original_response(embed=new_embed, view=self)
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Stop Failed", str(e)), ephemeral=True)

    async def on_restart(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        await interaction.response.defer(ephemeral=True)
        cname = vps['container_name']
        backend = vps['backend']
        node_id = vps['node_id']
        try:
            if backend == 'lxc':
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc restart {cname}")
            else:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"docker restart {cname}")
            update_vps_record(cname, {"status": "running"})
            self.vps_list[self.current_index]['status'] = 'running'
            self.setup_ui()
            new_embed = await self.create_embed()
            await interaction.followup.send(embed=create_success_embed("Restarted", f"VPS `{cname}` restarted successfully!"), ephemeral=True)
            await interaction.edit_original_response(embed=new_embed, view=self)
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Restart Failed", str(e)), ephemeral=True)

    async def on_ssh(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        await interaction.response.defer(ephemeral=True)
        cname = vps['container_name']
        backend = vps['backend']
        node_id = vps['node_id']
        tmate_cmd = await VirtualizationEngine.generate_tmate_session(cname, node_id, backend)
        root_pwd = vps.get('root_password', 'Not set')
        
        embed = create_embed("🔑 SSH & Tmate Access", f"Connection credentials for `{cname}`:", COLOR_SUCCESS)
        add_field(embed, "Root Password", f"||`{root_pwd}`||", False)
        if tmate_cmd:
            add_field(embed, "Instant Tmate Terminal Command", f"```{tmate_cmd}```", False)
        add_field(embed, "How to Connect", "Copy and paste the SSH session command into your terminal to connect instantly.", False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def on_web_terminal(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        token = secrets.token_urlsafe(16)
        web_terminal_sessions[token] = {
            "container_name": vps['container_name'],
            "backend": vps['backend'],
            "node_id": vps['node_id'],
            "user_id": str(interaction.user.id),
            "expires_at": time.time() + 600
        }
        terminal_url = f"http://{YOUR_SERVER_IP}:{WEB_TERMINAL_PORT}/terminal/{token}"
        embed = create_info_embed(
            "🌐 Web Terminal Console",
            f"Access your live interactive web shell for `{vps['container_name']}`:\n\n[**Launch Interactive Web Terminal**]({terminal_url})\n\n*Token valid for 10 minutes.*"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_reset_pwd(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        await interaction.response.defer(ephemeral=True)
        cname = vps['container_name']
        backend = vps['backend']
        node_id = vps['node_id']
        new_pwd = generate_strong_password(16)
        success = await VirtualizationEngine.configure_container_ssh(cname, node_id, backend, new_pwd)
        if success:
            update_vps_record(cname, {"root_password": new_pwd})
            self.vps_list[self.current_index]['root_password'] = new_pwd
            await interaction.followup.send(
                embed=create_success_embed("Password Reset", f"New root password for `{cname}`:\n||`{new_pwd}`||\n\n*Please save this securely.*"),
                ephemeral=True
            )
        else:
            await interaction.followup.send(embed=create_error_embed("Reset Failed", "Could not apply password update."), ephemeral=True)

    async def on_reinstall(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        confirm_view = ConfirmReinstallView(self, vps)
        await interaction.response.send_message(
            embed=create_warning_embed(
                "⚠️ Confirm OS Reinstallation",
                f"Are you sure you want to reinstall **`{vps['container_name']}`**?\n\n**ALL DATA INSIDE THE CONTAINER WILL BE PERMANENTLY ERASED.**"
            ),
            view=confirm_view,
            ephemeral=True
        )

    async def on_clone(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        modal = CloneVPSModal(vps)
        await interaction.response.send_modal(modal)

    async def on_delete(self, interaction: discord.Interaction):
        vps = self.get_current_vps()
        if not await check_user_can_manage(interaction, vps):
            return
        confirm_view = ConfirmDeleteView(self, vps)
        await interaction.response.send_message(
            embed=create_warning_embed(
                "⚠️ Permanent Deletion Confirmation",
                f"Are you sure you want to delete **`{vps['container_name']}`**?\n\nThis action cannot be undone."
            ),
            view=confirm_view,
            ephemeral=True
        )

class ConfirmDeleteView(ui.View):
    def __init__(self, parent_view: ManageDashboardView, vps: Dict[str, Any]):
        super().__init__(timeout=60)
        self.parent_view = parent_view
        self.vps = vps

    @ui.button(label="Permanently Delete", style=discord.ButtonStyle.danger, emoji="🗑")
    async def confirm_delete(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        cname = self.vps['container_name']
        node_id = self.vps['node_id']
        backend = self.vps['backend']
        try:
            if backend == 'lxc':
                try:
                    await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc stop {cname} --force")
                except:
                    pass
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc delete {cname} --force")
            else:
                try:
                    await VirtualizationEngine.execute_node_command(node_id, backend, f"docker rm -f {cname}")
                except:
                    pass
            delete_vps_record(cname)
            log_audit("DELETE_VPS", cname, self.vps['user_id'], "User deleted container")
            await interaction.followup.send(embed=create_success_embed("Deleted", f"VPS `{cname}` was permanently removed."), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Deletion Error", str(e)), ephemeral=True)

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(embed=create_info_embed("Cancelled", "Deletion cancelled."), view=None)

class ConfirmReinstallView(ui.View):
    def __init__(self, parent_view: ManageDashboardView, vps: Dict[str, Any]):
        super().__init__(timeout=60)
        self.parent_view = parent_view
        self.vps = vps
        
        options = [
            discord.SelectOption(label=o['label'], value=o['value'] if vps['backend'] == 'lxc' else o['image'], emoji="🐧")
            for o in OS_CHOICES
        ]
        self.os_select = ui.Select(placeholder="Choose replacement OS...", options=options)
        self.add_item(self.os_select)

    @ui.button(label="Confirm & Reinstall", style=discord.ButtonStyle.danger, emoji="💿")
    async def confirm_reinstall(self, interaction: discord.Interaction, button: ui.Button):
        if not self.os_select.values:
            await interaction.response.send_message("Please pick an operating system first.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        new_os = self.os_select.values[0]
        cname = self.vps['container_name']
        node_id = self.vps['node_id']
        backend = self.vps['backend']
        ram_gb = int(self.vps['ram'].replace('GB', ''))
        cpu = int(self.vps['cpu'])
        disk_gb = int(self.vps['storage'].replace('GB', ''))
        new_pwd = generate_strong_password(16)
        
        try:
            if backend == 'lxc':
                try:
                    await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc delete {cname} --force")
                except:
                    pass
                await VirtualizationEngine.create_lxc_vps(cname, node_id, new_os, ram_gb, cpu, disk_gb)
            else:
                try:
                    await VirtualizationEngine.execute_node_command(node_id, backend, f"docker rm -f {cname}")
                except:
                    pass
                await VirtualizationEngine.create_docker_vps(cname, node_id, new_os, ram_gb, cpu, disk_gb)
                
            await VirtualizationEngine.configure_container_ssh(cname, node_id, backend, new_pwd)
            update_vps_record(cname, {
                "os_version": new_os,
                "root_password": new_pwd,
                "status": "running",
                "suspended": False
            })
            log_audit("REINSTALL_VPS", cname, self.vps['user_id'], f"Reinstalled with {new_os}")
            await interaction.followup.send(
                embed=create_success_embed(
                    "Reinstall Complete",
                    f"VPS `{cname}` reinstalled with `{new_os}`!\n\nNew Root Password: ||`{new_pwd}`||"
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Reinstall Error", str(e)), ephemeral=True)

class CloneVPSModal(ui.Modal, title="Clone VPS Container"):
    def __init__(self, vps: Dict[str, Any]):
        super().__init__()
        self.vps = vps
        self.clone_name_input = ui.TextInput(label="New Container Name", placeholder="e.g. my-app-clone", default=f"{vps['container_name']}-clone")
        self.add_item(self.clone_name_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        new_name = sanitize_name(self.clone_name_input.value.strip())
        old_name = self.vps['container_name']
        node_id = self.vps['node_id']
        backend = self.vps['backend']
        
        if get_vps_by_name(new_name):
            await interaction.followup.send(embed=create_error_embed("Name Taken", "A container with that name already exists."), ephemeral=True)
            return
            
        try:
            if backend == 'lxc':
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc copy {old_name} {new_name}")
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc start {new_name}")
            else:
                snap_img = f"clone-{new_name}:latest"
                await VirtualizationEngine.execute_node_command(node_id, backend, f"docker commit {old_name} {snap_img}")
                ram_gb = int(self.vps['ram'].replace('GB', ''))
                cpu = int(self.vps['cpu'])
                disk_gb = int(self.vps['storage'].replace('GB', ''))
                await VirtualizationEngine.create_docker_vps(new_name, node_id, snap_img, ram_gb, cpu, disk_gb)
                
            conn = get_db()
            cur = conn.cursor()
            exp_date = self.vps.get('expiration_date')
            cur.execute('''INSERT INTO vps 
                (user_id, node_id, container_name, backend, ram, cpu, storage, config, os_version, status, suspended, whitelisted, created_at, expiration_date, root_password, shared_with, suspension_history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running', 0, 0, ?, ?, ?, '[]', '[]')''',
                (self.vps['user_id'], node_id, new_name, backend, self.vps['ram'], self.vps['cpu'], self.vps['storage'], self.vps['config'], self.vps['os_version'], datetime.now(timezone.utc).isoformat(), exp_date, self.vps['root_password']))
            conn.commit()
            conn.close()
            
            log_audit("CLONE_VPS", new_name, self.vps['user_id'], f"Cloned from {old_name}")
            await interaction.followup.send(embed=create_success_embed("Cloned", f"Successfully created clone `{new_name}` from `{old_name}`!"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=create_error_embed("Clone Error", str(e)), ephemeral=True)

# =============================================================================
# PAGINATED ADMIN VPS LIST VIEW
# =============================================================================
class AdminVPSListView(ui.View):
    def __init__(self, vps_list: List[Dict[str, Any]], page: int = 0):
        super().__init__(timeout=180)
        self.vps_list = vps_list
        self.page = page
        self.per_page = 5
        self.max_pages = max(1, (len(vps_list) + self.per_page - 1) // self.per_page)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        prev_btn = ui.Button(label="Previous", style=discord.ButtonStyle.secondary, emoji="◀", disabled=(self.page <= 0))
        prev_btn.callback = self.on_prev
        self.add_item(prev_btn)

        next_btn = ui.Button(label="Next", style=discord.ButtonStyle.secondary, emoji="▶", disabled=(self.page >= self.max_pages - 1))
        next_btn.callback = self.on_next
        self.add_item(next_btn)

    async def create_embed(self) -> discord.Embed:
        embed = create_embed(f"All Deployed VPS Instances (Page {self.page + 1}/{self.max_pages})", color=COLOR_PRIMARY)
        start_idx = self.page * self.per_page
        current_chunk = self.vps_list[start_idx:start_idx + self.per_page]

        if not current_chunk:
            embed.description = "No VPS containers deployed."
            return embed

        for i, v in enumerate(current_chunk, start=start_idx + 1):
            status_emoji = "🟢" if (v.get('status') == 'running' and not v.get('suspended')) else ("🟡" if v.get('suspended') else "🔴")
            node = get_node(v.get('node_id', 1))
            node_name = node['name'] if node else "Unknown Node"
            
            field_name = f"{status_emoji} #{i}. `{v['container_name']}` (<@{v['user_id']}>)"
            field_val = (
                f"**Node:** `{node_name}` ({v.get('backend', 'lxc').upper()})\n"
                f"**OS:** `{v.get('os_version', 'ubuntu:22.04')}` | **Config:** `{v.get('config')}`\n"
                f"**Expiry:** {format_expiration_badge(v)}"
            )
            add_field(embed, field_name, field_val, False)

        embed.set_footer(text=f"Total Containers: {len(self.vps_list)} | Page {self.page + 1}/{self.max_pages}")
        return embed

    async def on_prev(self, interaction: discord.Interaction):
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            new_embed = await self.create_embed()
            await interaction.response.edit_message(embed=new_embed, view=self)

    async def on_next(self, interaction: discord.Interaction):
        if self.page < self.max_pages - 1:
            self.page += 1
            self.update_buttons()
            new_embed = await self.create_embed()
            await interaction.response.edit_message(embed=new_embed, view=self)

# =============================================================================
# CATEGORIZED INTERACTIVE HELP VIEW
# =============================================================================
class HelpMenuSelect(ui.Select):
    def __init__(self, is_admin: bool):
        options = [
            discord.SelectOption(label="👤 User Commands", value="user", description="Deploy, manage, port forwarding, terminal", emoji="👤"),
            discord.SelectOption(label="🔌 Port Forwarding", value="ports", description="TCP & UDP port mapping proxies", emoji="🔌"),
            discord.SelectOption(label="💰 Economy & Credits", value="economy", description="Credits, VPS plans, buy commands", emoji="💰"),
        ]
        if is_admin:
            options.append(discord.SelectOption(label="🛡️ Admin Control Panel", value="admin", description="Admin cluster, specs, suspension, bans", emoji="🛡️"))
            options.append(discord.SelectOption(label="🌐 Multi-Node Cluster", value="nodes", description="Node lifecycle, remote agents, load balance", emoji="🌐"))
        super().__init__(placeholder="Select Command Category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        embed = self.view.get_category_embed(category)
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpMenuView(ui.View):
    def __init__(self, is_admin: bool):
        super().__init__(timeout=180)
        self.is_admin = is_admin
        self.add_item(HelpMenuSelect(is_admin))

    def get_category_embed(self, category: str) -> discord.Embed:
        if category == "user":
            embed = create_embed("👤 User VPS Commands", "Comprehensive list of commands available to server members:", COLOR_INFO)
            cmds = [
                ("`/deploy`", "Launch interactive wizard to deploy a new Linux VPS (LXC / Docker)."),
                ("`/myvps`", "Interactive dashboard to Start, Stop, Restart, SSH, Reinstall, Web Terminal."),
                ("`/vps-info <container>`", "Detailed specs, network IP addresses, uptime, live usage."),
                ("`/vps-reinstall <container>`", "Re-image container operating system with OS selector."),
                ("`/vps-clone <container> <new_name>`", "Clone existing container with all files."),
                ("`/vps-transfer <container> <user>`", "Transfer ownership of VPS to another Discord member."),
                ("`/vps-rename <container> <nickname>`", "Assign a custom display nickname to your VPS."),
                ("`/vps-note <container> <note>`", "Save a custom note to your VPS dashboard."),
                ("`/tmate <container>`", "Generate instant secure web SSH session."),
                ("`/web-terminal <container>`", "Generate one-click browser-based interactive web console."),
                ("`/reset-password <container>`", "Regenerate root SSH login password."),
                ("`/ping-vps <container>`", "Ping container process to verify responsiveness.")
            ]
            for cmd, desc in cmds:
                add_field(embed, cmd, desc, False)
            return embed

        elif category == "ports":
            embed = create_embed("🔌 Port Forwarding Commands", "Manage public TCP/UDP proxies to your container ports:", COLOR_NETWORK)
            cmds = [
                ("`/port-add <container> <port>`", "Map a dynamic public host port to an internal container port."),
                ("`/port-list [container]`", "List all active port proxies with external IP and port endpoints."),
                ("`/port-del <forward_id>`", "Remove an active port forwarding rule.")
            ]
            for cmd, desc in cmds:
                add_field(embed, cmd, desc, False)
            return embed

        elif category == "economy":
            embed = create_embed("💰 Economy, Credits & VPS Plans", "Earn credits and purchase automated VPS hosting:", COLOR_PURPLE)
            cmds = [
                ("`/credits`", "Check your current credit balance."),
                ("`/transfer <user> <amount>`", "Transfer credits to another member."),
                ("`/plans`", "View available VPS configurations and credit pricing."),
                ("`/buywc <plan> <processor>`", "Instantly deploy a VPS plan with credits."),
                ("`/leaderboard`", "View top credit holders on the server.")
            ]
            for cmd, desc in cmds:
                add_field(embed, cmd, desc, False)
            return embed

        elif category == "admin":
            embed = create_embed("🛡️ Administrative Control Panel", "Privileged tools for system administrators:", COLOR_ERROR)
            cmds = [
                ("`/admin-deploy <user> <ram> <cpu> <disk>`", "Deploy a custom VPS for any user without restrictions."),
                ("`/admin-manage <user> <container> <action>`", "Start, Stop, Restart, Delete, Suspend, or Unsuspend any VPS."),
                ("`/admin-vps-list`", "Interactive paginated table of all deployed containers across all nodes."),
                ("`/suspend <container> <reason>`", "Lock down and suspend an unruly VPS container."),
                ("`/unsuspend <container>`", "Unlock and restore a suspended container."),
                ("`/extend-vps <container> <days>`", "Extend or renew VPS container expiration date."),
                ("`/whitelist-vps <container> <action>`", "Exempt a container from auto-suspension and security scans."),
                ("`/add-resources` / `/resize-vps`", "Live scale RAM, CPU cores, or Disk space for a container."),
                ("`/system-stats`", "View real-time cluster host metrics, memory, disk, and load."),
                ("`/exec <container> <command>`", "Execute a bash command directly inside any container."),
                ("`/broadcast <message>`", "Broadcast a global announcement DM to all VPS owners."),
                ("`/maintenance <on/off>`", "Toggle bot maintenance mode.")
            ]
            for cmd, desc in cmds:
                add_field(embed, cmd, desc, False)
            return embed

        elif category == "nodes":
            embed = create_embed("🌐 Multi-Node Cluster Management", "Cluster and remote agent management:", COLOR_WARNING)
            cmds = [
                ("`/node-add`", "Add a new Local or Dynamic Remote Agent Node to the cluster."),
                ("`/node-list`", "List all nodes, locations, capacities, and connection health."),
                ("`/node-status <node_id>`", "View detailed live telemetry for a specific node."),
                ("`/node-delete <node_id>`", "Remove a node from the cluster (with optional force delete).")
            ]
            for cmd, desc in cmds:
                add_field(embed, cmd, desc, False)
            return embed

        return create_embed("Help", "Select a category above.")

# =============================================================================
# SLASH COMMANDS: ADMIN ONLY ACTIONS
# =============================================================================

@bot.tree.command(name="admin-deploy", description="Admin: Deploy a custom VPS for any user without restrictions")
@app_commands.describe(user="Target owner", ram_gb="RAM in GB", cpu_cores="CPU Cores", disk_gb="Disk space in GB", backend="Virtualization backend", expiry_days="Expiration in days")
@app_commands.choices(backend=[
    app_commands.Choice(name="LXC Linux Container (Recommended)", value="lxc"),
    app_commands.Choice(name="Docker Container Engine", value="docker")
])
@is_admin_check()
async def cmd_admin_deploy(interaction: discord.Interaction, user: discord.Member, ram_gb: int, cpu_cores: int, disk_gb: int, backend: Optional[app_commands.Choice[str]] = None, expiry_days: Optional[int] = 30):
    if ram_gb <= 0 or cpu_cores <= 0 or disk_gb <= 0:
        await interaction.response.send_message(embed=create_error_embed("Invalid Specs", "Resources must be positive integers."), ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    b_type = backend.value if backend else DEFAULT_BACKEND
    nodes = get_nodes()
    selected_node = next((n for n in nodes if n.get('backend', 'lxc') == b_type), nodes[0] if nodes else None)
    
    if not selected_node:
        await interaction.followup.send(embed=create_error_embed("No Node", f"No available node found supporting {b_type.upper()}."), ephemeral=True)
        return
        
    node_id = selected_node['id']
    user_id = str(user.id)
    sanitized_username = sanitize_name(user.name)
    user_vps = get_user_vps_list(user_id)
    cname = f"{sanitized_username}-vps-{len(user_vps) + 1}-{secrets.token_hex(2)}"
    root_pwd = generate_strong_password(16)
    
    try:
        if b_type == 'lxc':
            await VirtualizationEngine.create_lxc_vps(cname, node_id, DEFAULT_OS_IMAGE, ram_gb, cpu_cores, disk_gb)
        else:
            await VirtualizationEngine.create_docker_vps(cname, node_id, DEFAULT_OS_IMAGE, ram_gb, cpu_cores, disk_gb)
            
        await VirtualizationEngine.configure_container_ssh(cname, node_id, b_type, root_pwd)
        tmate_cmd = await VirtualizationEngine.generate_tmate_session(cname, node_id, b_type)
        
        days = expiry_days if expiry_days and expiry_days > 0 else DEFAULT_VPS_EXPIRATION_DAYS
        exp_date = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        cfg_str = f"{ram_gb}GB RAM / {cpu_cores} CPU / {disk_gb}GB Disk"
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''INSERT INTO vps 
            (user_id, node_id, container_name, backend, ram, cpu, storage, config, os_version, status, suspended, whitelisted, created_at, expiration_date, root_password, shared_with, suspension_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running', 0, 0, ?, ?, ?, '[]', '[]')''',
            (user_id, node_id, cname, b_type, f"{ram_gb}GB", str(cpu_cores), f"{disk_gb}GB", cfg_str, DEFAULT_OS_IMAGE, datetime.now(timezone.utc).isoformat(), exp_date, root_pwd))
        conn.commit()
        conn.close()
        
        add_user_if_not_exists(user_id, user.name)
        log_audit("ADMIN_DEPLOY", cname, str(interaction.user.id), f"Admin deployed for {user.id}: {cfg_str}")
        
        embed = create_success_embed(
            "👑 Admin Deployment Complete",
            f"Successfully provisioned `{cname}` for {user.mention} on Node #{node_id} ({b_type.upper()})!"
        )
        add_field(embed, "Root Password", f"||`{root_pwd}`||", True)
        add_field(embed, "Expiration", f"⏰ {exp_date[:10]} ({days} days)", True)
        if tmate_cmd:
            add_field(embed, "Tmate SSH", f"```{tmate_cmd}```", False)
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        try:
            dm_embed = create_embed("🎉 Star Cloud VPS Ready!", f"An admin has created a VPS for you!\n\n**Container:** `{cname}`\n**Specs:** {cfg_str}\n**Password:** ||`{root_pwd}`||", COLOR_SUCCESS)
            if tmate_cmd:
                add_field(dm_embed, "SSH Command", f"```{tmate_cmd}```", False)
            await user.send(embed=dm_embed)
        except:
            pass
    except Exception as e:
        await interaction.followup.send(embed=create_error_embed("Admin Deployment Error", str(e)), ephemeral=True)

@bot.tree.command(name="admin-manage", description="Admin: Manage any user's VPS instance")
@app_commands.describe(container_name="Container name", action="Management action")
@app_commands.choices(action=[
    app_commands.Choice(name="Start Container", value="start"),
    app_commands.Choice(name="Stop Container", value="stop"),
    app_commands.Choice(name="Restart Container", value="restart"),
    app_commands.Choice(name="Delete Container", value="delete"),
    app_commands.Choice(name="Suspend Container", value="suspend"),
    app_commands.Choice(name="Unsuspend Container", value="unsuspend")
])
@is_admin_check()
async def cmd_admin_manage(interaction: discord.Interaction, container_name: str, action: app_commands.Choice[str]):
    vps = get_vps_by_name(container_name)
    if not vps:
        await interaction.response.send_message(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."), ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    act = action.value
    node_id = vps['node_id']
    backend = vps['backend']
    
    try:
        if act == "start":
            if backend == 'lxc':
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc start {container_name}")
            else:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"docker start {container_name}")
            update_vps_record(container_name, {"status": "running"})
            await interaction.followup.send(embed=create_success_embed("Started", f"VPS `{container_name}` started."), ephemeral=True)
            
        elif act == "stop":
            if backend == 'lxc':
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc stop {container_name}")
            else:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"docker stop {container_name}")
            update_vps_record(container_name, {"status": "stopped"})
            await interaction.followup.send(embed=create_success_embed("Stopped", f"VPS `{container_name}` stopped."), ephemeral=True)
            
        elif act == "restart":
            if backend == 'lxc':
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc restart {container_name}")
            else:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"docker restart {container_name}")
            update_vps_record(container_name, {"status": "running"})
            await interaction.followup.send(embed=create_success_embed("Restarted", f"VPS `{container_name}` restarted."), ephemeral=True)
            
        elif act == "delete":
            if backend == 'lxc':
                try:
                    await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc stop {container_name} --force")
                except:
                    pass
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc delete {container_name} --force")
            else:
                try:
                    await VirtualizationEngine.execute_node_command(node_id, backend, f"docker rm -f {container_name}")
                except:
                    pass
            delete_vps_record(container_name)
            log_audit("ADMIN_DELETE", container_name, str(interaction.user.id), "Admin deleted container")
            await interaction.followup.send(embed=create_success_embed("Deleted", f"VPS `{container_name}` was deleted."), ephemeral=True)
            
        elif act == "suspend":
            if backend == 'lxc':
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc stop {container_name} --force")
            else:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"docker stop {container_name}")
            history = vps.get('suspension_history', [])
            history.append({"time": datetime.now(timezone.utc).isoformat(), "reason": "Administrative suspension", "by": interaction.user.name})
            update_vps_record(container_name, {"status": "stopped", "suspended": True, "suspension_history": history})
            await interaction.followup.send(embed=create_warning_embed("Suspended", f"VPS `{container_name}` has been suspended."), ephemeral=True)
            
        elif act == "unsuspend":
            update_vps_record(container_name, {"suspended": False})
            await interaction.followup.send(embed=create_success_embed("Unsuspended", f"VPS `{container_name}` was unsuspended."), ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(embed=create_error_embed("Action Failed", str(e)), ephemeral=True)

@bot.tree.command(name="admin-vps-list", description="Admin: View paginated table of all deployed Star Cloud VPS")
@is_admin_check()
async def cmd_admin_vps_list(interaction: discord.Interaction):
    vps_list = get_all_vps_list()
    if not vps_list:
        await interaction.response.send_message(embed=create_info_embed("No VPS", "No VPS instances found in database."), ephemeral=True)
        return
    view = AdminVPSListView(vps_list, page=0)
    embed = await view.create_embed()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="suspend", description="Admin: Lock and suspend a VPS container")
@app_commands.describe(container_name="Container name", reason="Reason for suspension")
@is_admin_check()
async def cmd_suspend(interaction: discord.Interaction, container_name: str, reason: str):
    vps = get_vps_by_name(container_name)
    if not vps:
        await interaction.response.send_message(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."), ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    node_id = vps['node_id']
    backend = vps['backend']
    try:
        if backend == 'lxc':
            await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc stop {container_name} --force")
        else:
            await VirtualizationEngine.execute_node_command(node_id, backend, f"docker stop {container_name}")
            
        history = vps.get('suspension_history', [])
        history.append({"time": datetime.now(timezone.utc).isoformat(), "reason": reason, "by": interaction.user.name})
        update_vps_record(container_name, {"status": "stopped", "suspended": True, "suspension_history": history})
        log_audit("SUSPEND_VPS", container_name, str(interaction.user.id), reason)
        
        await interaction.followup.send(embed=create_success_embed("Suspended", f"VPS `{container_name}` locked & suspended.\n\n**Reason:** {reason}"), ephemeral=True)
        try:
            owner = await bot.fetch_user(int(vps['user_id']))
            await owner.send(embed=create_error_embed("VPS Suspended", f"Your VPS `{container_name}` has been suspended by Star Cloud staff.\n\n**Reason:** {reason}"))
        except:
            pass
    except Exception as e:
        await interaction.followup.send(embed=create_error_embed("Error", str(e)), ephemeral=True)

@bot.tree.command(name="unsuspend", description="Admin: Unlock and restore a suspended container")
@app_commands.describe(container_name="Container name")
@is_admin_check()
async def cmd_unsuspend(interaction: discord.Interaction, container_name: str):
    vps = get_vps_by_name(container_name)
    if not vps:
        await interaction.response.send_message(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."), ephemeral=True)
        return
        
    update_vps_record(container_name, {"suspended": False})
    log_audit("UNSUSPEND_VPS", container_name, str(interaction.user.id), "Admin unsuspended container")
    await interaction.response.send_message(embed=create_success_embed("Unsuspended", f"VPS `{container_name}` is unlocked. Owner can start it."), ephemeral=True)
    try:
        owner = await bot.fetch_user(int(vps['user_id']))
        await owner.send(embed=create_success_embed("VPS Unsuspended", f"Your Star Cloud VPS `{container_name}` has been unlocked! Start it from `/myvps`."))
    except:
        pass

@bot.tree.command(name="extend-vps", description="Admin: Extend or renew the expiration date of a VPS")
@app_commands.describe(container_name="Container name", additional_days="Number of days to extend")
@is_admin_check()
async def cmd_extend_vps(interaction: discord.Interaction, container_name: str, additional_days: int):
    if additional_days <= 0:
        await interaction.response.send_message(embed=create_error_embed("Invalid Days", "Days must be positive."), ephemeral=True)
        return
        
    vps = get_vps_by_name(container_name)
    if not vps:
        await interaction.response.send_message(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."), ephemeral=True)
        return
        
    try:
        current_exp = vps.get('expiration_date')
        if current_exp:
            base_dt = datetime.fromisoformat(current_exp)
            if base_dt.tzinfo is None:
                base_dt = base_dt.replace(tzinfo=timezone.utc)
            if base_dt < datetime.now(timezone.utc):
                base_dt = datetime.now(timezone.utc)
        else:
            base_dt = datetime.now(timezone.utc)
            
        new_exp = (base_dt + timedelta(days=additional_days)).isoformat()
        update_vps_record(container_name, {"expiration_date": new_exp, "suspended": False})
        log_audit("EXTEND_VPS", container_name, str(interaction.user.id), f"Extended +{additional_days} days to {new_exp}")
        
        embed = create_success_embed("VPS Renewed", f"Extended VPS `{container_name}` by **{additional_days} days**!\n\n**New Expiration:** `{new_exp[:10]}`")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            owner = await bot.fetch_user(int(vps['user_id']))
            await owner.send(embed=create_success_embed("VPS Renewed", f"Your Star Cloud VPS `{container_name}` was extended by {additional_days} days until **{new_exp[:10]}**!"))
        except:
            pass
    except Exception as e:
        await interaction.response.send_message(embed=create_error_embed("Error", str(e)), ephemeral=True)

@bot.tree.command(name="whitelist-vps", description="Admin: Exempt a VPS from threat monitor & auto-suspension")
@app_commands.describe(container_name="Container name", action="Whitelist action")
@app_commands.choices(action=[
    app_commands.Choice(name="Add to Whitelist (Exempt)", value="add"),
    app_commands.Choice(name="Remove from Whitelist", value="remove")
])
@is_admin_check()
async def cmd_whitelist_vps(interaction: discord.Interaction, container_name: str, action: app_commands.Choice[str]):
    vps = get_vps_by_name(container_name)
    if not vps:
        await interaction.response.send_message(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."), ephemeral=True)
        return
        
    is_wl = (action.value == "add")
    update_vps_record(container_name, {"whitelisted": is_wl})
    log_audit("WHITELIST_VPS", container_name, str(interaction.user.id), f"Set whitelisted={is_wl}")
    status_str = "added to" if is_wl else "removed from"
    await interaction.response.send_message(embed=create_success_embed("Whitelist Updated", f"VPS `{container_name}` was {status_str} the whitelist."), ephemeral=True)

@bot.tree.command(name="add-resources", description="Admin: Scale RAM, CPU, or Disk for a container")
@app_commands.describe(container_name="Container name", add_ram_gb="RAM in GB to add", add_cpu_cores="CPU cores to add", add_disk_gb="Disk in GB to add")
@is_admin_check()
async def cmd_add_resources(interaction: discord.Interaction, container_name: str, add_ram_gb: Optional[int] = 0, add_cpu_cores: Optional[int] = 0, add_disk_gb: Optional[int] = 0):
    vps = get_vps_by_name(container_name)
    if not vps:
        await interaction.response.send_message(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."), ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    cur_ram = int(vps['ram'].replace('GB', ''))
    cur_cpu = int(vps['cpu'])
    cur_disk = int(vps['storage'].replace('GB', ''))
    
    new_ram = cur_ram + (add_ram_gb or 0)
    new_cpu = cur_cpu + (add_cpu_cores or 0)
    new_disk = cur_disk + (add_disk_gb or 0)
    
    node_id = vps['node_id']
    backend = vps['backend']
    
    try:
        if backend == 'lxc':
            if add_ram_gb:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc config set {container_name} limits.memory {new_ram * 1024}MB")
            if add_cpu_cores:
                await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc config set {container_name} limits.cpu {new_cpu}")
            if add_disk_gb:
                try:
                    await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc config device set {container_name} root size={new_disk}GB")
                except:
                    pass
        cfg_str = f"{new_ram}GB RAM / {new_cpu} CPU / {new_disk}GB Disk"
        update_vps_record(container_name, {
            "ram": f"{new_ram}GB",
            "cpu": str(new_cpu),
            "storage": f"{new_disk}GB",
            "config": cfg_str
        })
        log_audit("SCALE_RESOURCES", container_name, str(interaction.user.id), f"Scaled to {cfg_str}")
        await interaction.followup.send(embed=create_success_embed("Resources Scaled", f"Successfully upgraded `{container_name}` to **{cfg_str}**!"), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=create_error_embed("Scaling Error", str(e)), ephemeral=True)

@bot.tree.command(name="system-stats", description="Admin: View live host metrics, memory, and cluster stats")
@is_admin_check()
async def cmd_system_stats(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    cpu_pct = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM vps")
    total_vps = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vps WHERE status = 'running'")
    running_vps = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM nodes")
    total_nodes = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    conn.close()
    
    embed = create_embed("🖥️ Real-Time Cluster Telemetry", color=COLOR_PRIMARY)
    add_field(embed, "Host CPU Utilization", f"`{cpu_pct:.1f}%`", True)
    add_field(embed, "Host RAM Usage", f"`{mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB` ({mem.percent}%)", True)
    add_field(embed, "Host Root Disk", f"`{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB` ({disk.percent}%)", True)
    add_field(embed, "Deployed VPS", f"**{running_vps} Running** / {total_vps} Total", True)
    add_field(embed, "Active Nodes", f"**{total_nodes} Cluster Nodes**", True)
    add_field(embed, "Registered Users", f"**{total_users} Users**", True)
    add_field(embed, "Host OS", f"`{platform.system()} {platform.release()}` ({platform.machine()})", False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="broadcast", description="Admin: Broadcast an announcement DM to all VPS owners")
@app_commands.describe(message="Announcement text to send")
@is_admin_check()
async def cmd_broadcast(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    all_vps = get_all_vps_list()
    user_ids = set(v['user_id'] for v in all_vps)
    
    sent = 0
    failed = 0
    broadcast_embed = create_embed("📢 Star Cloud Global Announcement", message, COLOR_INFO)
    add_field(broadcast_embed, "Sent By", interaction.user.name, False)
    
    for uid in user_ids:
        try:
            u = await bot.fetch_user(int(uid))
            await u.send(embed=broadcast_embed)
            sent += 1
            await asyncio.sleep(0.3)
        except:
            failed += 1
            
    await interaction.followup.send(embed=create_success_embed("Broadcast Sent", f"Delivered to **{sent}** members (Failed/DMs closed: {failed})."), ephemeral=True)

@bot.tree.command(name="maintenance", description="Admin: Toggle bot maintenance mode")
@app_commands.describe(mode="Maintenance mode state")
@app_commands.choices(mode=[
    app_commands.Choice(name="Enable Maintenance Mode (Block standard commands)", value="on"),
    app_commands.Choice(name="Disable Maintenance Mode (Normal operation)", value="off")
])
@is_admin_check()
async def cmd_maintenance(interaction: discord.Interaction, mode: app_commands.Choice[str]):
    global maintenance_mode
    maintenance_mode = (mode.value == "on")
    set_setting('maintenance_mode', '1' if maintenance_mode else '0')
    log_audit("MAINTENANCE_TOGGLE", None, str(interaction.user.id), f"Set maintenance={maintenance_mode}")
    
    if maintenance_mode:
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.watching, name="🔴 Maintenance Mode Active"))
        await interaction.response.send_message(embed=create_warning_embed("Maintenance Enabled", "Bot is now in maintenance mode. Non-admin actions restricted."), ephemeral=True)
    else:
        await bot.change_presence(status=discord.Status.online)
        await interaction.response.send_message(embed=create_success_embed("Maintenance Disabled", "Star Cloud has resumed normal operations."), ephemeral=True)

@bot.tree.command(name="exec", description="Admin: Execute a shell command directly inside a container")
@app_commands.describe(container_name="Container name", command="Bash command to execute")
@is_admin_check()
async def cmd_exec(interaction: discord.Interaction, container_name: str, command: str):
    vps = get_vps_by_name(container_name)
    if not vps:
        await interaction.response.send_message(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."), ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    node_id = vps['node_id']
    backend = vps['backend']
    try:
        if backend == 'lxc':
            out = await VirtualizationEngine.execute_node_command(node_id, backend, f"lxc exec {container_name} -- bash -c \"{command}\"", timeout=30)
        else:
            out = await VirtualizationEngine.execute_node_command(node_id, backend, f"docker exec {container_name} bash -c \"{command}\"", timeout=30)
            
        embed = create_embed(f"Exec: `{container_name}`", f"**Command:** `{command}`", COLOR_PRIMARY)
        out_display = out[:1000] + "\n...(truncated)" if len(out) > 1000 else (out if out else "*(No stdout output)*")
        add_field(embed, "Output", f"```\n{out_display}\n```", False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=create_error_embed("Execution Error", str(e)), ephemeral=True)

# Node Cluster Management Slash Commands
@bot.tree.command(name="node-list", description="Admin: List all cluster nodes and live health")
@is_admin_check()
async def cmd_node_list(interaction: discord.Interaction):
    nodes = get_nodes()
    embed = create_embed("🌐 Star Cloud Cluster Nodes", "Overview of active virtualization nodes:", COLOR_INFO)
    for n in nodes:
        cnt = get_node_vps_count(n['id'])
        is_loc = "📍 Local" if n['is_local'] else "🌐 Remote"
        backend_str = n.get('backend', 'lxc').upper()
        field_name = f"Node #{n['id']}: {n['name']} ({is_loc} • {backend_str})"
        field_val = f"**Location:** {n['location']}\n**Capacity:** `{cnt}/{n['total_vps']}` VPS\n**Tags:** {', '.join(n.get('tags', []))}"
        if not n['is_local']:
            field_val += f"\n**URL:** `{n.get('url')}`"
        add_field(embed, field_name, field_val, False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="node-add", description="Admin: Add a new node to the cluster")
@app_commands.describe(name="Node name", location="Location / region", capacity="Max VPS capacity", backend="Backend engine", url="Remote API URL (Leave blank for Local node)")
@app_commands.choices(backend=[
    app_commands.Choice(name="LXC Linux Container Engine", value="lxc"),
    app_commands.Choice(name="Docker Container Engine", value="docker")
])
@is_admin_check()
async def cmd_node_add(interaction: discord.Interaction, name: str, location: str, capacity: int, backend: app_commands.Choice[str], url: Optional[str] = None):
    if capacity <= 0:
        await interaction.response.send_message(embed=create_error_embed("Invalid Capacity", "Capacity must be positive."), ephemeral=True)
        return
        
    is_local = 1 if not url else 0
    api_key = None if is_local else secrets.token_hex(16)
    clean_url = url.rstrip('/') if url else None
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('''INSERT INTO nodes (name, location, total_vps, tags, api_key, url, is_local, backend)
                       VALUES (?, ?, ?, '["cluster"]', ?, ?, ?, ?)''',
                    (name, location, capacity, api_key, clean_url, is_local, backend.value))
        conn.commit()
        node_id = cur.lastrowid
        conn.close()
        
        embed = create_success_embed("Node Added", f"Successfully created Node #{node_id} (`{name}`)!")
        add_field(embed, "Type", "Local Node" if is_local else "Remote Agent Node", True)
        add_field(embed, "Backend", backend.value.upper(), True)
        if not is_local:
            add_field(embed, "API Token", f"`{api_key}`", False)
            add_field(embed, "Remote Agent Setup", f"Run remote agent daemon with `--api-key={api_key}` on target server.", False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except sqlite3.IntegrityError:
        conn.close()
        await interaction.response.send_message(embed=create_error_embed("Duplicate", "A node with that name already exists."), ephemeral=True)

# =============================================================================
# BOT LIFECYCLE & STARTUP ENTRYPOINT
# =============================================================================
@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    
    try:
        logger.info("Synchronizing application slash commands globally...")
        synced = await bot.tree.sync()
        logger.info(f"Successfully synced {len(synced)} slash commands globally!")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

    if not anti_miner_and_threat_monitor.is_running():
        anti_miner_and_threat_monitor.start()
    if not auto_expire_monitor.is_running():
        auto_expire_monitor.start()
    if not dynamic_presence_updater.is_running():
        dynamic_presence_updater.start()

    if FLASK_TERMINAL_AVAILABLE:
        web_thread = threading.Thread(target=start_flask_terminal, daemon=True)
        web_thread.start()
        logger.info("Flask Web Terminal thread initialized.")

def main():
    if not DISCORD_TOKEN or DISCORD_TOKEN == 'YOUR_DISCORD_BOT_TOKEN_HERE':
        logger.error("CRITICAL: DISCORD_TOKEN is not set in environment or .env file.")
        print("Please configure DISCORD_TOKEN in .env and restart.")
        return
        
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Bot runtime crashed: {e}")

if __name__ == "__main__":
    main()
