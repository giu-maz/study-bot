import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

class Database:
    def __init__(self, db_path: str = "study_bot.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Crea connessione al database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Inizializza il database con le tabelle necessarie"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabella utenti
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                weekly_goal INTEGER DEFAULT 20,
                checkin_time TEXT DEFAULT "23:00",
                reminder_start TEXT,
                reminder_end TEXT,
                joined_date DATE DEFAULT CURRENT_DATE,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabella log giornalieri
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE,
                should_study BOOLEAN,
                hours_studied REAL,
                distraction_level TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, date)
            )
        ''')
        
        # Tabella report settimanali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start DATE,
                week_end DATE,
                report_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ========== USER MANAGEMENT ==========
    
    def add_user(self, user_id: int, username: str) -> bool:
        """Aggiunge un nuovo utente"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username)
                VALUES (?, ?)
            ''', (user_id, username))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Errore aggiunta utente: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Recupera dati utente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_user_goal(self, user_id: int, weekly_goal: int) -> bool:
        """Aggiorna obiettivo settimanale"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET weekly_goal = ? WHERE user_id = ?
            ''', (weekly_goal, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Errore update goal: {e}")
            return False
    
    def update_user_checkin_time(self, user_id: int, checkin_time: str) -> bool:
        """Aggiorna orario check-in"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET checkin_time = ? WHERE user_id = ?
            ''', (checkin_time, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Errore update checkin time: {e}")
            return False
    
    def update_user_reminders(self, user_id: int, reminder_start: str, reminder_end: str) -> bool:
        """Aggiorna orari reminder"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET reminder_start = ?, reminder_end = ? WHERE user_id = ?
            ''', (reminder_start, reminder_end, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Errore update reminders: {e}")
            return False
    
    def get_all_active_users(self) -> List[Dict]:
        """Recupera tutti gli utenti attivi"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_active = 1')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ========== DAILY LOGS ==========
    
    def add_daily_log(self, user_id: int, date: str, should_study: bool, 
                      hours_studied: float, distraction_level: str, notes: str = "") -> bool:
        """Aggiunge o aggiorna log giornaliero"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO daily_logs (user_id, date, should_study, hours_studied, distraction_level, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, date) 
                DO UPDATE SET 
                    should_study = excluded.should_study,
                    hours_studied = excluded.hours_studied,
                    distraction_level = excluded.distraction_level,
                    notes = excluded.notes
            ''', (user_id, date, should_study, hours_studied, distraction_level, notes))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Errore add daily log: {e}")
            return False
    
    def get_daily_log(self, user_id: int, date: str) -> Optional[Dict]:
        """Recupera log di un giorno specifico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM daily_logs WHERE user_id = ? AND date = ?
        ''', (user_id, date))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_weekly_logs(self, user_id: int, week_start: str, week_end: str) -> List[Dict]:
        """Recupera log di una settimana"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM daily_logs 
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        ''', (user_id, week_start, week_end))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_user_weekly_stats(self, user_id: int, week_start: str, week_end: str) -> Dict:
        """Calcola statistiche settimanali per utente"""
        logs = self.get_weekly_logs(user_id, week_start, week_end)
        
        total_hours = sum(log['hours_studied'] for log in logs if log['should_study'])
        study_days = sum(1 for log in logs if log['should_study'] and log['hours_studied'] > 0)
        total_study_days = sum(1 for log in logs if log['should_study'])
        
        # Calcola distrazione media
        distraction_map = {'low': 1, 'medium': 2, 'high': 3}
        distractions = [distraction_map.get(log['distraction_level'], 2) 
                       for log in logs if log['should_study'] and log['hours_studied'] > 0]
        avg_distraction = sum(distractions) / len(distractions) if distractions else 0
        
        if avg_distraction <= 1.5:
            distraction_text = "Bassa"
        elif avg_distraction <= 2.5:
            distraction_text = "Media"
        else:
            distraction_text = "Alta"
        
        notes_count = sum(1 for log in logs if log['notes'])
        
        return {
            'total_hours': total_hours,
            'study_days': study_days,
            'total_study_days': total_study_days,
            'distraction_text': distraction_text,
            'notes_count': notes_count
        }
    
    # ========== WEEKLY REPORTS ==========
    
    def save_weekly_report(self, week_start: str, week_end: str, report_text: str) -> bool:
        """Salva report settimanale"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO weekly_reports (week_start, week_end, report_text)
                VALUES (?, ?, ?)
            ''', (week_start, week_end, report_text))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Errore save report: {e}")
            return False
    
    # ========== UTILITY ==========
    
    def get_week_dates(self, offset: int = 0) -> Tuple[str, str]:
        """
        Restituisce lunedì e domenica della settimana
        offset: 0 = settimana corrente, -1 = settimana scorsa, ecc.
        """
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
        sunday = monday + timedelta(days=6)
        return monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')
    
    def backup_database(self) -> str:
        """Restituisce il path del database per backup"""
        return self.db_path
