
import subprocess
import os

def git_clone_or_pull(repo_url : str, directory : str):
    # Se non viene fornita una directory, si utilizza il nome del repo come directory.
    if directory is None:
        directory = repo_url.split('/')[-1]
        if directory.endswith('.git'):
            directory = directory[:-4]

    # Verifica se la directory esiste
    if os.path.exists(directory):
        # La directory esiste, esegui git pull
        command = ["git", "-C", directory, "pull"]
    else:
        # La directory non esiste, esegui git clone
        # command = ["git", "clone", "--depth 1", ]
        command = ["git", "clone", "--depth", "1", repo_url, directory]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr