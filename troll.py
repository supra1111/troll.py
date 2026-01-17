import discord
from discord.ext import commands
import datetime

# ================= AYARLAR =================
TOKEN = "TOKEN_BURAYA"
GUILD_ID = 1259126653838299209
YETKILI_ROL = "Channel Manager"
LOG_KANAL = "mod-log"
TIMEOUT_DK = 1

# ================= WHITELIST =================
WHITELIST_USERS = [
    123456789012345678  # kendi ID'n
]

WHITELIST_ROLES = [
    "Founder",
    "Admin"
]

# ================= İSTATİSTİK =================
stats = {
    "spam": 0,
    "kanal": 0,
    "rol": 0,
    "ban": 0,
    "bot": 0,
    "yetki": 0,
    "webhook": 0
}

# ================= INTENTS =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= YARDIMCI =================
def whitelist_mi(member):
    if member.guild.owner_id == member.id:
        return True
    if member.id in WHITELIST_USERS:
        return True
    for rol in member.roles:
        if rol.name in WHITELIST_ROLES:
            return True
    return False

async def log(guild, title, desc):
    kanal = discord.utils.get(guild.text_channels, name=LOG_KANAL)
    if not kanal:
        kanal = await guild.create_text_channel(LOG_KANAL)
    embed = discord.Embed(
        title=title,
        description=desc,
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    await kanal.send(embed=embed)

async def ceza(member, sebep):
    try:
        await member.timeout(datetime.timedelta(minutes=TIMEOUT_DK), reason=sebep)
    except:
        pass

# ================= WEBHOOK GUARD =================
@bot.event
async def on_webhooks_update(channel):
    async for entry in channel.guild.audit_logs(limit=1):
        if whitelist_mi(entry.user):
            return

        for wh in await channel.webhooks():
            await wh.delete()

        await ceza(entry.user, "Webhook Guard")
        stats["webhook"] += 1
        await log(channel.guild, "🛑 Webhook Guard", entry.user.mention)

# ================= BAN GUARD =================
@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if whitelist_mi(entry.user):
            return

        await guild.unban(user)
        await ceza(entry.user, "Ban Guard")
        stats["ban"] += 1
        await log(guild, "🛑 Ban Guard", entry.user.mention)

# ================= BOT GUARD =================
@bot.event
async def on_member_join(member):
    if member.bot:
        async for entry in member.guild.audit_logs(limit=1):
            if whitelist_mi(entry.user):
                return

            await member.kick(reason="Bot Guard")
            await ceza(entry.user, "Bot Ekleme Guard")
            stats["bot"] += 1
            await log(member.guild, "🛑 Bot Guard", entry.user.mention)

# ================= YETKİ GUARD =================
@bot.event
async def on_member_update(before, after):
    if whitelist_mi(after):
        return

    for rol in after.roles:
        if rol not in before.roles:
            if rol.permissions.administrator or rol.permissions.manage_roles:
                await after.remove_roles(rol)
                async for entry in after.guild.audit_logs(limit=1):
                    await ceza(entry.user, "Yetki Yükseltme Guard")
                    stats["yetki"] += 1
                    await log(after.guild, "🛑 Yetki Guard", entry.user.mention)

# ================= GUARD PANEL =================
@bot.tree.command(name="guard-stats", description="Guard istatistikleri")
async def guard_stats(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 Guard İstatistikleri",
        color=discord.Color.blue()
    )
    for k, v in stats.items():
        embed.add_field(name=k.upper(), value=v, inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================= RUN =================
bot.run(TOKEN)
# ================= ANTI NUKE =================
from collections import defaultdict
import time

nuke_log = defaultdict(list)
ceza_puani = defaultdict(int)

def anti_nuke_check(user_id):
    now = time.time()
    nuke_log[user_id] = [t for t in nuke_log[user_id] if now - t < ANTI_NUKE_TIME]
    nuke_log[user_id].append(now)
    return len(nuke_log[user_id]) >= ANTI_NUKE_LIMIT

async def nuke_ceza(member):
    for rol in member.roles:
        if rol.name != "@everyone":
            try:
                await member.remove_roles(rol)
            except:
                pass

    await log(member.guild, "☢️ ANTI NUKE", f"{member.mention} tüm yetkileri alındı")

# ================= CEZA SİSTEMİ =================
async def cezalandir(member, sebep):
    ceza_puani[member.id] += 1
    puan = ceza_puani[member.id]

    if puan == 1:
        await member.timeout(datetime.timedelta(minutes=1), reason=sebep)
    elif puan == 2:
        await member.kick(reason=sebep)
    else:
        await member.ban(reason=sebep)

# ================= KANAL SİLME (ANTI NUKE) =================
@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1):
        if whitelist_mi(entry.user):
            return

        if anti_nuke_check(entry.user.id):
            await nuke_ceza(entry.user)

        await cezalandir(entry.user, "Kanal Silme Guard")
        stats["kanal"] += 1

# ================= ROL SİLME (ANTI NUKE) =================
@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1):
        if whitelist_mi(entry.user):
            return

        if anti_nuke_check(entry.user.id):
            await nuke_ceza(entry.user)

        await cezalandir(entry.user, "Rol Silme Guard")
        stats["rol"] += 1
class WhitelistPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="➕ Ekle", style=discord.ButtonStyle.success)
    async def ekle(self, interaction, button):
        WHITELIST_USERS.append(interaction.user.id)
        await interaction.response.send_message("✅ Whitelist eklendi", ephemeral=True)

    @discord.ui.button(label="➖ Çıkar", style=discord.ButtonStyle.danger)
    async def cikar(self, interaction, button):
        if interaction.user.id in WHITELIST_USERS:
            WHITELIST_USERS.remove(interaction.user.id)
        await interaction.response.send_message("❌ Whitelist çıkarıldı", ephemeral=True)

    @discord.ui.button(label="📋 Liste", style=discord.ButtonStyle.primary)
    async def liste(self, interaction, button):
        text = "\n".join(str(i) for i in WHITELIST_USERS)
        await interaction.response.send_message(f"```{text}```", ephemeral=True)

@bot.tree.command(name="whitelist-panel", description="Whitelist yönetimi")
async def whitelist_panel(interaction: discord.Interaction):
    if not whitelist_mi(interaction.user):
        return await interaction.response.send_message("Yetkin yok", ephemeral=True)

    await interaction.response.send_message(
        "🧠 Whitelist Yönetimi",
        view=WhitelistPanel(),
        ephemeral=True
    )
import matplotlib.pyplot as plt
import os

def guard_grafik_olustur():
    isimler = list(stats.keys())
    degerler = list(stats.values())

    plt.figure(figsize=(8, 4))
    plt.bar(isimler, degerler)
    plt.title("Guard Olay İstatistikleri")
    plt.xlabel("Guard Türü")
    plt.ylabel("Olay Sayısı")
    plt.tight_layout()

    dosya = "guard_stats.png"
    plt.savefig(dosya)
    plt.close()
    return dosya
@bot.tree.command(name="guard-panel", description="Grafikli guard paneli")
async def guard_panel(interaction: discord.Interaction):
    dosya = guard_grafik_olustur()

    embed = discord.Embed(
        title="📊 Guard Kontrol Paneli",
        description="Sunucu güvenlik istatistikleri",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )

    embed.add_field(
        name="Toplam Olay",
        value=str(sum(stats.values())),
        inline=False
    )

    file = discord.File(dosya, filename="guard_stats.png")
    embed.set_image(url="attachment://guard_stats.png")

    await interaction.response.send_message(
        embed=embed,
        file=file,
        ephemeral=True
    )

    os.remove(dosya)
if not whitelist_mi(interaction.user):
    return await interaction.response.send_message(
        "❌ Yetkin yok",
        ephemeral=True
    )
from collections import defaultdict
import datetime

daily_stats = defaultdict(int)
weekly_stats = defaultdict(int)

def kaydet(event):
    gun = datetime.date.today().isoformat()
    hafta = datetime.date.today().strftime("%Y-%W")

    daily_stats[f"{gun}-{event}"] += 1
    weekly_stats[f"{hafta}-{event}"] += 1
import matplotlib.pyplot as plt

def grafik_olustur(mod="genel"):
    if mod == "gunluk":
        data = daily_stats
        baslik = "📅 Günlük Guard İstatistikleri"
    elif mod == "haftalik":
        data = weekly_stats
        baslik = "🗓️ Haftalık Guard İstatistikleri"
    else:
        data = stats
        baslik = "📊 Genel Guard İstatistikleri"

    keys = list(data.keys())
    values = list(data.values())

    plt.figure(figsize=(9, 4))
    plt.bar(keys, values)
    plt.title(baslik)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    dosya = f"guard_{mod}.png"
    plt.savefig(dosya)
    plt.close()
    return dosya
class GrafikPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    async def guncelle(self, interaction, mod):
        dosya = grafik_olustur(mod)
        file = discord.File(dosya, filename="grafik.png")

        embed = discord.Embed(
            title="📊 Guard Grafik Paneli",
            description=f"Gösterim: {mod.upper()}",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://grafik.png")

        await interaction.response.edit_message(
            embed=embed,
            attachments=[file]
        )

    @discord.ui.button(label="📊 Genel", style=discord.ButtonStyle.primary)
    async def genel(self, interaction, button):
        await self.guncelle(interaction, "genel")

    @discord.ui.button(label="📅 Günlük", style=discord.ButtonStyle.success)
    async def gunluk(self, interaction, button):
        await self.guncelle(interaction, "gunluk")

    @discord.ui.button(label="🗓️ Haftalık", style=discord.ButtonStyle.secondary)
    async def haftalik(self, interaction, button):
        await self.guncelle(interaction, "haftalik")
@bot.tree.command(name="guard-panel", description="Grafikli guard paneli")
async def guard_panel(interaction: discord.Interaction):
    if not whitelist_mi(interaction.user):
        return await interaction.response.send_message(
            "❌ Yetkin yok",
            ephemeral=True
        )

    dosya = grafik_olustur("genel")
    file = discord.File(dosya, filename="grafik.png")

    embed = discord.Embed(
        title="📊 Guard Grafik Paneli",
        description="Butonlarla grafik değiştir",
        color=discord.Color.blue()
    )
    embed.set_image(url="attachment://grafik.png")

    await interaction.response.send_message(
        embed=embed,
        file=file,
        view=GrafikPanel(),
        ephemeral=True
    )
from collections import defaultdict
import datetime

hourly_stats = defaultdict(int)

def saatlik_kaydet(event):
    saat = datetime.datetime.now().strftime("%Y-%m-%d %H")
    hourly_stats[f"{saat}-{event}"] += 1
stats["ban"] += 1
kaydet("ban")          # günlük / haftalık
saatlik_kaydet("ban")  # saatlik
import matplotlib.pyplot as plt

def filtreli_grafik(event="hepsi", mod="genel"):
    data = {}

    if mod == "saatlik":
        source = hourly_stats
        baslik = "⏰ Saatlik Guard Grafiği (Son 24 Saat)"
    elif mod == "gunluk":
        source = daily_stats
        baslik = "📅 Günlük Guard Grafiği"
    elif mod == "haftalik":
        source = weekly_stats
        baslik = "🗓️ Haftalık Guard Grafiği"
    else:
        source = stats
        baslik = "📊 Genel Guard Grafiği"

    for k, v in source.items():
        if event == "hepsi":
            data[k] = v
        elif event in k:
            data[k] = v

    keys = list(data.keys())[-24:]  # saatlikte son 24
    values = list(data.values())[-24:]

    plt.figure(figsize=(10, 4))
    plt.plot(keys, values, marker="o")
    plt.xticks(rotation=45, ha="right")
    plt.title(f"{baslik} | Filtre: {event.upper()}")
    plt.tight_layout()

    dosya = f"guard_{mod}_{event}.png"
    plt.savefig(dosya)
    plt.close()
    return dosya
class GelismisGrafikPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.mod = "genel"
        self.event = "hepsi"

    async def guncelle(self, interaction):
        dosya = filtreli_grafik(self.event, self.mod)
        file = discord.File(dosya, filename="grafik.png")

        embed = discord.Embed(
            title="📊 Gelişmiş Guard Grafik Paneli",
            description=f"Zaman: {self.mod.upper()} | Filtre: {self.event.upper()}",
            color=discord.Color.green()
        )
        embed.set_image(url="attachment://grafik.png")

        await interaction.response.edit_message(
            embed=embed,
            attachments=[file]
        )

    # ---- ZAMAN ----
    @discord.ui.button(label="⏰ Saatlik", style=discord.ButtonStyle.primary, row=0)
    async def saatlik(self, interaction, button):
        self.mod = "saatlik"
        await self.guncelle(interaction)

    @discord.ui.button(label="📅 Günlük", style=discord.ButtonStyle.success, row=0)
    async def gunluk(self, interaction, button):
        self.mod = "gunluk"
        await self.guncelle(interaction)

    @discord.ui.button(label="🗓️ Haftalık", style=discord.ButtonStyle.secondary, row=0)
    async def haftalik(self, interaction, button):
        self.mod = "haftalik"
        await self.guncelle(interaction)

    # ---- FİLTRE ----
    @discord.ui.button(label="🚫 Ban", style=discord.ButtonStyle.danger, row=1)
    async def ban(self, interaction, button):
        self.event = "ban"
        await self.guncelle(interaction)

    @discord.ui.button(label="📁 Kanal", style=discord.ButtonStyle.primary, row=1)
    async def kanal(self, interaction, button):
        self.event = "kanal"
        await self.guncelle(interaction)

    @discord.ui.button(label="🎭 Rol", style=discord.ButtonStyle.success, row=1)
    async def rol(self, interaction, button):
        self.event = "rol"
        await self.guncelle(interaction)

    @discord.ui.button(label="♻️ Hepsi", style=discord.ButtonStyle.secondary, row=1)
    async def hepsi(self, interaction, button):
        self.event = "hepsi"
        await self.guncelle(interaction)
@bot.tree.command(name="guard-panel", description="Gelişmiş grafik paneli")
async def guard_panel(interaction: discord.Interaction):
    if not whitelist_mi(interaction.user):
        return await interaction.response.send_message(
            "❌ Yetkin yok", ephemeral=True
        )

    dosya = filtreli_grafik()
    file = discord.File(dosya, filename="grafik.png")

    embed = discord.Embed(
        title="📊 Gelişmiş Guard Paneli",
        description="Zaman & filtre seç",
        color=discord.Color.green()
    )
    embed.set_image(url="attachment://grafik.png")

    await interaction.response.send_message(
        embed=embed,
        file=file,
        view=GelismisGrafikPanel(),
        ephemeral=True
    )
from collections import defaultdict
import time

spike_events = defaultdict(list)
def spike_kontrol(event, user_id):
    now = time.time()
    spike_events[event] = [t for t in spike_events[event] if now - t < SPIKE_TIME_WINDOW]
    spike_events[event].append(now)

    if len(spike_events[event]) >= SPIKE_THRESHOLD:
        return True
    return False
async def savunma_modu(guild, sebep):
    for role in guild.roles:
        if role.permissions.administrator or role.permissions.manage_channels:
            perms = role.permissions
            perms.update(administrator=False, manage_channels=False, manage_roles=False)
            try:
                await role.edit(permissions=perms)
            except:
                pass

    await log(
        guild,
        "☢️ ANOMALİ ALGILANDI",
        f"Sebep: {sebep}\nSunucu savunma moduna alındı"
    )
stats["ban"] += 1
kaydet("ban")
saatlik_kaydet("ban")

if spike_kontrol("ban", entry.user.id):
    await savunma_modu(guild, "Ban Spike")
stats["kanal"] += 1
kaydet("kanal")
saatlik_kaydet("kanal")

if spike_kontrol("kanal", entry.user.id):
    await savunma_modu(guild, "Kanal Silme Spike")
stats["rol"] += 1
kaydet("rol")
saatlik_kaydet("rol")

if spike_kontrol("rol", entry.user.id):
    await savunma_modu(guild, "Rol Spike")
role_backup = {}

async def yedek_al(guild):
    role_backup[guild.id] = {}
    for role in guild.roles:
        role_backup[guild.id][role.id] = role.permissions
async def savunma_modu(guild, sebep):
    await yedek_al(guild)

    for role in guild.roles:
        if role.permissions.administrator or role.permissions.manage_roles or role.permissions.manage_channels:
            perms = role.permissions
            perms.update(
                administrator=False,
                manage_roles=False,
                manage_channels=False
            )
            try:
                await role.edit(permissions=perms)
            except:
                pass

    await log(
        guild,
        "☢️ SAVUNMA MODU AÇILDI",
        f"Sebep: {sebep}"
    )
async def savunma_kapat(guild):
    if guild.id not in role_backup:
        return False

    for role in guild.roles:
        if role.id in role_backup[guild.id]:
            try:
                await role.edit(permissions=role_backup[guild.id][role.id])
            except:
                pass

    await log(guild, "🔓 SAVUNMA MODU KAPATILDI", "Yetkiler geri yüklendi")
    return True
class SavunmaPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="🔓 Savunmayı Kapat", style=discord.ButtonStyle.success)
    async def kapat(self, interaction, button):
        if not whitelist_mi(interaction.user):
            return await interaction.response.send_message(
                "❌ Yetkin yok", ephemeral=True
            )

        basarili = await savunma_kapat(interaction.guild)
        if basarili:
            await interaction.response.send_message(
                "✅ Savunma modu kapatıldı", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⚠️ Aktif savunma modu yok", ephemeral=True
            )
@bot.tree.command(name="savunma-panel", description="Savunma modu yönetimi")
async def savunma_panel(interaction: discord.Interaction):
    if not whitelist_mi(interaction.user):
        return await interaction.response.send_message(
            "❌ Yetkin yok", ephemeral=True
        )

    await interaction.response.send_message(
        "☢️ Savunma Modu Kontrol Paneli",
        view=SavunmaPanel(),
        ephemeral=True
    )
async def alarm_listesi(guild):
    alicilar = set()

    # Sunucu sahibi
    owner = guild.owner
    if owner:
        alicilar.add(owner)

    # Whitelist kullanıcılar
    for uid in WHITELIST_USERS:
        member = guild.get_member(uid)
        if member:
            alicilar.add(member)

    # Whitelist roller
    for role in guild.roles:
        if role.name in WHITELIST_ROLES:
            for member in role.members:
                alicilar.add(member)

    return alicilar
async def savunma_alarm_dm(guild, sebep):
    if not ALARM_DM:
        return

    alicilar = await alarm_listesi(guild)

    embed = discord.Embed(
        title="☢️ SAVUNMA MODU AKTİF",
        description="Sunucu otomatik olarak korumaya alındı!",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )

    embed.add_field(name="Sunucu", value=guild.name, inline=False)
    embed.add_field(name="Sebep", value=sebep, inline=False)
    embed.add_field(name="Durum", value="Yetkiler geçici olarak kısıtlandı", inline=False)

    for uye in alicilar:
        try:
            await uye.send(embed=embed)
        except:
            pass
async def savunma_modu(guild, sebep):
    await yedek_al(guild)

    for role in guild.roles:
        if role.permissions.administrator or role.permissions.manage_roles or role.permissions.manage_channels:
            perms = role.permissions
            perms.update(
                administrator=False,
                manage_roles=False,
                manage_channels=False
            )
            try:
                await role.edit(permissions=perms)
            except:
                pass

    await log(
        guild,
        "☢️ SAVUNMA MODU AÇILDI",
        f"Sebep: {sebep}"
    )

    await savunma_alarm_dm(guild, sebep)
