"""
Bot de Atención al Cliente - Clínica Dental Sonrisa (caso de portfolio)
=========================================================================
Bot de Telegram que:
1. Responde FAQs usando IA (Claude API)
2. Permite agendar citas (flujo guiado con botones)
3. Escala a un humano si detecta que no puede resolver la consulta

Autor: [Tu nombre] - Proyecto de portfolio freelance
"""

import logging
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TU_TOKEN_AQUI")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
HUMAN_NOTIFY_CHAT_ID = os.environ.get("HUMAN_NOTIFY_CHAT_ID", "")  # chat id del staff

client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# Estados de la conversación de agendado
NOMBRE, TELEFONO, SERVICIO, FECHA_PREFERIDA = range(4)

# Info del negocio (esto es lo que personalizarías por cliente real)
BUSINESS_INFO = """
Eres el asistente virtual de "Clínica Dental Sonrisa".
Información del negocio:
- Horario: Lunes a Viernes, 9:00 a 20:00. Sábados 10:00 a 14:00.
- Servicios: limpieza dental (45€), revisión general (gratis), ortodoncia
  (presupuesto a medida), blanqueamiento (120€), urgencias dentales.
- Dirección: Calle Mayor 45, Madrid.
- Aceptamos seguros: Adeslas, Sanitas, DKV.

Responde preguntas del cliente de forma breve, cercana y profesional (2-4 frases).
Si la pregunta no tiene que ver con la clínica, o requiere un diagnóstico médico
real, o el cliente parece molesto/es una queja formal, responde EXACTAMENTE con
la palabra "ESCALAR" y nada más.
"""

# ---------------------------------------------------------------------------
# Base de datos (SQLite simple para citas)
# ---------------------------------------------------------------------------
DB_PATH = "citas.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            nombre TEXT,
            telefono TEXT,
            servicio TEXT,
            fecha_preferida TEXT,
            creado_en TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def guardar_cita(chat_id, nombre, telefono, servicio, fecha_preferida):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO citas (chat_id, nombre, telefono, servicio, fecha_preferida, creado_en)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (chat_id, nombre, telefono, servicio, fecha_preferida, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Handlers principales
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Agendar cita", callback_data="agendar")],
        [InlineKeyboardButton("❓ Preguntar algo", callback_data="preguntar")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "¡Hola! 👋 Soy el asistente virtual de *Clínica Dental Sonrisa*.\n\n"
        "Puedo ayudarte a agendar una cita o responder tus dudas. "
        "¿Qué necesitas?",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "preguntar":
        await query.edit_message_text(
            "Perfecto, escríbeme tu pregunta y te respondo enseguida 😊"
        )
    elif query.data == "agendar":
        await query.edit_message_text("Vamos a agendar tu cita 📅\n\n¿Cuál es tu nombre completo?")
        return NOMBRE


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde preguntas libres usando Claude, o escala a humano si no puede."""
    user_message = update.message.text

    if not client:
        await update.message.reply_text(
            "⚠️ Configura tu ANTHROPIC_API_KEY para activar las respuestas con IA."
        )
        return

    await update.message.chat.send_action(action="typing")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=BUSINESS_INFO,
            messages=[{"role": "user", "content": user_message}],
        )
        reply = response.content[0].text.strip()

        if reply == "ESCALAR":
            await escalar_a_humano(update, context, user_message)
        else:
            await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error llamando a la API: {e}")
        await update.message.reply_text(
            "Ups, tuve un problema técnico. Un miembro del equipo te contactará pronto."
        )


async def escalar_a_humano(update: Update, context: ContextTypes.DEFAULT_TYPE, mensaje_original: str):
    """Notifica al staff y avisa al cliente."""
    await update.message.reply_text(
        "Tu consulta requiere atención personalizada 🙋\n"
        "He avisado a nuestro equipo, te contactarán en breve."
    )

    if HUMAN_NOTIFY_CHAT_ID:
        usuario = update.message.from_user
        aviso = (
            f"🔔 *Nueva consulta escalada*\n"
            f"Usuario: {usuario.first_name} (@{usuario.username})\n"
            f"Mensaje: {mensaje_original}"
        )
        try:
            await context.bot.send_message(
                chat_id=HUMAN_NOTIFY_CHAT_ID, text=aviso, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"No se pudo notificar al staff: {e}")


# ---------------------------------------------------------------------------
# Flujo de agendado de citas (ConversationHandler)
# ---------------------------------------------------------------------------
async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text
    await update.message.reply_text("Gracias. ¿Cuál es tu número de teléfono de contacto?")
    return TELEFONO


async def recibir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefono"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Limpieza dental", callback_data="Limpieza dental")],
        [InlineKeyboardButton("Revisión general", callback_data="Revisión general")],
        [InlineKeyboardButton("Ortodoncia", callback_data="Ortodoncia")],
        [InlineKeyboardButton("Blanqueamiento", callback_data="Blanqueamiento")],
    ]
    await update.message.reply_text(
        "¿Qué servicio necesitas?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SERVICIO


async def recibir_servicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["servicio"] = query.data
    await query.edit_message_text(
        f"Servicio: {query.data}\n\n¿Qué día y franja horaria prefieres? (ej: 'martes por la tarde')"
    )
    return FECHA_PREFERIDA


async def recibir_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["fecha_preferida"] = update.message.text

    guardar_cita(
        chat_id=update.message.chat_id,
        nombre=context.user_data["nombre"],
        telefono=context.user_data["telefono"],
        servicio=context.user_data["servicio"],
        fecha_preferida=context.user_data["fecha_preferida"],
    )

    resumen = (
        "✅ *¡Cita solicitada!*\n\n"
        f"👤 Nombre: {context.user_data['nombre']}\n"
        f"📞 Teléfono: {context.user_data['telefono']}\n"
        f"🦷 Servicio: {context.user_data['servicio']}\n"
        f"📅 Preferencia: {context.user_data['fecha_preferida']}\n\n"
        "Nuestro equipo confirmará el horario exacto por teléfono en breve."
    )
    await update.message.reply_text(resumen, parse_mode="Markdown")
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Agendado cancelado. Escribe /start si quieres empezar de nuevo.")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^agendar$")],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_telefono)],
            SERVICIO: [CallbackQueryHandler(recibir_servicio)],
            FECHA_PREFERIDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^preguntar$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    logger.info("Bot iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
