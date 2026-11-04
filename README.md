# hobot-metrics

Мониторинг робота-пылесоса Hobot Legee 7 через локальный протокол Tuya (без облака), с визуализацией в Grafana. Доступ к дашборду — только через собственный VPN-туннель, из любой точки.

> Проект для личного использования и совместимости с уже купленным устройством.
> Не аффилирован с Hobot, Tuya или связанными компаниями — все названия
> упомянуты исключительно в целях описания совместимости. См. `LICENSE`.

## Архитектура

- **exporter** — Python-сервис, опрашивает устройство напрямую по локальной сети через `tinytuya` и отдаёт метрики в формате Prometheus на `:9099/metrics`. Живёт на отдельном всегда включённом устройстве в домашней сети (роутер с Entware, Raspberry Pi и т.д. — см. `router/README.md`). Может также работать в Docker (см. `exporter/`), если такой вариант удобнее.
- **prometheus** — собирает метрики с exporter'а раз в 60 секунд. Развёрнут на VPS, достаёт данные через WireGuard-туннель до домашнего устройства с exporter'ом.
- **grafana** — дашборд с визуализацией (заряд батареи, статус, площадь и время уборки, ошибки). Тоже на VPS, доступ ограничен только через VPN — см. `docs/NETWORK_SETUP.md`.

Оба Docker-сервиса (Prometheus, Grafana) запущены с лимитами памяти и CPU, чтобы не мешать другим сервисам на том же VPS.

## Быстрый старт

1. Разверни exporter на отдельном всегда включённом устройстве в домашней сети —
   см. `router/README.md`. Впиши свои `HOBOT_DEVICE_ID`/`HOBOT_DEVICE_IP`/`HOBOT_LOCAL_KEY` прямо в скрипт автозапуска (см. `docs/REVERSE_ENGINEERING.md`, как их получить).

2. Настрой WireGuard-туннель между VPS и этим устройством — см. `docs/NETWORK_SETUP.md`.

3. На VPS: скопируй `.env.example` в `.env`, смени `GRAFANA_ADMIN_PASSWORD`.

4. Обнови `prometheus/prometheus.yml` — укажи реальный адрес exporter'а внутри туннеля.

5. Подними Prometheus + Grafana на VPS:
   ```
   docker compose up -d
   ```

6. Дашборд "Hobot Legee 7 — Метрики пылесоса" должен появиться в Grafana автоматически (через provisioning). Доступ — только через VPN (см. `docs/NETWORK_SETUP.md`).

## Server-specific settings

Развернутый сервер может отличаться от кода в репозитории в нескольких местах из-за ручных правок:

- `prometheus/prometheus.yml`: адрес экспортера внутри WireGuard-туннеля
- Git-игнорирует локальные файлы: `.env`, `docker-compose.override.yml`, `alertmanager/`, `prometheus/extra/`.

## Важные нюансы

- **IP устройства-экспортера может смениться** (DHCP) — закрепи статическую
  DHCP-резервацию на роутере, чтобы избежать этого.
- **`HOBOT_LOCAL_KEY` — секрет уровня пароля** к устройству. Не публикуй его нигде.

## Дальнейшее развитие

- Можно добавить алерты в Grafana (например, на низкий заряд батареи или код ошибки != 0).
- Можно расширить exporter, добавив больше data points из схемы устройства (расписания уборки, состояние отдельных модулей и т.д.) — они видны в `dps` в логах exporter'а.

## Документация проекта

- [`LICENSE`](./LICENSE) — условия использования
- [`CHANGELOG.md`](./CHANGELOG.md) — история версий
- [`docs/REVERSE_ENGINEERING.md`](./docs/REVERSE_ENGINEERING.md) — как были добыты devId/localKey (методология, без секретов)
- [`docs/NETWORK_SETUP.md`](./docs/NETWORK_SETUP.md) — архитектура доступа: Prometheus+Grafana на VPS, VPN-гейтед доступ
- [`router/README.md`](./router/README.md) — запуск exporter'а на отдельном всегда включённом устройстве (роутер/Raspberry Pi)
- [`scripts/`](./scripts/) — вспомогательные скрипты (Frida-хуки, диагностика tinytuya)
