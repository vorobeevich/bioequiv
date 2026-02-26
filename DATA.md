# Данные

Данные не входят в репозиторий. Скачайте с Яндекс.Диска и положите в `data/`.

**[Скачать данные с Яндекс.Диска](https://disk.360.yandex.ru/d/MCD1W5t7eObHfg)**

---

## Файлы данных

| Файл | Размер | Источник | Стадия | Назначение |
|------|--------|----------|--------|------------|
| `eaeu_registry.csv` | 3.2 MB | Реестр ЕАЭС | 1 | МНН → оригинальный препарат |
| `vidal_molecules.csv` | 15 MB | Видаль | 2 | Вещества: рус↔лат, ФК текст |
| `vidal_drugs_merged.csv` | 86 MB | Видаль | 2 | Препараты: ФК, фармакология, противопоказания |
| `edrug3d_pk.csv` | 208 KB | e-Drug3D | 2 | Cmax, Tmax, T½ по веществам |
| `osp_pk_parameters.csv` | 339 KB | OSP | 2 | AUC, Cmax, CV% |
| `cvintra_pmc.csv` | 5 KB | PMC6989220 | 2 | CVintra Cmax/AUC (53 вещества) |
| `drugbank_pk.csv` | 18 MB | DrugBank | 2 | Absorption, half-life, clearance |
| `ohlp_pk_texts.csv` | 460 MB | ГРЛС ЕАЭС | 2 | ОХЛП: 15 разделов из PDF |
| `fda_psg_parsed.csv` | 1.9 MB | FDA PSG | 2 | Дизайн BE, CVintra, NTI/HVD |
| **Итого** | **~585 MB** | | | |

---

## Конфигурация

Все пути к данным задаются в `pipeline/config.py`. Приложение читает **только** файлы из `data/`.

При отсутствии `ohlp_pk_texts.csv` или `fda_psg_parsed.csv` приложение работает, но без этих источников (флаги `OHLP_ENABLED`, `FDA_PSG_ENABLED`).
