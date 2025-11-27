def read_file(path_file: str) -> str:
    """
    Lit le contenu d'un fichier texte et le retourne sous forme de chaîne de caractères.
    """
    try:
        with open(path_file, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except Exception as e:
        print(f"❌ Erreur de lecture du fichier '{path_file}' : {e}")
        return ""