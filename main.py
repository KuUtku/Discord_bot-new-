import discord
from discord.ext import commands
import random
import os
import glob 
import asyncio
from dotenv import load_dotenv

load_dotenv()  # .env dosyasından token oku

# Bot prefix'i
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # Ses durumları için gerekli

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents
)

# Bot hazır olduğunda çalışır
@bot.event
async def on_ready():
    print(f'✅ Bot giriş yaptı: {bot.user}')
    # Cog'u burada yükle
    if not bot.get_cog('Music'):
        await bot.add_cog(Music(bot))

#Yardım komutu
@bot.command()
async def yardim(ctx):
    await ctx.send("İşte işine yarayacak komutlar:"
    "!ping - Botun aktif olup olmadığını kontrol eder."
    "!selam <isim> - Belirtilen isme selam verir."
    "!mem - Rastgele bir mem gönderir."
    "!temiz - Çevre temizliği hakkında bilgi verir."
    "!join - Botu sesli kanala davet eder."
    "!leave - Botu sesli kanaldan çıkarır."
    "!play <kısmi isim> - music/ klasöründen belirtilen isme sahip müziği çalar. İsim belirtilmezse rastgele bir müzik çalar."
    "!stop - Çalan müziği durdurur."
    "!pause - Çalan müziği duraklatır."
    "!resume - Duraklatılmış müziği devam ettirir."
    "!volume <0-100> - Müzik ses seviyesini ayarlar."
    )

# Basit komutlar
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def selam(ctx, isim: str = "kullanıcı"):
    await ctx.send(f"Merhaba {isim}! 👋")

# Mem Gönderme
@bot.command()
async def mem(ctx):
    images = glob.glob('images/*')
    if not images:
        await ctx.send("❌ Mem bulunamadı.")
        return
    path = random.choice(images)
    await ctx.send(file=discord.File(path))

# Çevre Temizliği
@bot.command()
async def temiz(ctx):
    await ctx.send("Çevre kirliliği, doğal kaynakların yanlış kullanımı ve atıkların kontrolsüz bir şekilde çevreye bırakılması sonucu oluşan ciddi bir sorundur. Bu kirliliğin azaltılmasında geri dönüşüm önemli bir rol oynar.")

# Hata yakalama
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"❌ Hata oluştu: {error}")

# FFMPEG seçenekleri (local dosya için)
ffmpeg_options = {
    'options': '-vn',
    'executable': r'C:\Users\CASPER\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe'
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Ses odasına katıl"""
        if channel is None:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                await ctx.send("❌ Bir ses odasında değilsin!")
                return

        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        await ctx.send(f"✅ {channel.name} adlı kanala katıldım!")

    @commands.command()
    async def leave(self, ctx):
        """Ses odasından ayrıl"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Ses odasından ayrıldım!")
        else:
            await ctx.send("❌ Herhangi bir ses odasında değilim!")

    @commands.command()
    async def play(self, ctx, *, isim: str = None):
        """Local music/ klasöründen dosya çal. (play <kısmi isim> veya play)"""
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("❌ Bir ses odasında değilsin!")
                return

        files = glob.glob('music/*')
        if not files:
            await ctx.send("❌ music/ klasöründe hiç dosya yok. Dosyaları koy ve tekrar dene.")
            return

        path = None
        if isim:
            matches = [f for f in files if isim.lower() in os.path.basename(f).lower()]
            if matches:
                path = matches[0]
            else:
                await ctx.send("❌ Belirtilen dosya bulunamadı. Dosya adının bir kısmını deneyin.")
                return
        else:
            path = random.choice(files)

        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(path, **ffmpeg_options))
        vc.play(source, after=lambda e: print(f'Hata: {e}') if e else None)
        await ctx.send(f'▶️ Şu an çalıyor: **{os.path.basename(path)}**')

    @commands.command()
    async def stop(self, ctx):
        """Müzik çalmayı durdur"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏹️ Müzik durduruldu!")
        else:
            await ctx.send("❌ Şu an bir müzik çalmıyor!")

    @commands.command()
    async def pause(self, ctx):
        """Müzik durakla"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Müzik duraklatıldı!")
        else:
            await ctx.send("❌ Şu an çalmıyor!")

    @commands.command()
    async def resume(self, ctx):
        """Müzik devam et"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Müzik devam ediyor!")
        else:
            await ctx.send("❌ Duraklatılmış bir müzik yok!")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Ses seviyesini değiştir (0-100)"""
        if ctx.voice_client is None or ctx.voice_client.source is None:
            await ctx.send("❌ Ses kaynağı bulunamadı!")
            return

        if 0 <= volume <= 100:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(f"🔊 Ses seviyesi %{volume} olarak ayarlandı!")
        else:
            await ctx.send("❌ Lütfen 0-100 arasında bir değer gir!")

        bot.run(YOUR TOKEN)
