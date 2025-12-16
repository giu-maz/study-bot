# 📚 Study Accountability Bot

Bot Telegram per il tracciamento dello studio e accountability di gruppo.

## 🎯 Funzionalità

- ✅ Check-in giornaliero automatico (orario personalizzabile)
- 📊 Statistiche personali e di gruppo
- 🔔 Reminder inizio/fine studio (configurabili)
- 📈 Report settimanale automatico (Domenica sera)
- 💾 Backup database
- 🔒 Privacy: ognuno vede solo i propri dati + report di gruppo

## 🚀 Setup Rapido

### Prerequisiti

1. **Account Telegram**
2. **Account GitHub** (gratuito)
3. **Account Render.com** (gratuito)

### Passo 1: Crea il Bot Telegram

1. Apri Telegram e cerca `@BotFather`
2. Invia `/newbot`
3. Scegli un nome per il bot (es: "Study Accountability Bot")
4. Scegli un username (deve finire con `bot`, es: `my_study_bot`)
5. **SALVA IL TOKEN** che ti dà BotFather (sarà tipo: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Passo 2: Carica il Codice su GitHub

1. Vai su [GitHub](https://github.com) e crea un account se non ce l'hai
2. Clicca su "New repository"
3. Nome: `study-accountability-bot`
4. Seleziona "Public" o "Private" (come preferisci)
5. Clicca "Create repository"

6. Scarica questo progetto e caricalo su GitHub:
   - Opzione A: Usa GitHub Desktop (più semplice)
   - Opzione B: Da terminale:
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     git branch -M main
     git remote add origin https://github.com/TUO_USERNAME/study-accountability-bot.git
     git push -u origin main
     ```

### Passo 3: Deploy su Render.com

1. Vai su [Render.com](https://render.com) e registrati (gratis)
2. Clicca "New +" → "Web Service"
3. Connetti il tuo account GitHub
4. Seleziona il repository `study-accountability-bot`
5. Configurazione:
   - **Name**: study-bot (o come vuoi)
   - **Region**: Frankfurt (più vicino all'Italia)
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
6. Clicca su "Advanced" e aggiungi Environment Variable:
   - **Key**: `BOT_TOKEN`
   - **Value**: Il token che ti ha dato BotFather
7. Clicca "Create Web Service"

**Attendi 2-3 minuti** per il primo deploy.

### Passo 4: Configura il Bot

1. Apri Telegram e cerca il tuo bot (il nome che hai scelto)
2. Premi "Start" o invia `/start`
3. Configura il tuo profilo:
   ```
   /setgoal 20          # Imposta obiettivo settimanale (20 ore)
   /settime 23:00       # Imposta orario check-in (23:00)
   /setreminders 19:00 20:30   # Imposta reminder studio
   ```

4. **Aggiungi il bot al gruppo studio:**
   - Crea un gruppo Telegram con i tuoi amici
   - Aggiungi il bot al gruppo (come aggiungeresti un contatto)
   - Ogni persona nel gruppo deve fare `/start` nel bot

### Passo 5: Test

1. Aspetta l'orario del check-in (es: 23:00)
2. Il bot ti invierà un messaggio privato con il check-in
3. Compila usando i bottoni
4. Domenica sera riceverai il report settimanale

## 📱 Comandi Disponibili

### Setup Iniziale
```
/start                        - Registrati al bot
/setgoal [ore]               - Obiettivo settimanale (es: /setgoal 20)
/settime [HH:MM]             - Orario check-in (es: /settime 23:00)
/setreminders [HH:MM] [HH:MM] - Orari reminder (es: /setreminders 19:00 20:30)
```

### Uso Quotidiano
```
/checkin    - Check-in manuale
/mystats    - Le tue statistiche
/skip       - Salta check-in di oggi (giorno libero)
```

### Report
```
/weekly     - Report settimanale
/help       - Lista comandi
```

### Backup (Solo in Chat Privata)
```
/backup     - Scarica backup database
```

## 🔧 Troubleshooting

### Il bot non risponde
1. Verifica su Render.com che il servizio sia "Active" (non "Suspended")
2. Controlla i log su Render.com per vedere eventuali errori
3. Verifica che il BOT_TOKEN sia corretto

### Non ricevo i reminder
1. Assicurati di aver impostato gli orari con `/setreminders`
2. Il bot deve poterti inviare messaggi privati (avvia conversazione con `/start`)

### Il database si è perso
1. Usa `/backup` regolarmente per salvare il database
2. Su Render.com, il database viene salvato ma può essere perso in caso di rideploy
3. Soluzione: scarica backup settimanalmente

### Voglio modificare il codice
1. Modifica i file localmente
2. Fai commit e push su GitHub
3. Render.com rileverà le modifiche e rifarà automaticamente il deploy

## 🛠️ Personalizzazioni

### Cambiare l'orario del report settimanale
In `config.py`:
```python
WEEKLY_REPORT_DAY: int = 6  # 0=Lunedì, 6=Domenica
WEEKLY_REPORT_TIME: str = "20:00"
```

### Cambiare il giorno del report
```python
WEEKLY_REPORT_DAY: int = 0  # Lunedì invece di Domenica
```

## 📊 Struttura Database

Il bot salva tutto in `study_bot.db` (SQLite):

- **users**: Dati utenti (obiettivi, orari)
- **daily_logs**: Check-in giornalieri
- **weekly_reports**: Storico report settimanali

## 🔒 Privacy

- Ogni utente vede solo i propri dati
- Il report settimanale mostra tutti nel gruppo
- I reminder sono privati (solo tu li ricevi)
- Il database è privato sul server Render

## 💰 Costi

**TUTTO GRATIS:**
- Telegram: Gratis
- GitHub: Gratis (repository pubbliche illimitate)
- Render.com: Gratis (750h/mese = 24/7)

## 🆘 Supporto

Se hai problemi:
1. Controlla i log su Render.com
2. Verifica che il BOT_TOKEN sia corretto
3. Assicurati che il bot sia stato aggiunto al gruppo

## 📝 Licenza

MIT License - Usa e modifica come vuoi!
