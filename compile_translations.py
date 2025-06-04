import os
import subprocess
import sys

def compile_translations():
    """Compile all translation files."""
    try:
        # Get the absolute path to the translations directory
        translations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'translations')
        
        if not os.path.exists(translations_dir):
            print(f"Translations directory not found at {translations_dir}")
            return

        # Check if pybabel is installed
        try:
            subprocess.run(['pybabel', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Installing pybabel...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'Babel'], check=True)

        # Compile translations for each language
        for lang in os.listdir(translations_dir):
            lang_dir = os.path.join(translations_dir, lang)
            if os.path.isdir(lang_dir):
                po_file = os.path.join(lang_dir, 'LC_MESSAGES', 'messages.po')
                if os.path.exists(po_file):
                    print(f"Compiling translations for {lang}...")
                    try:
                        subprocess.run(['pybabel', 'compile', '-d', translations_dir], check=True)
                        print(f"Successfully compiled translations for {lang}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error compiling translations for {lang}: {str(e)}")
                        continue
        
        print("Translation compilation completed!")
    except Exception as e:
        print(f"Error in translation compilation: {str(e)}")
        # Don't raise the exception, just log it
        return False
    return True

if __name__ == '__main__':
    compile_translations() 