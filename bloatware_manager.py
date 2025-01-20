#!/usr/bin/env python3

import subprocess
import os
import time
import re

# Arquivo contendo a lista de pacotes de bloatware
BLOATWARE_LIST = "bloatware.txt"

# Pacote a ser excluído da desativação de apps do usuário
EXCLUDED_PACKAGE = "com.termux"

# Tempo de espera entre as desativações/ativações (em segundos)
SLEEP_TIME = 1

def trim(text):
    """Remove espaços em branco do início e do final de uma string."""
    return text.strip()

def disable_package(package):
    """Desativa um pacote usando adb."""
    package = trim(package)
    print(f"Desativando o pacote: {package}")
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "disable-user", "--user", "0", package],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Pacote {package} desativado com sucesso.")
        time.sleep(SLEEP_TIME)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao desativar o pacote {package}:")
        print(e.stderr)


def enable_package(package):
    """Ativa um pacote usando adb."""
    package = trim(package)
    print(f"Ativando o pacote: {package}")
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "enable", "--user", "0", package],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Pacote {package} ativado com sucesso.")
        time.sleep(SLEEP_TIME)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao ativar o pacote {package}:")
        print(e.stderr)


def disable_all_user_packages():
    """Desativa todos os apps do usuário (exceto EXCLUDED_PACKAGE)."""
    print(f"Listando apps do usuário a serem desativados (exceto {EXCLUDED_PACKAGE}):")
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages", "-3"],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Erro ao listar pacotes do usuário: {e.stderr}")
        return

    packages = result.stdout.strip().splitlines()
    if not packages:
      print(f"Nenhum aplicativo do usuário para desativar (exceto {EXCLUDED_PACKAGE}).")
      return
    packages_to_disable = []
    for package in packages:
        package = package.replace("package:", "").strip()
        if package != EXCLUDED_PACKAGE:
            packages_to_disable.append(package)
            print(f"  - {package}")

    if not packages_to_disable:
        print(f"Nenhum aplicativo do usuário para desativar (exceto {EXCLUDED_PACKAGE}).")
        return

    confirm = input(f"Confirma desativar todos os aplicativos listados? (s/n): ").lower()
    if confirm in ["s", "sim"]:
        print(f"Desativando todos os apps do usuário (exceto {EXCLUDED_PACKAGE})...")
        for package in packages_to_disable:
            disable_package(package)
        print(f"Todos os apps do usuário (exceto {EXCLUDED_PACKAGE}) foram desativados.")
    else:
        print("Desativação cancelada.")

def enable_all_user_packages():
    """Ativa todos os apps do usuário que foram desativados."""
    print("Listando apps do usuário a serem ativados...")
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages", "-d", "-3"], # lista somente os desativados
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Erro ao listar pacotes desativados do usuário: {e.stderr}")
        return

    packages = result.stdout.strip().splitlines()
    if not packages:
        print("Nenhum aplicativo do usuário desativado encontrado.")
        return

    packages_to_enable = []
    for package in packages:
        package = package.replace("package:", "").strip()
        packages_to_enable.append(package)
        print(f"  - {package}")

    confirm = input("Confirma reativar todos os aplicativos listados? (s/n): ").lower()
    if confirm in ["s", "sim"]:
        print("Reativando todos os apps do usuário...")
        for package in packages_to_enable:
            enable_package(package)
        print("Todos os apps do usuário foram reativados.")
    else:
        print("Reativação cancelada.")

def disable_selected_active_packages():
    """Lista aplicativos ativos e permite selecionar quais desativar."""
    print("Listando aplicativos ativos:")
    try:
        result = subprocess.run(
            ["adb", "shell", "ps", "|", "grep", "u0_"],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Erro ao listar aplicativos ativos: {e.stderr}")
        return

    packages = []
    lines = result.stdout.strip().splitlines()
    for line in lines:
        match = re.search(r'^\S+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\S+\s+(.+)$', line)
        if match:
            package_name = match.group(1).split(':')[0].strip()
            if 'com.termux' not in package_name:
                packages.append(package_name)

    if not packages:
        print("Nenhum aplicativo ativo encontrado.")
        return

    unique_packages = sorted(list(set(packages)))

    for i, package in enumerate(unique_packages):
        print(f"{i + 1}. {package}")

    selected_indices = input("Selecione os números dos aplicativos para desativar (separados por vírgula ou espaço): ").strip()

    try:
        selected_indices = list(map(int, selected_indices.replace(',', ' ').split()))

    except ValueError:
        print("Entrada inválida. Por favor, insira números separados por vírgula ou espaço.")
        return

    packages_to_disable = []

    for index in selected_indices:
        if 1 <= index <= len(unique_packages):
          packages_to_disable.append(unique_packages[index - 1])
        else:
          print(f"Número inválido: {index}")
          return

    if not packages_to_disable:
        print("Nenhum aplicativo selecionado para desativar.")
        return

    print("Aplicativos selecionados para desativar:")
    for package in packages_to_disable:
        print(f"  - {package}")

    confirm = input("Confirma desativar os aplicativos selecionados? (s/n): ").lower()

    if confirm in ["s", "sim"]:
        print("Desativando aplicativos selecionados...")
        for package in packages_to_disable:
            disable_package(package)
        print("Aplicativos selecionados desativados.")
    else:
        print("Desativação cancelada.")

def enable_selected_packages():
    """Lista todos os aplicativos (sistema e usuário) e permite reativar."""
    print("Listando todos os aplicativos (sistema e usuário):")
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages", "-f"],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Erro ao listar todos os pacotes: {e.stderr}")
        return

    packages = []
    lines = result.stdout.strip().splitlines()
    for line in lines:
        package = line.split("=")[-1].strip()
        packages.append(package)


    if not packages:
        print("Nenhum aplicativo encontrado.")
        return

    unique_packages = sorted(list(set(packages)))

    for i, package in enumerate(unique_packages):
        print(f"{i + 1}. {package}")

    selected_indices = input("Selecione os números dos aplicativos para reativar (separados por vírgula ou espaço, ou 'all' para todos): ").strip().lower()

    if selected_indices == "all":
        print("Reativando todos os aplicativos...")
        for package in unique_packages:
              enable_package(package)
        print("Todos os aplicativos foram reativados.")
        return

    try:
        selected_indices = list(map(int, selected_indices.replace(',', ' ').split()))

    except ValueError:
        print("Entrada inválida. Por favor, insira números separados por vírgula ou espaço, ou 'all'.")
        return

    packages_to_enable = []

    for index in selected_indices:
        if 1 <= index <= len(unique_packages):
          packages_to_enable.append(unique_packages[index - 1])
        else:
          print(f"Número inválido: {index}")
          return

    if not packages_to_enable:
        print("Nenhum aplicativo selecionado para reativar.")
        return
    print("Aplicativos selecionados para reativar:")
    for package in packages_to_enable:
        print(f"  - {package}")

    confirm = input("Confirma reativar os aplicativos selecionados? (s/n): ").lower()

    if confirm in ["s", "sim"]:
        print("Reativando aplicativos selecionados...")
        for package in packages_to_enable:
            enable_package(package)
        print("Aplicativos selecionados reativados.")
    else:
        print("Reativação cancelada.")


def show_menu():
    """Exibe o menu."""
    print("\nMenu:")
    print("1. Desativar Bloatware (lista)")
    print("2. Reativar Bloatware (lista)")
    print(f"3. Desativar todos os apps do usuário (exceto {EXCLUDED_PACKAGE})")
    print("4. Reativar todos os apps do usuário")
    print("5. Desativar apps ativos selecionados")
    print("6. Reativar Apps")
    print("7. Sair")
    option = input("Escolha uma opção: ")
    return option

def main():
    """Função principal do script."""
    while True:
        option = show_menu()

        if option == "1":
            print("Desativando bloatware da lista...")
            if os.path.exists(BLOATWARE_LIST):
              with open(BLOATWARE_LIST, 'r') as f:
                for package in f:
                  disable_package(package.strip())
              print("Bloatware da lista desativado.")
            else:
                print(f"Arquivo '{BLOATWARE_LIST}' não encontrado")
        elif option == "2":
            print("Reativando bloatware da lista...")
            if os.path.exists(BLOATWARE_LIST):
              with open(BLOATWARE_LIST, 'r') as f:
                for package in f:
                   enable_package(package.strip())
              print("Bloatware da lista reativado.")
            else:
              print(f"Arquivo '{BLOATWARE_LIST}' não encontrado")

        elif option == "3":
            disable_all_user_packages()
        elif option == "4":
             enable_all_user_packages()
        elif option == "5":
             disable_selected_active_packages()
        elif option == "6":
            enable_selected_packages()
        elif option == "7":
            print("Saindo...")
            break
        else:
            print("Opção inválida. Escolha 1, 2, 3, 4, 5, 6 ou 7.")


if __name__ == "__main__":
    main()