"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

# Caminho base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT_FILE = os.path.join(BASE_DIR, "prompts", "bug_to_user_story_v2.yml")


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ["description", "system_prompt", "user_prompt", "version"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    system_prompt = prompt_data.get("system_prompt", "").strip()
    if not system_prompt:
        errors.append("system_prompt está vazio")

    if "[TODO]" in system_prompt:
        errors.append("system_prompt ainda contém marcadores [TODO]")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"
        )

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(
    prompt_name: str, prompt_data: dict, public_identifier: str = None
) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt (repo_handle, ex: bug_to_user_story_v2)
        prompt_data: Dados do prompt
        public_identifier: Identificador público {username}/{repo} para exibição

    Returns:
        True se sucesso, False caso contrário
    """
    # Valida antes de enviar
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Validação falhou:")
        for err in errors:
            print(f"   - {err}")
        return False

    # Extrai campos do YAML
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data["user_prompt"]
    description = prompt_data.get("description", "")
    tags = prompt_data.get("tags", [])
    techniques = prompt_data.get("techniques_applied", [])

    # Cria o ChatPromptTemplate (formato esperado pelo LangSmith Hub)
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt),
    ])

    print(f"📤 Publicando prompt: {prompt_name}")
    print(f"   - Descrição: {description}")
    print(f"   - Tags: {tags}")
    print(f"   - Técnicas: {techniques}")

    display_id = public_identifier or prompt_name

    try:
        client = Client()

        def _do_push(is_public: bool) -> bool:
            """Empacota o push tratando o caso idempotente (409)."""
            try:
                client.push_prompt(
                    prompt_name,
                    object=chat_prompt,
                    description=description,
                    tags=tags,
                    is_public=is_public,
                )
                vis = "PÚBLICO" if is_public else "PRIVADO"
                print(f"✅ Prompt publicado como {vis} no LangSmith Hub!")
                return True
            except Exception as push_err:
                err_msg = str(push_err).lower()
                if "nothing to commit" in err_msg or "409" in err_msg:
                    print("✅ Prompt já está atualizado no LangSmith Hub (sem mudanças).")
                    return True
                raise

        # Tenta publicar como público primeiro
        try:
            _do_push(is_public=True)
        except Exception as pub_err:
            err_msg = str(pub_err).lower()
            # Se falhar por falta de handle público, publica como privado
            if "handle" in err_msg or "public" in err_msg:
                print("⚠️  Não foi possível publicar como público (handle não criado).")
                print("   Publicando como PRIVADO. Para torná-lo público:")
                print("   1. Acesse https://smith.langchain.com/prompts")
                print("   2. Crie um prompt público para gerar seu handle")
                print("   3. Reexecute este script")
                _do_push(is_public=False)
            else:
                raise
        print(f"   - URL: https://smith.langchain.com/hub/{display_id}")
        return True
    except Exception as e:
        print(f"❌ Erro ao publicar prompt: {e}")
        return False


def main():
    """Função principal"""
    print_section_header("Push de Prompts para o LangSmith Hub")

    # Verifica credenciais obrigatórias
    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    # Carrega o prompt otimizado do YAML
    print(f"📂 Carregando prompt de: {PROMPT_FILE}")
    data = load_yaml(PROMPT_FILE)
    if not data:
        print("❌ Falha ao carregar o arquivo YAML.")
        return 1

    # O YAML tem uma chave raiz (bug_to_user_story_v2)
    prompt_key = list(data.keys())[0]
    prompt_data = data[prompt_key]

    # O LangSmith resolve o tenant automaticamente pela API key.
    # O push_prompt recebe apenas o repo_handle (ex: bug_to_user_story_v2),
    # sem prefixo de username. O Hub identifica publicamente como {handle}/{repo}.
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = prompt_key  # ex: bug_to_user_story_v2
    public_identifier = f"{username}/{prompt_key}"  # para exibição

    # Faz o push
    success = push_prompt_to_langsmith(
        prompt_name, prompt_data, public_identifier=public_identifier
    )
    if success:
        print("\n🎉 Operação concluída com sucesso!")
        print("   Verifique no dashboard do LangSmith se o prompt foi publicado.")
        return 0
    else:
        print("\n💥 Operação falhou.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
