import discord
from discord.ext import commands
from discord import app_commands
import datetime
import random

# ================= AYARLAR =================
TOKEN = "MTQ2MTQzNzc0MDkxNzcyMzM2Nw.GSH1-C.FAB33kiLnCyUW0ps8DlZRZNepBdqzqeD1IKgkQ"
GUILD_ID = 1259126653838299209  # Sunucu ID
YETKILI_ROL = "Channel Manager"
LOG_KANAL = "mod-log"

SPAM_LIMIT = 5
TIMEOUT_DK = 1

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= READY =================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    # 🔥 ESKİ SLASH KOMUTLARINI TEMİZLER
    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)

    print(f"Aktif: {bot.user}")
    print("Slash komutlar temizlendi ve senkronlandı")

# ================= LOG =================
async def log_gonder(guild, embed):
    kanal = discord.utils.get(guild.text_channels, name=LOG_KANAL)
    if not kanal:
        kanal = await guild.create_text_channel(LOG_KANAL)
    await kanal.send(embed=embed)

def yetkili_mi(member):
    rol = discord.utils.get(member.guild.roles, name=YETKILI_ROL)
    return rol in member.roles if rol else False

# ================= GUARD / SPAM =================
son_mesaj = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if yetkili_mi(message.author):
        return

    uid = message.author.id
    icerik = message.content.lower()

    onceki, adet = son_mesaj.get(uid, ("", 0))
    adet = adet + 1 if icerik == onceki else 1
    son_mesaj[uid] = (icerik, adet)

    if adet >= SPAM_LIMIT:
        try:
            await message.author.timeout(
                datetime.timedelta(minutes=TIMEOUT_DK),
                reason="Spam / Guard"
            )
        except:
            pass

        embed = discord.Embed(
            title="🚨 Spam Guard",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Kullanıcı", value=message.author.mention)
        embed.add_field(name="Mesaj", value=message.content[:100])
        embed.add_field(name="Ceza", value=f"{TIMEOUT_DK} dk timeout")

        await log_gonder(message.guild, embed)
        await message.channel.send(
            f"⚠️ {message.author.mention} spam yaptığı için **{TIMEOUT_DK} dk timeout** aldı."
        )

        son_mesaj[uid] = ("", 0)

    await bot.process_commands(message)

# ================= BUTON PANEL =================
class KanalPanel(discord.ui.View):
    def __init__(self, yetkili):
        super().__init__(timeout=120)
        self.yetkili = yetkili

    async def interaction_check(self, interaction):
        return interaction.user == self.yetkili

    @discord.ui.button(label="➕ Metin Kanal", style=discord.ButtonStyle.success)
    async def metin(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await interaction.guild.create_text_channel("yeni-metin")
        await interaction.response.send_message(
            f"{ch.mention} oluşturuldu", ephemeral=True
        )

    @discord.ui.button(label="🔊 Ses Kanal", style=discord.ButtonStyle.primary)
    async def ses(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await interaction.guild.create_voice_channel("Yeni Ses")
        await interaction.response.send_message(
            f"{ch.name} oluşturuldu", ephemeral=True
        )

    @discord.ui.button(label="📂 Kategori", style=discord.ButtonStyle.secondary)
    async def kategori(self, interaction: discord.Interaction, button: discord.ui.Button):
        k = await interaction.guild.create_category("Yeni Kategori")
        await interaction.response.send_message(
            f"{k.name} oluşturuldu", ephemeral=True
        )

    @discord.ui.button(label="🗑️ Kanal Sil", style=discord.ButtonStyle.danger)
    async def sil(self, interaction: discord.Interaction, button: discord.ui.Button):
        ad = interaction.channel.name
        await interaction.channel.delete()

        embed = discord.Embed(
            title="🗑️ Kanal Silindi",
            description=ad,
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        await log_gonder(interaction.guild, embed)

# ================= SLASH KOMUTLAR =================
@bot.tree.command(name="yonetim", description="Butonlu kanal yönetimi")
async def yonetim(interaction: discord.Interaction):
    if not yetkili_mi(interaction.user):
        return await interaction.response.send_message(
            "❌ Yetkin yok", ephemeral=True
        )

    await interaction.response.send_message(
        "🎛️ Kanal Yönetim Paneli",
        view=KanalPanel(interaction.user),
        ephemeral=True
    )

@bot.tree.command(name="ping", description="Bot gecikmesi")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Pong 🏓 {round(bot.latency * 1000)}ms"
    )

@bot.tree.command(name="yazi-tura", description="Yazı tura atar")
async def yazi_tura(interaction: discord.Interaction):
    await interaction.response.send_message(
        random.choice(["🪙 Yazı", "🪙 Tura"])
    )

@bot.tree.command(name="zar", description="Zar atar")
async def zar(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🎲 {random.randint(1, 6)}"
    )

# ================= RUN =================
bot.run(TOKEN)
