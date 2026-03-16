from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import httpx
import os
from datetime import datetime, timedelta
from pathlib import Path

# ==============================================================================
# wifi-dashboard — Backend FastAPI
# Ubicación: ~/wifi-stability-monitor/dashboard/main.py
# Ejecutar: uvicorn dashboard.main:app --host 0.0.0.0 --port 8088
# ==============================================================================

CSV_PATH = Path("/var/log/wifi-metrics.csv")

# --- Configuración Telegram ----------------------------------------------------
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_URL     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Cooldown: no repetir la misma alerta dentro de este tiempo
COOLDOWN_MINUTOS = 15

# Registro de última alerta enviada por tipo
_ultimo_alerta: dict[str, datetime] = {}

app = FastAPI(title="WiFi Stability Monitor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Telegram ------------------------------------------------------------------

def enviar_alerta(tipo: str, mensaje: str):
    """Envía alerta por Telegram respetando el cooldown por tipo."""
    ahora = datetime.now()
    ultima = _ultimo_alerta.get(tipo)
    if ultima and (ahora - ultima) < timedelta(minutes=COOLDOWN_MINUTOS):
        return  # En cooldown, no spamear
    try:
        with httpx.Client(timeout=5) as client:
            client.post(TELEGRAM_URL, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": mensaje,
                "parse_mode": "HTML"
            })
        _ultimo_alerta[tipo] = ahora
    except Exception:
        pass  # Si falla Telegram, no interrumpir el endpoint


def evaluar_alertas(latencia, signal, packet_loss, uptime, caidas_hoy):
    """Evalúa umbrales y dispara alertas si corresponde."""
    ts = datetime.now().strftime("%H:%M:%S")

    if latencia is not None and latencia > 150:
        enviar_alerta("latencia",
            f"⚠️ <b>WiFi Monitor — Latencia alta</b>\n"
            f"Latencia: <b>{latencia} ms</b> (umbral: 150 ms)\n"
            f"🕐 {ts}")

    if signal is not None and signal < -75:
        enviar_alerta("signal",
            f"⚠️ <b>WiFi Monitor — Señal débil</b>\n"
            f"Señal: <b>{signal} dBm</b> (umbral: -75 dBm)\n"
            f"🕐 {ts}")

    if packet_loss is not None and packet_loss > 5:
        enviar_alerta("packet_loss",
            f"⚠️ <b>WiFi Monitor — Packet loss elevado</b>\n"
            f"Packet loss: <b>{packet_loss}%</b> (umbral: 5%)\n"
            f"🕐 {ts}")

    if uptime < 95:
        enviar_alerta("uptime",
            f"🔴 <b>WiFi Monitor — Uptime crítico</b>\n"
            f"Uptime del día: <b>{uptime}%</b> (umbral: 95%)\n"
            f"🕐 {ts}")

    if caidas_hoy >= 5:
        enviar_alerta("caidas",
            f"🔴 <b>WiFi Monitor — Múltiples caídas</b>\n"
            f"Caídas hoy: <b>{caidas_hoy}</b> (umbral: 5)\n"
            f"🕐 {ts}")


# --- Helpers -------------------------------------------------------------------

def load_csv() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
    df = df.replace("-", None)
    df["latencia_ms"] = pd.to_numeric(df["latencia_ms"], errors="coerce")
    df["signal_dbm"] = pd.to_numeric(df["signal_dbm"], errors="coerce")
    df["packet_loss_pct"] = pd.to_numeric(df["packet_loss_pct"], errors="coerce")
    return df.sort_values("timestamp")


def semaforo_latencia(val):
    if val is None:
        return "rojo"
    if val < 50:
        return "verde"
    if val < 150:
        return "amarillo"
    return "rojo"


def semaforo_signal(val):
    if val is None:
        return "rojo"
    if val > -65:
        return "verde"
    if val > -75:
        return "amarillo"
    return "rojo"


def semaforo_packet_loss(val):
    if val is None:
        return "rojo"
    if val == 0:
        return "verde"
    if val <= 5:
        return "amarillo"
    return "rojo"


def semaforo_uptime(val):
    if val >= 99:
        return "verde"
    if val >= 95:
        return "amarillo"
    return "rojo"


# --- Endpoints -----------------------------------------------------------------

@app.get("/api/kpis")
def get_kpis():
    """KPIs actuales basados en los últimos 30 minutos."""
    df = load_csv()
    ahora = df["timestamp"].max()
    reciente = df[df["timestamp"] >= ahora - timedelta(minutes=30)]

    # Último registro
    ultimo = df.iloc[-1]
    estado_actual = ultimo["estado"]

    # Latencia promedio (últimos 30 min)
    latencia_avg = reciente["latencia_ms"].mean()
    latencia_avg = round(latencia_avg, 1) if pd.notna(latencia_avg) else None

    # Señal actual
    signal_actual = ultimo["signal_dbm"]
    signal_actual = float(signal_actual) if pd.notna(signal_actual) else None

    # Packet loss promedio (últimos 30 min)
    pl_avg = reciente["packet_loss_pct"].mean()
    pl_avg = round(pl_avg, 1) if pd.notna(pl_avg) else None

    # Uptime del día
    hoy = df[df["timestamp"].dt.date == ahora.date()]
    total = len(hoy)
    conectados = len(hoy[hoy["estado"] == "conectado"])
    uptime_pct = round((conectados / total) * 100, 2) if total > 0 else 100.0

    # Caídas del día
    caidas_hoy = len(hoy[hoy["evento"] == "caida"])

    # Evaluar alertas
    evaluar_alertas(latencia_avg, signal_actual, pl_avg, uptime_pct, caidas_hoy)

    return {
        "estado_actual": estado_actual,
        "latencia_ms": {
            "valor": latencia_avg,
            "semaforo": semaforo_latencia(latencia_avg),
            "unidad": "ms",
            "descripcion": "Promedio últimos 30 min"
        },
        "signal_dbm": {
            "valor": signal_actual,
            "semaforo": semaforo_signal(signal_actual),
            "unidad": "dBm",
            "descripcion": "Valor actual"
        },
        "packet_loss": {
            "valor": pl_avg,
            "semaforo": semaforo_packet_loss(pl_avg),
            "unidad": "%",
            "descripcion": "Promedio últimos 30 min"
        },
        "uptime": {
            "valor": uptime_pct,
            "semaforo": semaforo_uptime(uptime_pct),
            "unidad": "%",
            "descripcion": "Uptime del día"
        },
        "caidas_hoy": caidas_hoy,
        "ultimo_registro": ahora.isoformat()
    }


@app.get("/api/historico")
def get_historico(horas: int = 6):
    """Serie temporal para los gráficos de línea."""
    df = load_csv()
    ahora = df["timestamp"].max()
    desde = ahora - timedelta(hours=horas)
    df = df[df["timestamp"] >= desde]

    return {
        "timestamps": df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist(),
        "latencia_ms": df["latencia_ms"].tolist(),
        "signal_dbm": df["signal_dbm"].tolist(),
        "packet_loss_pct": df["packet_loss_pct"].tolist(),
        "eventos": df["evento"].tolist()
    }


@app.get("/api/caidas")
def get_caidas():
    """Lista de eventos de caída registrados."""
    df = load_csv()
    caidas = df[df["evento"] == "caida"][["timestamp", "signal_dbm"]].copy()
    caidas["timestamp"] = caidas["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return caidas.to_dict(orient="records")


@app.get("/health")
def health():
    return {"status": "ok", "csv": str(CSV_PATH), "existe": CSV_PATH.exists()}
