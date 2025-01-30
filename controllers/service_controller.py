import os
import shutil
import sqlite3
import platform
from pathlib import Path

def get_chrome_cache_dir():
    system = platform.system()
    if system == "Windows":
        cache_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'Cache')
    elif system == "Darwin":
        cache_path = os.path.expanduser('~/Library/Caches/Google/Chrome/Default/Cache')
    elif system == "Linux":
        cache_path = os.path.expanduser('~/.cache/google-chrome/default/Cache')
    else:
        raise OSError("Système d'exploitation non supporté")
    return cache_path

def copy_cache(source_dir, dest_dir):
    if not os.path.exists(source_dir):
        print("Répertoire cache introuvable!")
        return False
    
    try:
        shutil.copytree(source_dir, dest_dir)
        print(f"Cache copié vers: {dest_dir}")
        return True
    except Exception as e:
        print(f"Erreur lors de la copie: {str(e)}")
        return False

def analyze_cache(cache_dir):
    # Exemple d'analyse simple des URLs en cache via la base de données
    db_path = os.path.join(cache_dir, 'Network', 'Cookies')  # Exemple avec les cookies
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Exemple de requête pour les cookies
        cursor.execute("SELECT host_key, name, value FROM cookies")
        results = cursor.fetchall()
        
        print(f"\n{len(results)} cookies trouvés:")
        for row in results[:5]:  # Affiche les 5 premiers
            print(f"Domain: {row[0]} | Nom: {row[1]} | Valeur: {row[2]}")
            
        conn.close()
    except Exception as e:
        print(f"Erreur d'analyse SQLite: {str(e)}")

if __name__ == "__main__":
    target_folder = "chrome_cache_backup"
    
    print("Récupération du cache Chrome...")
    cache_dir = get_chrome_cache_dir()
    print(f"Répertoire cache détecté: {cache_dir}")
    
    if copy_cache(cache_dir, target_folder):
        print("\nAnalyse basique du contenu...")
        analyze_cache(target_folder)
    else:
        print("Échec de la récupération du cache")

    print("\nNotes importantes:")
    print("- Les fichiers bruts du cache ne sont pas directement lisibles")
    print("- Chrome doit être fermé pendant l'opération")
    print("- Certains fichiers peuvent être manquants (protégés/utilisés)")