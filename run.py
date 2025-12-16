"""
Wrapper per far girare il bot come Web Service su Render (gratis)
Apre una porta HTTP per far contento Render, ma il bot continua a funzionare normalmente
"""
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Importa il bot
import bot

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler per rispondere alle richieste HTTP di Render"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        # Silenzia i log HTTP
        pass

def run_web_server():
    """Avvia un semplice server HTTP sulla porta richiesta da Render"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f'HTTP server running on port {port}')
    server.serve_forever()

if __name__ == '__main__':
    # Avvia il server HTTP in un thread separato
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Avvia il bot nel thread principale
    bot.main()
