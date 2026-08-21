# hobot-metrics

Docker Compose стек для мониторинга робота-пылесоса Hobot Legee 7 через локальный протокол Tuya (без облака), с визуализацией в Grafana.

## Состав

- **exporter** — Python-сервис, опрашивает пылесос напрямую по локальной сети через `tinytuya` и отдаёт метрики в формате Prometheus на `:9099/metrics`.
- **prometheus** — собирает метрики с exporter'а каждые 15 секунд.
- **grafana** — дашборд с визуализацией (заряд батареи, статус, площадь и время уборки, ошибки).

## Быстрый старт

1. Скопируй `.env.example` в `.env`:
   ```
   cp .env.example .env
   ```
   Впиши свои значения `HOBOT_DEVICE_ID`, `HOBOT_DEVICE_IP`, `HOBOT_LOCAL_KEY` (см. `docs/REVERSE_ENGINEERING.md`, как их получить) — и **обязательно смени `GRAFANA_ADMIN_PASSWORD`** на что-то своё.

2. Подними стек:
   ```
   docker compose up -d --build
   ```

3. Открой:
   - Grafana: http://localhost:3000 (логин/пароль из `.env`)
   - Prometheus: http://localhost:9090
   - Сырые метрики exporter'а: http://localhost:9099/metrics

Дашборд "Hobot Legee 7 — Метрики пылесоса" должен появиться в Grafana автоматически (через provisioning), без ручной настройки.

## Важные нюансы

- **IP пылесоса может смениться** (DHCP), если у тебя на роутере не закреплена статическая аренда — тогда `HOBOT_DEVICE_IP` в `.env` нужно будет обновить и перезапустить `hobot-exporter` (`docker compose restart hobot-exporter`). Рекомендуется сразу закрепить статический IP/DHCP-резервацию для пылесоса на роутере.

## Дальнейшее развитие

- Можно добавить алерты в Grafana (например, на низкий заряд батареи или код ошибки != 0).
- Можно расширить exporter, добавив больше data points из схемы устройства (расписания уборки, состояние отдельных модулей и т.д.) — они видны в `dps` в логах exporter'а.
- Если IP пылесоса плавает, можно заменить статичный IP на периодическое обнаружение через `tinytuya.deviceScan()` внутри exporter'а.

## Документация проекта

- [`CHANGELOG.md`](./CHANGELOG.md) — история версий
- [`docs/REVERSE_ENGINEERING.md`](./docs/REVERSE_ENGINEERING.md) — как были добыты devId/localKey (методология, без секретов)
- [`docs/NETWORK_SETUP.md`](./docs/NETWORK_SETUP.md) — настройка VPN-гейтед доступа к Grafana (WireGuard + Xray)
- [`scripts/`](./scripts/) — вспомогательные скрипты (Frida-хуки, диагностика tinytuya)
