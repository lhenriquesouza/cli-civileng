#!/usr/bin/env bash
# install.sh — One-liner installer for CLI CivilEng
# Usage: curl -fsSL https://raw.githubusercontent.com/lhenriquesouza/cli-civileng/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/lhenriquesouza/cli-civileng.git"
INSTALL_DIR="${CLI_CIVILENG_HOME:-$HOME/.cli-civileng}"
BIN_DIR="${CLI_CIVILENG_BIN:-$HOME/.local/bin}"

# ── Colors ──────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${GREEN}→${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC}  $*"; }
error() { echo -e "${RED}✗${NC}  $*"; exit 1; }

echo ""
echo -e "${BOLD}🏗️  CLI CivilEng — Instalador${NC}"
echo "=================================="
echo ""

# ── Prerequisites ───────────────────────────────────────
info "Verificando pré-requisitos..."

if ! command -v python3 &>/dev/null; then
    error "python3 não encontrado. Instale Python 3.11+ primeiro."
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    error "Python 3.11+ requerido. Versão encontrada: $PY_VERSION"
fi
info "Python $PY_VERSION ✓"

if ! command -v git &>/dev/null; then
    warn "git não encontrado — tentando instalar..."
    if command -v apt &>/dev/null; then
        sudo apt update -qq && sudo apt install -y -qq git
    elif command -v brew &>/dev/null; then
        brew install git
    else
        error "Instale git manualmente: https://git-scm.com/downloads"
    fi
fi
info "git ✓"

# ── Clone / update repo ─────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    info "Repositório já existe em $INSTALL_DIR — atualizando..."
    cd "$INSTALL_DIR"
    git pull origin main --ff-only 2>/dev/null || warn "git pull falhou, usando versão local"
else
    info "Clonando repositório..."
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── Virtual environment ─────────────────────────────────
if [ ! -d "venv" ]; then
    info "Criando ambiente virtual..."
    python3 -m venv venv
fi

info "Instalando dependências..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -e . -q

# ── CLI wrapper script ──────────────────────────────────
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/cli-civileng" << 'WRAPPER'
#!/usr/bin/env bash
# Wrapper: ativa o venv e executa a CLI
INSTALL_DIR="${CLI_CIVILENG_HOME:-$HOME/.cli-civileng}"
if [ ! -f "$INSTALL_DIR/venv/bin/activate" ]; then
    echo "❌ CLI CivilEng não instalada. Rode o install.sh primeiro." >&2
    exit 1
fi
source "$INSTALL_DIR/venv/bin/activate"
exec python3 -m cli_civileng.main "$@"
WRAPPER
chmod +x "$BIN_DIR/cli-civileng"

# ── PATH check ──────────────────────────────────────────
if ! echo "$PATH" | tr ':' '\n' | grep -qxF "$BIN_DIR"; then
    SHELL_RC=""
    case "$SHELL" in
        */zsh)   SHELL_RC="$HOME/.zshrc" ;;
        */bash)  SHELL_RC="$HOME/.bashrc" ;;
        */fish)  SHELL_RC="$HOME/.config/fish/config.fish" ;;
        *)       SHELL_RC="$HOME/.profile" ;;
    esac

    if [ -f "$SHELL_RC" ]; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
        info "Adicionado $BIN_DIR ao PATH em $SHELL_RC"
    fi
    export PATH="$BIN_DIR:$PATH"
fi

# ── Config ──────────────────────────────────────────────
if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
    cp "$INSTALL_DIR/config.yaml.example" "$INSTALL_DIR/config.yaml"
    warn "Arquivo config.yaml criado em $INSTALL_DIR/config.yaml"
    echo "   ${BOLD}Edite-o com sua API key do OpenRouter:${NC}"
    echo "   ${YELLOW}nano $INSTALL_DIR/config.yaml${NC}"
    echo ""
fi

# ── Done ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}✅ CLI CivilEng instalada com sucesso!${NC}"
echo ""
echo "   Comandos disponíveis:"
echo "     cli-civileng --help"
echo "     cli-civileng extract-rules"
echo "     cli-civileng validate"
echo ""
echo "   ⚠️  Antes de usar, configure sua API key:"
echo "     nano $INSTALL_DIR/config.yaml"
echo ""
if command -v cli-civileng &>/dev/null; then
    echo "   Pronto para usar! Execute: ${BOLD}cli-civileng --help${NC}"
else
    echo "   Reinicie o terminal ou rode: ${BOLD}source $SHELL_RC${NC}"
fi
echo ""
