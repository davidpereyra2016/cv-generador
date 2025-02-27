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

def start_feature(feature_name):
    """Inicia una nueva rama feature."""
    print(f"Iniciando feature: {feature_name}")
    run_command("git checkout develop")
    run_command("git pull")
    run_command(f"git checkout -b feature/{feature_name}")
    print(f"\nRama feature/{feature_name} creada. Puedes comenzar a trabajar en ella.")
    print("Cuando termines, ejecuta: python gitflow.py finish-feature feature_name")

def finish_feature(feature_name):
    """Finaliza una rama feature, la fusiona con develop y crea un pull request."""
    print(f"Finalizando feature: {feature_name}")
    current_branch = subprocess.check_output(
        "git rev-parse --abbrev-ref HEAD", 
        shell=True
    ).decode().strip()
    
    if current_branch != f"feature/{feature_name}":
        print(f"Error: No estás en la rama feature/{feature_name}")
        return 1
    
    # Verificar si hay cambios sin commit
    status = subprocess.check_output("git status --porcelain", shell=True).decode()
    if status:
        print("Error: Tienes cambios sin commit. Haz commit antes de finalizar la feature.")
        return 1
    
    # Push a la rama remota
    run_command(f"git push -u origin feature/{feature_name}")
    
    # Fusionar con develop localmente (opcional, se puede hacer mediante PR)
    print("\n¿Deseas fusionar la feature con develop localmente? (s/n)")
    choice = input().lower()
    if choice == 's' or choice == 'si' or choice == 'sí' or choice == 'y' or choice == 'yes':
        print("Fusionando con develop...")
        run_command("git checkout develop")
        run_command("git pull")  # Asegurarse de tener la última versión de develop
        run_command(f"git merge --no-ff feature/{feature_name} -m \"Merge feature/{feature_name} into develop\"")
        run_command("git push origin develop")
        print("Feature fusionada con develop exitosamente.")
    else:
        print("No se realizó la fusión local. Puedes hacerlo mediante un Pull Request.")
    
    # Generar URL para crear PR
    repo_url = subprocess.check_output(
        "git config --get remote.origin.url", 
        shell=True
    ).decode().strip()
    
    # Convertir SSH URL a HTTPS si es necesario
    if repo_url.startswith("git@github.com:"):
        repo_url = repo_url.replace("git@github.com:", "https://github.com/").replace(".git", "")
    elif repo_url.startswith("https://") and repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    
    pr_url = f"{repo_url}/compare/develop...feature/{feature_name}?expand=1"
    
    print("\nFeature finalizada. Crea un Pull Request visitando:")
    print(pr_url)
    
    # Abrir el navegador con la URL del PR
    run_command(f"start {pr_url}")
    
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
    current_branch = subprocess.check_output(
        "git rev-parse --abbrev-ref HEAD", 
        shell=True
    ).decode().strip()
    
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
    repo_url = subprocess.check_output(
        "git config --get remote.origin.url", 
        shell=True
    ).decode().strip()
    
    # Convertir SSH URL a HTTPS si es necesario
    if repo_url.startswith("git@github.com:"):
        repo_url = repo_url.replace("git@github.com:", "https://github.com/").replace(".git", "")
    elif repo_url.startswith("https://") and repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    
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
    current_branch = subprocess.check_output(
        "git rev-parse --abbrev-ref HEAD", 
        shell=True
    ).decode().strip()
    
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
    repo_url = subprocess.check_output(
        "git config --get remote.origin.url", 
        shell=True
    ).decode().strip()
    
    # Convertir SSH URL a HTTPS si es necesario
    if repo_url.startswith("git@github.com:"):
        repo_url = repo_url.replace("git@github.com:", "https://github.com/").replace(".git", "")
    elif repo_url.startswith("https://") and repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    
    pr_main_url = f"{repo_url}/compare/main...hotfix/v{version}?expand=1"
    pr_develop_url = f"{repo_url}/compare/develop...hotfix/v{version}?expand=1"
    
    print("\nHotfix finalizado. Crea Pull Requests visitando:")
    print(f"PR a main: {pr_main_url}")
    print(f"PR a develop: {pr_develop_url}")
    
    # Abrir el navegador con las URLs de los PRs
    run_command(f"start {pr_main_url}")
    
    return 0

def show_help():
    """Muestra la ayuda del script."""
    print("""
GitFlow Helper Script

Uso: python gitflow.py [comando] [argumentos]

Comandos disponibles:
  start-feature <nombre>     Inicia una nueva rama feature
  finish-feature <nombre>    Finaliza una rama feature, opcionalmente la fusiona con develop y crea un PR
  start-release <version>    Inicia una nueva rama release
  finish-release <version>   Finaliza una rama release, opcionalmente la fusiona con main y develop, crea un tag y PRs
  start-hotfix <version>     Inicia una nueva rama hotfix
  finish-hotfix <version>    Finaliza una rama hotfix, opcionalmente la fusiona con main y develop, crea un tag y PRs
  help                       Muestra esta ayuda
    """)

def main():
    """Función principal."""
    if len(sys.argv) < 2:
        show_help()
        return 1
    
    command = sys.argv[1]
    
    if command == "start-feature" and len(sys.argv) == 3:
        return start_feature(sys.argv[2])
    elif command == "finish-feature" and len(sys.argv) == 3:
        return finish_feature(sys.argv[2])
    elif command == "start-release" and len(sys.argv) == 3:
        return start_release(sys.argv[2])
    elif command == "finish-release" and len(sys.argv) == 3:
        return finish_release(sys.argv[2])
    elif command == "start-hotfix" and len(sys.argv) == 3:
        return start_hotfix(sys.argv[2])
    elif command == "finish-hotfix" and len(sys.argv) == 3:
        return finish_hotfix(sys.argv[2])
    elif command == "help":
        show_help()
        return 0
    else:
        print("Comando no reconocido o faltan argumentos.")
        show_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
