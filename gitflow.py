#!/usr/bin/env python
"""
Script para facilitar el uso de GitFlow en el proyecto cv-generador.
Ejecutar con: python gitflow.py [comando] [argumentos]
"""

import os
import sys
import subprocess

def run_command(command):
    """Ejecuta un comando y muestra su salida."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)
    
    return process.returncode

def get_current_branch():
    """Obtiene el nombre de la rama actual."""
    return subprocess.check_output(
        "git rev-parse --abbrev-ref HEAD", 
        shell=True
    ).decode().strip()

def get_repo_url():
    """Obtiene la URL del repositorio."""
    repo_url = subprocess.check_output(
        "git config --get remote.origin.url", 
        shell=True
    ).decode().strip()
    
    # Convertir SSH URL a HTTPS si es necesario
    if repo_url.startswith("git@github.com:"):
        repo_url = repo_url.replace("git@github.com:", "https://github.com/").replace(".git", "")
    elif repo_url.startswith("https://") and repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    
    return repo_url

def start_feature(feature_name):
    """Inicia una nueva rama feature."""
    print(f"Iniciando feature: {feature_name}")
    run_command("git checkout develop")
    run_command("git pull")
    run_command(f"git checkout -b feature/{feature_name}")
    print(f"\nRama feature/{feature_name} creada. Puedes comenzar a trabajar en ella.")
    print("Cuando termines, ejecuta: python gitflow.py finish-feature feature_name")

def finish_feature(feature_name, merge_locally=None):
    """Finaliza una rama feature y opcionalmente la fusiona con develop"""
    feature_branch = f"feature/{feature_name}"
    
    # Verificar que estamos en la rama feature correcta
    current_branch = get_current_branch()
    if current_branch != feature_branch:
        print(f"Error: No estás en la rama {feature_branch}")
        return 1
    
    print(f"Finalizando feature: {feature_name}")
    
    # Hacer push de la rama feature al remoto
    run_command("git push -u origin " + feature_branch)
    
    # Generar URL para crear PR
    repo_url = get_repo_url()
    if repo_url:
        pr_url = f"{repo_url}/pull/new/{feature_branch}"
        print(f"\nPuedes crear un Pull Request en: {pr_url}\n")
    
    # Preguntar si se desea fusionar localmente o mediante PR
    if merge_locally is None:
        print("\n¿Deseas fusionar la feature con develop localmente? (s/n)")
        choice = input().lower()
    else:
        choice = 's' if merge_locally else 'n'
    
    if choice.startswith('s'):
        # Fusionar localmente
        print("\nFusionando con develop localmente...")
        run_command("git checkout develop")
        run_command(f"git merge --no-ff {feature_branch} -m \"Merge feature '{feature_name}' into develop\"")
        
        # Preguntar si se desea eliminar la rama feature
        print("\n¿Deseas eliminar la rama feature? (s/n)")
        delete_choice = input().lower()
        if delete_choice.startswith('s'):
            run_command(f"git branch -d {feature_branch}")
            print(f"\nRama {feature_branch} eliminada localmente.")
        
        print("\nFeature finalizada y fusionada con develop.")
        return 0
    else:
        print("\nNo se ha fusionado localmente. Por favor, crea un Pull Request.")
        return 0

def start_release(version):
    """Inicia una nueva rama release."""
    print(f"Iniciando release: {version}")
    run_command("git checkout develop")
    run_command("git pull")
    run_command(f"git checkout -b release/v{version}")
    print(f"\nRama release/v{version} creada. Puedes realizar ajustes finales.")
    print("Cuando termines, ejecuta: python gitflow.py finish-release version")

def finish_release(version):
    """Finaliza una rama release, la fusiona con main y develop, y crea un tag."""
    print(f"Finalizando release: {version}")
    current_branch = get_current_branch()
    
    if current_branch != f"release/v{version}":
        print(f"Error: No estás en la rama release/v{version}")
        return 1
    
    # Verificar si hay cambios sin commit
    status = subprocess.check_output("git status --porcelain", shell=True).decode()
    if status:
        print("Error: Tienes cambios sin commit. Haz commit antes de finalizar la release.")
        return 1
    
    # Push a la rama remota
    run_command(f"git push -u origin release/v{version}")
    
    # Fusionar con main y develop localmente (opcional, se puede hacer mediante PR)
    print("\n¿Deseas fusionar la release con main y develop localmente? (s/n)")
    choice = input().lower()
    if choice == 's' or choice == 'si' or choice == 'sí' or choice == 'y' or choice == 'yes':
        print("Fusionando con main...")
        run_command("git checkout main")
        run_command("git pull")  # Asegurarse de tener la última versión de main
        run_command(f"git merge --no-ff release/v{version} -m \"Merge release/v{version} into main\"")
        
        # Crear tag en main
        print(f"Creando tag v{version}...")
        run_command(f"git tag -a v{version} -m \"Version {version}\"")
        
        print("Fusionando con develop...")
        run_command("git checkout develop")
        run_command("git pull")  # Asegurarse de tener la última versión de develop
        run_command(f"git merge --no-ff release/v{version} -m \"Merge release/v{version} into develop\"")
        
        # Push cambios y tags
        run_command("git push origin main develop --tags")
        print("Release fusionada con main y develop exitosamente.")
        print(f"Tag v{version} creado y publicado.")
    else:
        print("No se realizó la fusión local. Puedes hacerlo mediante Pull Requests.")
    
    # Generar URLs para crear PRs
    repo_url = get_repo_url()
    
    pr_main_url = f"{repo_url}/compare/main...release/v{version}?expand=1"
    pr_develop_url = f"{repo_url}/compare/develop...release/v{version}?expand=1"
    
    print("\nRelease finalizada. Crea Pull Requests visitando:")
    print(f"PR a main: {pr_main_url}")
    print(f"PR a develop: {pr_develop_url}")
    
    # Abrir el navegador con las URLs de los PRs
    run_command(f"start {pr_main_url}")
    
    return 0

def start_hotfix(version):
    """Inicia una nueva rama hotfix."""
    print(f"Iniciando hotfix: {version}")
    run_command("git checkout main")
    run_command("git pull")
    run_command(f"git checkout -b hotfix/v{version}")
    print(f"\nRama hotfix/v{version} creada. Puedes corregir el error crítico.")
    print("Cuando termines, ejecuta: python gitflow.py finish-hotfix version")

def finish_hotfix(version):
    """Finaliza una rama hotfix, la fusiona con main y develop, y crea un tag."""
    print(f"Finalizando hotfix: {version}")
    current_branch = get_current_branch()
    
    if current_branch != f"hotfix/v{version}":
        print(f"Error: No estás en la rama hotfix/v{version}")
        return 1
    
    # Verificar si hay cambios sin commit
    status = subprocess.check_output("git status --porcelain", shell=True).decode()
    if status:
        print("Error: Tienes cambios sin commit. Haz commit antes de finalizar el hotfix.")
        return 1
    
    # Push a la rama remota
    run_command(f"git push -u origin hotfix/v{version}")
    
    # Fusionar con main y develop localmente (opcional, se puede hacer mediante PR)
    print("\n¿Deseas fusionar el hotfix con main y develop localmente? (s/n)")
    choice = input().lower()
    if choice == 's' or choice == 'si' or choice == 'sí' or choice == 'y' or choice == 'yes':
        print("Fusionando con main...")
        run_command("git checkout main")
        run_command("git pull")  # Asegurarse de tener la última versión de main
        run_command(f"git merge --no-ff hotfix/v{version} -m \"Merge hotfix/v{version} into main\"")
        
        # Crear tag en main
        print(f"Creando tag v{version}...")
        run_command(f"git tag -a v{version} -m \"Version {version}\"")
        
        print("Fusionando con develop...")
        run_command("git checkout develop")
        run_command("git pull")  # Asegurarse de tener la última versión de develop
        run_command(f"git merge --no-ff hotfix/v{version} -m \"Merge hotfix/v{version} into develop\"")
        
        # Push cambios y tags
        run_command("git push origin main develop --tags")
        print("Hotfix fusionado con main y develop exitosamente.")
        print(f"Tag v{version} creado y publicado.")
    else:
        print("No se realizó la fusión local. Puedes hacerlo mediante Pull Requests.")
    
    # Generar URLs para crear PRs
    repo_url = get_repo_url()
    
    pr_main_url = f"{repo_url}/compare/main...hotfix/v{version}?expand=1"
    pr_develop_url = f"{repo_url}/compare/develop...hotfix/v{version}?expand=1"
    
    print("\nHotfix finalizado. Crea Pull Requests visitando:")
    print(f"PR a main: {pr_main_url}")
    print(f"PR a develop: {pr_develop_url}")
    
    # Abrir el navegador con las URLs de los PRs
    run_command(f"start {pr_main_url}")
    
    return 0

def print_help():
    """Muestra la ayuda del script."""
    print("""
GitFlow Helper Script

Uso: python gitflow.py [comando] [argumentos]

Comandos disponibles:
  start-feature <nombre>                 Inicia una nueva rama feature
  finish-feature <nombre> [true/false]   Finaliza una rama feature, opcionalmente la fusiona con develop y crea un PR
  start-release <version>                Inicia una nueva rama release
  finish-release <version>               Finaliza una rama release, opcionalmente la fusiona con main y develop, crea un tag y PRs
  start-hotfix <version>                 Inicia una nueva rama hotfix
  finish-hotfix <version>                Finaliza una rama hotfix, opcionalmente la fusiona con main y develop, crea un tag y PRs
  help                                   Muestra esta ayuda
    """)

def main():
    """Función principal que procesa los argumentos de la línea de comandos"""
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    if command == "start-feature" and len(sys.argv) >= 3:
        return start_feature(sys.argv[2])
    elif command == "finish-feature" and len(sys.argv) >= 3:
        merge_locally = None
        if len(sys.argv) >= 4:
            merge_locally = sys.argv[3].lower() == 'true'
        return finish_feature(sys.argv[2], merge_locally)
    elif command == "start-release" and len(sys.argv) >= 3:
        return start_release(sys.argv[2])
    elif command == "finish-release" and len(sys.argv) >= 3:
        return finish_release(sys.argv[2])
    elif command == "start-hotfix" and len(sys.argv) >= 3:
        return start_hotfix(sys.argv[2])
    elif command == "finish-hotfix" and len(sys.argv) >= 3:
        return finish_hotfix(sys.argv[2])
    elif command == "help":
        print_help()
        return 0
    else:
        print("Comando no reconocido o faltan argumentos.")
        print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
