import discord
from discord.ext import commands
import asyncio
import os
import json
import sqlite3
import random
import string
import secrets
import shlex
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load ENV Variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_NAME = os.getenv('BOT_NAME', 'Star Cloud')
PREFIX = os.getenv('PREFIX', '/')
YOUR_SERVER_IP = os.getenv('YOUR_SERVER_IP', '16.192.150.38')
MAIN_ADMIN_ID = int(os.getenv('MAIN_ADMIN_ID', '1417892611804368957'))
DEFAULT_STORAGE_POOL = os.getenv('DEFAULT_STORAGE_POOL', 'default')
BOT_VERSION = os.getenv('BOT_VERSION', '8.0-PRO')
BOT_DEVELOPER = os.getenv('BOT_DEVELOPER', 'KingSlayer')
BOT_THUMBNAIL_URL = os.getenv('https://cdn.discordapp.com/attachments/1518891606407647362/1542399970236301343/StarCloud-Banner.png?ex=6a911769&is=6a8fc5e9&hm=cf07552ca552a54d12b7ab74978677903b344bdba47f450695becfbde897bb14&')
BOT_ICON_URL = os.getenv('https://cdn.discordapp.com/attachments/1518891606407647362/1542399970647347221/StarCloud-Logo.png?ex=6a911769&is=6a8fc5e9&hm=dee542bb5cf8be9ec87f8ea9def4be2c084a4abbe9f7be4cc51dc21d6c743a05&')

# OS Options (Added Kali, CentOS, Alpine along with standard ones)
OS_OPTIONS = [
    {"label": "Ubuntu 20.04 LTS", "value": "images:ubuntu/20.04"},
    {"label": "Ubuntu 22.04 LTS", "value": "images:ubuntu/22.04"},
    {"label": "Ubuntu 24.04 LTS", "value": "images:ubuntu/24.04"},
    {"label": "Debian 11 (Bullseye)", "value": "images:debian/11"},
    {"label": "Debian 12 (Bookworm)", "value": "images:debian/12"},
    {"label": "Kali Linux", "value": "images:kali"},
    {"label": "CentOS 9 Stream", "value": "images:centos/9-Stream"},
    {"label": "Alpine 3.18", "value": "images:alpine/3.18"}
]

# Database Setup
def init_db():
    conn = sqlite3.connect('starcloud_vps.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS vps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        container_name TEXT UNIQUE NOT NULL,
        ram TEXT NOT NULL,
        cpu TEXT NOT NULL,
        storage TEXT NOT NULL,
        os_version TEXT,
        status TEXT DEFAULT 'running',
        ipv4 TEXT DEFAULT NULL,
        ssh_port INTEGER,
        root_password TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# Helper Functions
def generate_password(length=16):
    charset = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(charset) for _ in range(length))

async def run_shell(cmd: str, timeout: int = 120):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "", "Timeout", 1
    return stdout.decode().strip(), stderr.decode().strip(), proc.returncode

def get_free_port():
    conn = sqlite3.connect('starcloud_vps.db')
    cur = conn.cursor()
    cur.execute('SELECT ssh_port FROM vps')
    used_ports = [row[0] for row in cur.fetchall() if row[0]]
    conn.close()
    while True:
        port = random.randint(20000, 40000)
        if port not in used_ports:
            return port

# Embed Builder
def create_embed(title, description, color=0x2c3e50):
    embed = discord.Embed(title=f"🌟 {BOT_NAME} - {title}", description=description, color=color)
    embed.set_thumbnail(url=BOT_THUMBNAIL_URL)
    embed.set_footer(text=f"{BOT_NAME} v{BOT_VERSION} • Coded by {BOT_DEVELOPER}", icon_url=BOT_ICON_URL)
    return embed

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

class ManageView(discord.ui.View):
    def __init__(self, user_id, vps_data):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.vps = vps_data
        self.container_name = vps_data[2]
        self.ipv4 = vps_data[8] if vps_data[8] else YOUR_SERVER_IP
        self.ssh_port = vps_data[9]
        self.password = vps_data[10]

    async def verify_user(self, interaction):
        if str(interaction.user.id) != self.user_id and str(interaction.user.id) != str(MAIN_ADMIN_ID):
            await interaction.response.send_message("❌ Yeh VPS tumhara nahi hai!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="▶ Start", style=discord.ButtonStyle.success, custom_id="start")
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.verify_user(interaction): return
        await interaction.response.defer()
        await run_shell(f"lxc start {self.container_name}")
        await interaction.followup.send(f"✅ **{self.container_name}** started!", ephemeral=True)

    @discord.ui.button(label="⏸ Stop", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.verify_user(interaction): return
        await interaction.response.defer()
        await run_shell(f"lxc stop {self.container_name}")
        await interaction.followup.send(f"🛑 **{self.container_name}** stopped!", ephemeral=True)

    @discord.ui.button(label="🔄 Restart", style=discord.ButtonStyle.primary, custom_id="restart")
    async def restart_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.verify_user(interaction): return
        await interaction.response.defer()
        await run_shell(f"lxc restart {self.container_name}")
        await interaction.followup.send(f"🔄 **{self.container_name}** restarted!", ephemeral=True)

    @discord.ui.button(label="🔑 Get SSH Info", style=discord.ButtonStyle.secondary, custom_id="ssh_info")
    async def ssh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.verify_user(interaction): return
        embed = create_embed("🔑 SSH Credentials", f"Connect using Termius, PuTTY or CMD:")
        embed.add_field(name="IP Address", value=f"`{self.ipv4}`", inline=True)
        embed.add_field(name="Port", value=f"`{self.ssh_port}`", inline=True)
        embed.add_field(name="Username", value="`root`", inline=True)
        embed.add_field(name="Password", value=f"||{self.password}||", inline=False)
        embed.add_field(name="Quick Command", value=f"`ssh root@{self.ipv4} -p {self.ssh_port}`", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🌐 Web SSH (SSHX)", style=discord.ButtonStyle.success, custom_id="sshx")
    async def sshx_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.verify_user(interaction): return
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("⏳ Generating SSHX Web Terminal link... (Please wait 5-10 seconds)", ephemeral=True)
        
        # Permanent SSHX Generation Logic
        cn = self.container_name
        # Install sshx if not exists
        await run_shell(f"lxc exec {cn} -- bash -c 'command -v sshx || curl -sSf https://sshx.io/get | sh'")
        # Run sshx in background and dump output to log
        await run_shell(f"lxc exec {cn} -- bash -c 'nohup sshx > /root/.sshx_link.log 2>&1 &'")
        
        # Wait and extract link
        await asyncio.sleep(4)
        out, err, _ = await run_shell(f"lxc exec {cn} -- bash -c 'grep -aho \"https://sshx.io/s/[A-Za-z0-9#=_-]*\" /root/.sshx_link.log | head -n1'")
        sshx_link = out.strip()
        
        if sshx_link:
            embed = create_embed("🌐 SSHX Web Terminal", f"Click the link below to open terminal in browser:\n\n🔗 **{sshx_link}**")
            await interaction.user.send(embed=embed)
            await interaction.followup.send("✅ Check your DMs for the SSHX link!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to generate SSHX link. Make sure VPS is running and has internet.", ephemeral=True)

    @discord.ui.button(label="📁 File Manager", style=discord.ButtonStyle.secondary, custom_id="file_manager")
    async def file_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.verify_user(interaction): return
        await interaction.response.send_message(
            "📁 **File Manager Active:**\nPlease upload your file in this channel within the next **60 seconds**.\n(File will be uploaded to `/root/` in your VPS)", 
            ephemeral=False
        )

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and len(m.attachments) > 0

        try:
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            attachment = msg.attachments[0]
            file_name = attachment.filename
            
            status = await interaction.channel.send(f"📥 Downloading `{file_name}`...")
            await attachment.save(file_name)
            
            await status.edit(content=f"📤 Pushing `{file_name}` to VPS...")
            await run_shell(f"lxc file push {file_name} {self.container_name}/root/{file_name}")
            
            # Delete local file
            os.remove(file_name)
            await status.edit(content=f"✅ File `{file_name}` successfully uploaded to `/root/` in **{self.container_name}**!")
        except asyncio.TimeoutError:
            await interaction.channel.send("❌ Time's up! You didn't upload any file.")
        except Exception as e:
            await interaction.channel.send(f"❌ Upload failed: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def create(ctx, user: discord.Member, ram: int, cpu: int, disk: int, ipv4: str = None):
    """Admin Command to Create VPS. Usage: /create @user 4 2 50 [IPv4]"""
    # Show OS Selection First
    options = [discord.SelectOption(label=o["label"], value=o["value"]) for o in OS_OPTIONS]
    select = discord.ui.Select(placeholder="Select OS for the VPS", options=options)

    async def os_callback(interaction: discord.Interaction):
        if interaction.user.id != ctx.author.id: return
        os_version = select.values[0]
        await interaction.response.edit_message(content=f"⏳ Deploying **{os_version}** VPS for {user.mention}...", view=None)
        
        user_id = str(user.id)
        container_name = f"starcloud-{user.name[:10].replace(' ','').lower()}-{random.randint(100,999)}"
        ram_mb = ram * 1024
        ssh_port = get_free_port()
        password = generate_password()

        # Permanent Fix: Create container
        await run_shell(f"lxc init {os_version} {container_name} -s {DEFAULT_STORAGE_POOL}")
        await run_shell(f"lxc config set {container_name} limits.memory {ram_mb}MB")
        await run_shell(f"lxc config set {container_name} limits.cpu {cpu}")
        await run_shell(f"lxc config device set {container_name} root size={disk}GB")
        
        # Critical LXC configs for Docker/Nesting and Auto-Start
        await run_shell(f"lxc config set {container_name} security.nesting true")
        await run_shell(f"lxc config set {container_name} security.privileged true")
        await run_shell(f"lxc config set {container_name} boot.autostart 1") # Perm
