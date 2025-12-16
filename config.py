import os
from typing import Optional

class Config:
    """Configurazione del bot"""
    
    # Token bot Telegram (da ottenere da @BotFather)
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # ID del gruppo dove opera il bot (opzionale, per limitare l'uso)
    ALLOWED_GROUP_ID: Optional[int] = os.getenv('ALLOWED_GROUP_ID', None)
    
    # Timezone
    TIMEZONE: str = 'Europe/Rome'
    
    # Database
    DB_PATH: str = os.getenv('DB_PATH', 'study_bot.db')
    
    # Giorno report settimanale (0=Lunedì, 6=Domenica)
    WEEKLY_REPORT_DAY: int = 6  # Domenica
    WEEKLY_REPORT_TIME: str = "20:00"
    
    # Messaggi
    WELCOME_MESSAGE = """
👋 Benvenuto nel bot di accountability per lo studio!

Per iniziare, configura il tuo profilo:
• /setgoal [ore] - Imposta obiettivo settimanale (es: /setgoal 20)
• /settime [HH:MM] - Imposta orario check-in (es: /settime 23:00)
• /setreminders [HH:MM] [HH:MM] - Imposta reminder (es: /setreminders 19:00 20:30)

Comandi disponibili:
• /mystats - Visualizza le tue statistiche
• /checkin - Check-in manuale
• /skip - Salta il check-in di oggi
• /weekly - Report settimanale
• /help - Lista completa comandi
"""
    
    HELP_MESSAGE = """
📚 **Comandi disponibili:**

**Setup:**
• /start - Registrati al bot
• /setgoal [ore] - Obiettivo settimanale (es: /setgoal 20)
• /settime [HH:MM] - Orario check-in (es: /settime 23:00)
• /setreminders [HH:MM] [HH:MM] - Orari reminder inizio/fine studio

**Uso quotidiano:**
• /checkin - Check-in manuale
• /mystats - Le tue statistiche personali
• /skip - Salta il check-in di oggi (giorno libero)

**Report:**
• /weekly - Mostra report settimanale
• /help - Mostra questo messaggio

**Admin:**
• /backup - Scarica backup database (solo in privato)
"""

    @staticmethod
    def validate_token() -> bool:
        """Verifica che il token sia configurato"""
        return bool(Config.BOT_TOKEN and Config.BOT_TOKEN != '')
