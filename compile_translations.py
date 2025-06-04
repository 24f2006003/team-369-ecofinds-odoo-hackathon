import os
import subprocess

def compile_translations():
    """Compile all translation files."""
    try:
        # Get the absolute path to the translations directory
        translations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'translations')
        
        # Compile translations for each language
        for lang in os.listdir(translations_dir):
            lang_dir = os.path.join(translations_dir, lang)
            if os.path.isdir(lang_dir):
                po_file = os.path.join(lang_dir, 'LC_MESSAGES', 'messages.po')
                if os.path.exists(po_file):
                    print(f"Compiling translations for {lang}...")
                    subprocess.run(['pybabel', 'compile', '-d', translations_dir], check=True)
                    print(f"Successfully compiled translations for {lang}")
        
        print("All translations compiled successfully!")
    except Exception as e:
        print(f"Error compiling translations: {str(e)}")
        raise

if __name__ == '__main__':
    compile_translations() 