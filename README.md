# 🦷 Bot de Atención al Cliente para Telegram — Clínica Dental Sonrisa

Bot de atención al cliente construido con Python que automatiza la
comunicación de un negocio con sus clientes: responde preguntas frecuentes
usando IA, gestiona el agendado de citas, y escala a un humano cuando la
consulta lo requiere.

> **Nota:** este es un proyecto de portfolio con un caso ficticio (clínica
> dental), pero la arquitectura es genérica y se adapta a cualquier negocio:
> restaurantes, tiendas online, inmobiliarias, gestorías, etc.

## ✨ Funcionalidades

- **Respuestas inteligentes**: usa la API de Claude para responder preguntas
  sobre horarios, servicios y precios con un tono natural y cercano.
- **Agendado de citas guiado**: flujo conversacional con botones que recoge
  nombre, teléfono, servicio y fecha preferida, y lo guarda en base de datos.
- **Escalado automático a humano**: si detecta que la consulta no puede
  resolverla sola (queja, urgencia médica, tema fuera de alcance), avisa al
  equipo automáticamente por Telegram.
- **Base de datos local**: las citas se guardan en SQLite, listo para
  consultar o exportar.

## 🛠️ Stack técnico

- Python 3.10+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — API de Telegram
- [Anthropic API](https://www.anthropic.com) (Claude) — generación de respuestas
- SQLite — persistencia de citas

## 🚀 Cómo ejecutarlo

1. Clona el repositorio e instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Crea un bot en Telegram hablando con [@BotFather](https://t.me/BotFather)
   y copia el token que te da.

3. Copia `.env.example` a `.env` y rellena tus credenciales:
   ```bash
   cp .env.example .env
   ```

4. Ejecuta el bot:
   ```bash
   python bot.py
   ```

5. Abre tu bot en Telegram y escribe `/start`.

## 📁 Estructura del proyecto

```
telegram-bot-portfolio/
├── bot.py              # Lógica principal del bot
├── requirements.txt    # Dependencias
├── .env.example        # Plantilla de variables de entorno
├── citas.db             # Base de datos SQLite (se crea automáticamente)
└── README.md
```

## 🔧 Cómo adaptarlo a otro negocio

Este bot está diseñado para adaptarse rápido a cualquier cliente:

1. Cambia el contenido de `BUSINESS_INFO` en `bot.py` con la información del
   negocio real (horarios, servicios, precios, dirección).
2. Ajusta los botones de servicios en `recibir_telefono()` según lo que
   ofrezca el negocio.
3. Personaliza los mensajes de bienvenida y confirmación.
4. (Opcional) Conecta la base de datos a Google Sheets, Notion o un CRM real
   en lugar de SQLite, para negocios que ya usan esas herramientas.

## 💡 Posibles mejoras (para propuestas a clientes)

- Integración con Google Calendar para bloquear horarios reales.
- Panel de administración web para ver citas y estadísticas.
- Soporte multiidioma.
- Migración a WhatsApp Business API.
- Recordatorios automáticos de citas por Telegram.

---

**Proyecto desarrollado por Guillermo Esteban Moreno** — disponible para automatizaciones
a medida y bots de atención al cliente.
