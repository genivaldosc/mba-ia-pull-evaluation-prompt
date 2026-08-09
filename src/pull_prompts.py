"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt do LangSmith Prompt Hub e salva localmente em YAML.

    Returns:
        True se sucesso, False caso contrário
    """
    # Verifica credenciais obrigatórias
    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return False

    # Nome do prompt no Hub (owner/prompt_name)
    prompt_hub_name = "leonanluppi/bug_to_user_story_v1"

    print_section_header(f"Pull do prompt: {prompt_hub_name}")

    try:
        # Faz o pull do prompt usando o Client do LangSmith
        print("📥 Baixando prompt do LangSmith Hub...")
        client = Client()
        prompt = client.pull_prompt(prompt_hub_name)
        print(f"✅ Prompt baixado com sucesso: {type(prompt).__name__}")
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt: {e}")
        return False

    # Extrai system_prompt e user_prompt do ChatPromptTemplate
    system_prompt = ""
    user_prompt = ""

    for message in prompt.messages:
        # O template fica em message.prompt.template
        template = getattr(getattr(message, "prompt", None), "template", None) or ""
        # Identifica o role pelo tipo da classe (SystemMessagePromptTemplate / HumanMessagePromptTemplate)
        class_name = type(message).__name__.lower()
        if "system" in class_name:
            system_prompt = template
        elif "human" in class_name:
            user_prompt = template

    # Monta a estrutura YAML no mesmo formato do arquivo existente
    prompt_key = prompt_hub_name.split("/")[-1]  # bug_to_user_story_v1
    prompt_data = {
        prompt_key: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "created_at": "2025-01-15",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    # Salva localmente
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts",
        "bug_to_user_story_v1.yml",
    )

    print(f"💾 Salvando prompt em: {output_path}")
    if save_yaml(prompt_data, output_path):
        print("✅ Prompt salvo com sucesso!")
        print(f"   - System prompt: {len(system_prompt)} caracteres")
        print(f"   - User prompt: {len(user_prompt)} caracteres")
        return True
    else:
        print("❌ Falha ao salvar o prompt.")
        return False


def main():
    """Função principal"""
    print_section_header("Pull de Prompts do LangSmith")
    success = pull_prompts_from_langsmith()
    if success:
        print("\n🎉 Operação concluída com sucesso!")
        return 0
    else:
        print("\n💥 Operação falhou.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
