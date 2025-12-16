import logging
import pytz
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import Database
from config import Config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inizializza database
db = Database(Config.DB_PATH)

# Timezone italiana
TZ = pytz.timezone(Config.TIMEZONE)

# Stato temporaneo per check-in
user_checkin_state = {}


# ========== COMANDI BASE ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Registra l'utente"""
    user = update.effective_user
    
    # Registra utente nel database
    db.add_user(user.id, user.username or user.first_name)
    
    await update.message.reply_text(Config.WELCOME_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - Mostra comandi disponibili"""
    await update.message.reply_text(Config.HELP_MESSAGE)


# ========== COMANDI CONFIGURAZIONE ==========

async def setgoal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /setgoal [ore] - Imposta obiettivo settimanale"""
    user_id = update.effective_user.id
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "⚠️ Uso corretto: /setgoal [ore]\nEsempio: /setgoal 20"
        )
        return
    
    try:
        goal = int(context.args[0])
        if goal < 0 or goal > 168:
            await update.message.reply_text("⚠️ Inserisci un numero di ore valido (0-168)")
            return
        
        db.update_user_goal(user_id, goal)
        await update.message.reply_text(f"✅ Obiettivo settimanale impostato: {goal} ore")
    except ValueError:
        await update.message.reply_text("⚠️ Inserisci un numero valido")


async def settime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /settime [HH:MM] - Imposta orario check-in"""
    user_id = update.effective_user.id
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "⚠️ Uso corretto: /settime [HH:MM]\nEsempio: /settime 23:00"
        )
        return
    
    try:
        # Valida formato orario
        time_str = context.args[0]
        datetime.strptime(time_str, '%H:%M')
        
        db.update_user_checkin_time(user_id, time_str)
        
        # Rischedula check-in per questo utente
        reschedule_user_checkin(context.application, user_id)
        
        await update.message.reply_text(f"✅ Orario check-in impostato: {time_str}")
    except ValueError:
        await update.message.reply_text("⚠️ Formato orario non valido. Usa HH:MM (es: 23:00)")


async def setreminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /setreminders [HH:MM] [HH:MM] - Imposta reminder inizio/fine"""
    user_id = update.effective_user.id
    
    if not context.args or len(context.args) != 2:
        await update.message.reply_text(
            "⚠️ Uso corretto: /setreminders [inizio] [fine]\n"
            "Esempio: /setreminders 19:00 20:30"
        )
        return
    
    try:
        start_time = context.args[0]
        end_time = context.args[1]
        
        # Valida formati
        datetime.strptime(start_time, '%H:%M')
        datetime.strptime(end_time, '%H:%M')
        
        db.update_user_reminders(user_id, start_time, end_time)
        
        # Rischedula reminder per questo utente
        reschedule_user_reminders(context.application, user_id)
        
        await update.message.reply_text(
            f"✅ Reminder impostati:\n"
            f"• Inizio studio: {start_time}\n"
            f"• Fine studio: {end_time}"
        )
    except ValueError:
        await update.message.reply_text("⚠️ Formato orario non valido. Usa HH:MM")


# ========== CHECK-IN ==========

async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /checkin - Avvia check-in manuale"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ Usa /start per registrarti prima!")
        return
    
    await send_checkin_message(update.effective_chat.id, user_id, context)


async def send_checkin_message(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Invia messaggio di check-in con bottoni"""
    # Ottieni username
    user = db.get_user(user_id)
    username = user['username'] if user else "utente"
    
    keyboard = [
        [
            InlineKeyboardButton("Sì", callback_data=f"checkin_yes_{user_id}"),
            InlineKeyboardButton("No - giorno libero", callback_data=f"checkin_no_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    today = datetime.now(TZ).strftime('%Y-%m-%d')
    existing_log = db.get_daily_log(user_id, today)
    
    if existing_log:
        message = f"ℹ️ @{username}, hai già fatto il check-in oggi!\n\n"
        message += "Vuoi aggiornarlo?\n\n1️⃣ Dovevi studiare oggi?"
    else:
        message = f"🎯 Check-in giornaliero - @{username}\n\n1️⃣ Dovevi studiare oggi?"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=reply_markup
    )


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /skip - Salta check-in di oggi (giorno libero)"""
    user_id = update.effective_user.id
    today = datetime.now(TZ).strftime('%Y-%m-%d')
    
    # Salva come giorno libero
    db.add_daily_log(user_id, today, should_study=False, hours_studied=0, 
                     distraction_level='low', notes='Giorno libero')
    
    await update.message.reply_text("✅ Check-in saltato. Registrato come giorno libero.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce callback dai bottoni inline"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = int(data.split('_')[-1])
    
    # Verifica che l'utente che clicca sia quello giusto
    if query.from_user.id != user_id:
        await query.answer("⚠️ Questo check-in non è per te!", show_alert=True)
        return
    
    today = datetime.now(TZ).strftime('%Y-%m-%d')
    
    # Step 1: Dovevi studiare?
    if data.startswith('checkin_yes_'):
        user_checkin_state[user_id] = {'should_study': True, 'date': today}
        
        keyboard = [
            [InlineKeyboardButton("0h", callback_data=f"hours_0_{user_id}"),
             InlineKeyboardButton("0.5h", callback_data=f"hours_0.5_{user_id}"),
             InlineKeyboardButton("1h", callback_data=f"hours_1_{user_id}")],
            [InlineKeyboardButton("1.5h", callback_data=f"hours_1.5_{user_id}"),
             InlineKeyboardButton("2h", callback_data=f"hours_2_{user_id}"),
             InlineKeyboardButton("2.5h", callback_data=f"hours_2.5_{user_id}")],
            [InlineKeyboardButton("3h+", callback_data=f"hours_3_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="2️⃣ Quante ore hai studiato?",
            reply_markup=reply_markup
        )
    
    elif data.startswith('checkin_no_'):
        # Giorno libero
        db.add_daily_log(user_id, today, should_study=False, hours_studied=0,
                        distraction_level='low', notes='Giorno libero')
        await query.edit_message_text("✅ Check-in salvato! Giorno libero registrato.")
        user_checkin_state.pop(user_id, None)
    
    # Step 2: Ore studiate
    elif data.startswith('hours_'):
        hours = float(data.split('_')[1])
        user_checkin_state[user_id]['hours_studied'] = hours
        
        keyboard = [
            [InlineKeyboardButton("Basso 💪", callback_data=f"distraction_low_{user_id}"),
             InlineKeyboardButton("Medio 😅", callback_data=f"distraction_medium_{user_id}")],
            [InlineKeyboardButton("Alto 😞", callback_data=f"distraction_high_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="3️⃣ Livello di distrazione?",
            reply_markup=reply_markup
        )
    
    # Step 3: Distrazione
    elif data.startswith('distraction_'):
        distraction = data.split('_')[1]
        user_checkin_state[user_id]['distraction_level'] = distraction
        
        # Salva nel database
        state = user_checkin_state[user_id]
        db.add_daily_log(
            user_id, 
            state['date'],
            state['should_study'],
            state['hours_studied'],
            state['distraction_level'],
            notes=""
        )
        
        # Calcola ore settimanali
        week_start, week_end = db.get_week_dates()
        stats = db.get_user_weekly_stats(user_id, week_start, week_end)
        user = db.get_user(user_id)
        goal = user['weekly_goal'] if user else 20
        
        await query.edit_message_text(
            f"✅ Check-in salvato!\n\n"
            f"Ore oggi: {state['hours_studied']}h\n"
            f"Totale questa settimana: {stats['total_hours']}h / {goal}h"
        )
        
        # Chiedi note (opzionale)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="4️⃣ Vuoi aggiungere note? (opzionale)\nRispondi a questo messaggio o ignora."
        )
        
        user_checkin_state.pop(user_id, None)


# ========== STATISTICHE ==========

async def mystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /mystats - Mostra statistiche personali"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ Usa /start per registrarti prima!")
        return
    
    week_start, week_end = db.get_week_dates()
    stats = db.get_user_weekly_stats(user_id, week_start, week_end)
    
    message = f"📊 **Statistiche personali - @{user['username']}**\n\n"
    message += f"**Questa settimana:**\n"
    message += f"• Ore studiate: {stats['total_hours']}h / {user['weekly_goal']}h obiettivo\n"
    message += f"• Giorni di studio: {stats['study_days']}/{stats['total_study_days']}\n"
    message += f"• Distrazione media: {stats['distraction_text']}\n"
    message += f"• Note aggiunte: {stats['notes_count']}\n"
    
    # Calcola percentuale completamento
    if user['weekly_goal'] > 0:
        completion = (stats['total_hours'] / user['weekly_goal']) * 100
        if completion >= 100:
            message += f"\n🎉 Obiettivo raggiunto! ({completion:.0f}%)"
        else:
            message += f"\n📈 Progresso: {completion:.0f}%"
    
    await update.message.reply_text(message)


async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /weekly - Genera report settimanale"""
    await generate_weekly_report(context, update.effective_chat.id)


async def generate_weekly_report(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Genera e invia report settimanale"""
    week_start, week_end = db.get_week_dates()
    users = db.get_all_active_users()
    
    if not users:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Nessun utente registrato."
        )
        return
    
    # Header
    start_date = datetime.strptime(week_start, '%Y-%m-%d').strftime('%d/%m')
    end_date = datetime.strptime(week_end, '%Y-%m-%d').strftime('%d/%m')
    
    message = f"📈 **REPORT SETTIMANALE**\n"
    message += f"Settimana {start_date} - {end_date}\n\n"
    message += "📊 **STATISTICHE PERSONALI:**\n\n"
    
    # Statistiche per utente
    total_hours_all = 0
    active_users = 0
    goals_reached = 0
    
    for user in users:
        stats = db.get_user_weekly_stats(user['user_id'], week_start, week_end)
        
        if stats['study_days'] > 0:
            active_users += 1
            total_hours_all += stats['total_hours']
            
            message += f"@{user['username']}:\n"
            message += f"• Ore studiate: {stats['total_hours']}h / {user['weekly_goal']}h obiettivo"
            
            if stats['total_hours'] >= user['weekly_goal']:
                message += " ✅"
                goals_reached += 1
            
            message += f"\n• Giorni di studio: {stats['study_days']}/{stats['total_study_days']}\n"
            message += f"• Distrazione media: {stats['distraction_text']}\n"
            
            if stats['notes_count'] > 0:
                message += f"• Note aggiunte: {stats['notes_count']}\n"
            
            message += "\n"
    
    # Statistiche di gruppo
    message += "---\n\n"
    message += "📊 **STATISTICHE DI GRUPPO:**\n\n"
    message += f"• Partecipanti attivi: {active_users}/{len(users)}\n"
    message += f"• Totale ore studiate: {total_hours_all}h\n"
    
    if active_users > 0:
        avg_hours = total_hours_all / active_users
        message += f"• Media ore/persona: {avg_hours:.1f}h\n"
        completion_rate = (goals_reached / active_users) * 100
        message += f"• Tasso completamento obiettivi: {completion_rate:.0f}%\n"
    
    # Salva report nel database
    db.save_weekly_report(week_start, week_end, message)
    
    await context.bot.send_message(chat_id=chat_id, text=message)


# ========== BACKUP ==========

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /backup - Invia backup database (solo in chat privata)"""
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "⚠️ Questo comando funziona solo in chat privata con il bot."
        )
        return
    
    db_path = db.backup_database()
    
    try:
        await update.message.reply_document(
            document=open(db_path, 'rb'),
            filename=f"study_bot_backup_{datetime.now(TZ).strftime('%Y%m%d_%H%M')}.db",
            caption="📦 Backup database"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore durante backup: {e}")


# ========== SCHEDULER ==========

def setup_scheduler(application: Application):
    """Configura lo scheduler per notifiche automatiche"""
    scheduler = AsyncIOScheduler(timezone=TZ)
    
    # Schedule check-in per ogni utente
    users = db.get_all_active_users()
    for user in users:
        schedule_user_checkin(scheduler, application, user)
        schedule_user_reminders(scheduler, application, user)
    
    # Schedule report settimanale (Domenica alle 20:00)
    scheduler.add_job(
        send_weekly_report_to_all,
        CronTrigger(day_of_week=Config.WEEKLY_REPORT_DAY, 
                   hour=int(Config.WEEKLY_REPORT_TIME.split(':')[0]),
                   minute=int(Config.WEEKLY_REPORT_TIME.split(':')[1]),
                   timezone=TZ),
        args=[application],
        id='weekly_report'
    )
    
    scheduler.start()
    return scheduler


def schedule_user_checkin(scheduler: AsyncIOScheduler, application: Application, user: dict):
    """Schedula check-in per un utente specifico"""
    if not user['checkin_time']:
        return
    
    hour, minute = map(int, user['checkin_time'].split(':'))
    
    scheduler.add_job(
        send_user_checkin,
        CronTrigger(hour=hour, minute=minute, timezone=TZ),
        args=[application, user['user_id']],
        id=f"checkin_{user['user_id']}",
        replace_existing=True
    )


def schedule_user_reminders(scheduler: AsyncIOScheduler, application: Application, user: dict):
    """Schedula reminder per un utente specifico"""
    if not user['reminder_start'] or not user['reminder_end']:
        return
    
    # Reminder inizio
    hour_start, minute_start = map(int, user['reminder_start'].split(':'))
    scheduler.add_job(
        send_start_reminder,
        CronTrigger(hour=hour_start, minute=minute_start, timezone=TZ),
        args=[application, user['user_id']],
        id=f"reminder_start_{user['user_id']}",
        replace_existing=True
    )
    
    # Reminder fine
    hour_end, minute_end = map(int, user['reminder_end'].split(':'))
    scheduler.add_job(
        send_end_reminder,
        CronTrigger(hour=hour_end, minute=minute_end, timezone=TZ),
        args=[application, user['user_id']],
        id=f"reminder_end_{user['user_id']}",
        replace_existing=True
    )


def reschedule_user_checkin(application: Application, user_id: int):
    """Rischedula check-in per un utente dopo cambio orario"""
    user = db.get_user(user_id)
    if user and hasattr(application, 'scheduler'):
        schedule_user_checkin(application.scheduler, application, user)


def reschedule_user_reminders(application: Application, user_id: int):
    """Rischedula reminder per un utente dopo cambio orari"""
    user = db.get_user(user_id)
    if user and hasattr(application, 'scheduler'):
        schedule_user_reminders(application.scheduler, application, user)


async def send_user_checkin(application: Application, user_id: int):
    """Invia check-in automatico ad un utente"""
    user = db.get_user(user_id)
    if not user:
        return
    
    # Invia in privato all'utente
    try:
        await send_checkin_message(user_id, user_id, application)
    except Exception as e:
        logger.error(f"Errore invio check-in a {user_id}: {e}")


async def send_start_reminder(application: Application, user_id: int):
    """Invia reminder inizio studio"""
    user = db.get_user(user_id)
    if not user:
        return
    
    try:
        await application.bot.send_message(
            chat_id=user_id,
            text=f"⏰ Reminder: È ora di studiare! 💪"
        )
    except Exception as e:
        logger.error(f"Errore invio reminder start a {user_id}: {e}")


async def send_end_reminder(application: Application, user_id: int):
    """Invia reminder fine studio"""
    user = db.get_user(user_id)
    if not user:
        return
    
    try:
        await application.bot.send_message(
            chat_id=user_id,
            text=f"⏱️ Session terminata! Ricorda il check-in alle {user['checkin_time']}"
        )
    except Exception as e:
        logger.error(f"Errore invio reminder end a {user_id}: {e}")


async def send_weekly_report_to_all(application: Application):
    """Invia report settimanale a tutti i gruppi attivi"""
    # Per ora invia nel gruppo principale
    # TODO: Gestire multipli gruppi se necessario
    users = db.get_all_active_users()
    if users:
        # Prendi il primo utente per ottenere un chat_id valido
        # In produzione, salva i chat_id dei gruppi nel database
        pass


# ========== MAIN ==========

def main():
    """Avvia il bot"""
    if not Config.validate_token():
        logger.error("❌ BOT_TOKEN non configurato! Controlla il file .env")
        return
    
    # Crea application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Setup scheduler
    scheduler = setup_scheduler(application)
    application.scheduler = scheduler
    
    # Registra handler
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setgoal", setgoal_command))
    application.add_handler(CommandHandler("settime", settime_command))
    application.add_handler(CommandHandler("setreminders", setreminders_command))
    application.add_handler(CommandHandler("checkin", checkin_command))
    application.add_handler(CommandHandler("skip", skip_command))
    application.add_handler(CommandHandler("mystats", mystats_command))
    application.add_handler(CommandHandler("weekly", weekly_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Avvia bot
    logger.info("🚀 Bot avviato!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
