# Деплой

**Текущее демо:** http://89.167.40.65:8501 (доступно только через VPN)

---

## Локальный запуск

```bash
git clone https://github.com/YOUR_USER/bioequiv.git
cd bioequiv

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Скачать данные

Скачайте все CSV с [Яндекс.Диска](https://disk.360.yandex.ru/d/MCD1W5t7eObHfg) и положите в папку `data/`:

```
mkdir -p data
# скачать 9 файлов в data/
```

### API ключ

```bash
echo "DEEPSEEK_API_KEY=sk-..." > .env
```

Без ключа приложение работает, но LLM-генерация отключена.

### Запуск

```bash
streamlit run "1_💊_Анализ.py" --server.port 8501
```

CLI:
```bash
python run.py --inn "аторвастатин"
```

### Тесты

```bash
python -m pytest tests/ -v
```

---

## Деплой на сервер

### 1. Подготовить сервер

```bash
# На сервере: Python 3.9+, pip, venv
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
```

### 2. Загрузить код

```bash
# С локальной машины:
scp -r . user@server:/opt/bioequiv
# или через git:
ssh user@server "cd /opt && git clone https://github.com/YOUR_USER/bioequiv.git"
```

### 3. Загрузить данные

```bash
# Скачать CSV с Яндекс.Диска на сервер в /opt/bioequiv/data/
ssh user@server "mkdir -p /opt/bioequiv/data"
scp data/*.csv user@server:/opt/bioequiv/data/
```

### 4. Установить зависимости

```bash
ssh user@server "cd /opt/bioequiv && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
```

### 5. API ключ

```bash
ssh user@server 'echo "DEEPSEEK_API_KEY=sk-..." > /opt/bioequiv/.env'
```

### 6. Запуск

```bash
ssh user@server "cd /opt/bioequiv && source .venv/bin/activate && nohup streamlit run '1_💊_Анализ.py' --server.port 8501 --server.address 0.0.0.0 --server.headless true > /tmp/streamlit.log 2>&1 &"
```

### 7. Проверить

```bash
curl http://server:8501
```

### Обновление

```bash
ssh user@server "cd /opt/bioequiv && git pull && source .venv/bin/activate && pip install -q -r requirements.txt"
# Перезапуск:
ssh user@server "pkill -f 'streamlit run' && cd /opt/bioequiv && source .venv/bin/activate && nohup streamlit run '1_💊_Анализ.py' --server.port 8501 --server.address 0.0.0.0 --server.headless true > /tmp/streamlit.log 2>&1 &"
```
