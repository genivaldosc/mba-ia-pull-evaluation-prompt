"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
V2_FILE = PROMPTS_DIR / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestPrompts:
    def setup_method(self):
        """Carrega o prompt v2 antes de cada teste."""
        self.data = load_prompts(str(V2_FILE))
        # O YAML tem uma chave raiz com o nome do prompt
        self.prompt = list(self.data.values())[0]
        self.system_prompt = self.prompt.get("system_prompt", "")

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in self.prompt, "Campo 'system_prompt' não encontrado"
        assert self.system_prompt.strip(), "system_prompt está vazio"

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        assert "Você é um Product Manager" in self.system_prompt, (
            "Prompt não define a persona 'Product Manager'"
        )

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        assert "Markdown" in self.system_prompt or "MARKDOWN" in self.system_prompt, (
            "Prompt não exige formato Markdown"
        )

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        assert "EXEMPLO" in self.system_prompt, (
            "Prompt não contém exemplos Few-shot"
        )
        assert "Saída Esperada" in self.system_prompt, (
            "Prompt não contém exemplos de saída esperada"
        )

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        assert "[TODO]" not in self.system_prompt, (
            "system_prompt ainda contém marcadores [TODO]"
        )

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = self.prompt.get("techniques_applied", [])
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])