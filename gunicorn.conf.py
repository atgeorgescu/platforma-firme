# Citit automat de gunicorn (inclusiv cu comanda de start existentă pe Render).
timeout = 180
threads = 4
graceful_timeout = 30

def on_starting(server):
    # Planul gratuit are 512 MB RAM; OCR-ul rulează într-un subproces (~320 MB),
    # deci forțăm un singur worker chiar dacă linia de comandă cere mai mulți.
    server.num_workers = 1
