#!/bin/bash
# deploy.sh — деплой на monster
# Использование: bash deploy.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARCHIVE=/tmp/bioequiv_deploy.tar.gz
REMOTE_DIR=/root/bioequiv
REMOTE=monster

echo "=== Деплой на $REMOTE ==="

# 1. Собрать архив (исключаем тяжёлые файлы — уже есть на сервере)
echo "[1/4] Сборка архива..."
tar czf "$ARCHIVE" \
  --exclude='data/fda_psg' \
  --exclude='data/ohlp_pk_texts.csv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.venv' \
  -C "$PROJECT_DIR" \
  data/ pipeline/ assets/ tests/ scripts/ pages/ docs/ .streamlit/ \
  "1_💊_Анализ.py" run.py requirements.txt README.md DATA.md DEPLOY.md deploy.sh \
  .env 2>/dev/null || true
echo "  Архив: $(du -sh $ARCHIVE | cut -f1)"

# 2. Загрузить на сервер
echo "[2/4] Загрузка на $REMOTE..."
scp "$ARCHIVE" "$REMOTE":~/

# Тяжёлые файлы — только если их ещё нет на сервере
for HEAVY in "data/ohlp_pk_texts.csv"; do
  LOCAL_FILE="$PROJECT_DIR/$HEAVY"
  REMOTE_FILE="$REMOTE_DIR/$HEAVY"
  if [ -f "$LOCAL_FILE" ]; then
    EXISTS=$(ssh -o BatchMode=yes "$REMOTE" "[ -f $REMOTE_FILE ] && echo yes || echo no")
    if [ "$EXISTS" = "no" ]; then
      echo "  Загружаем $HEAVY (первый раз)..."
      ssh -o BatchMode=yes "$REMOTE" "mkdir -p $REMOTE_DIR/data"
      scp "$LOCAL_FILE" "$REMOTE:$REMOTE_FILE"
    else
      echo "  $HEAVY уже на сервере — пропускаем"
    fi
  fi
done

# 3. Распаковать (--warning=no-unknown-keyword подавляет macOS xattr warnings)
echo "[3/4] Распаковка..."
ssh -o BatchMode=yes "$REMOTE" "
  mkdir -p $REMOTE_DIR
  cd $REMOTE_DIR
  tar xzf ~/bioequiv_deploy.tar.gz --warning=no-unknown-keyword 2>&1 | tail -5
  echo '  Файлов в data/: '
  ls data/ | wc -l
"

# Удалить старые файлы на сервере (если остались)
ssh -o BatchMode=yes "$REMOTE" "
  cd $REMOTE_DIR
  rm -f data/vidal_drugs.csv data/vidal_drugs_full.csv data/fda_psg_oral_urls_and_pdfs.zip app.py 2>/dev/null
"

# 4. Перезапустить Streamlit
echo "[4/4] Перезапуск Streamlit..."
cat > /tmp/_start_sl.sh << 'EOF'
#!/bin/bash
pkill -9 -f 'streamlit run' 2>/dev/null || true
sleep 1
cd ~/bioequiv
if [ ! -d .venv ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -q -r requirements.txt
else
  source .venv/bin/activate
  pip install -q -r requirements.txt 2>/dev/null
fi
nohup streamlit run "1_💊_Анализ.py" \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true \
  > /tmp/streamlit.log 2>&1 &
echo $!
EOF
scp /tmp/_start_sl.sh "$REMOTE":/tmp/_start_sl.sh > /dev/null
PID=$(ssh -o BatchMode=yes "$REMOTE" "bash /tmp/_start_sl.sh")
sleep 3
LOG=$(ssh -o BatchMode=yes "$REMOTE" "tail -3 /tmp/streamlit.log 2>/dev/null")

echo ""
echo "=== Готово ==="
echo "  PID:    $PID"
echo "  URL:    http://89.167.40.65:8501"
echo "  Логи:   ssh $REMOTE 'tail -f /tmp/streamlit.log'"
echo ""
echo "$LOG"
