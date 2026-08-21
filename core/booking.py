"""Disponibilidad de reservas para las instalaciones.

QUE HACE ESTE ARCHIVO
    Responde dos preguntas:
      1. "Que dias y horas puedo ofrecerle al cliente?"  -> open_days()
      2. "Lo que el cliente eligio, sigue siendo valido?" -> validate_selection()

QUE **NO** HACE
    No toca la base de datos. Ni una consulta.

    Por que: si este archivo abriera la base de datos, para probarlo habria
    que levantar una base de datos. Al recibir los cupos ocupados como un
    diccionario normal, se puede probar toda la logica de calendario con
    datos inventados, en milisegundos, sin infraestructura.

    Quien si consulta la base es db/bookings.py, que arma ese diccionario.

EL DICCIONARIO `taken`
    Es el mapa de lo que ya esta ocupado. Se ve asi:

        {
            "2026-08-21": {1: 1, 3: 1},   # el dia 21 tiene los slots 1 y 3 ocupados
            "2026-08-24": {5: 1},         # el dia 24 solo el slot 5
        }

    fecha (texto ISO) -> { numero de franja -> cuantas reservas hay }
    Un dia que no aparece en el diccionario esta completamente libre.
"""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from core.config import settings


# ===========================================================================
# CONFIGURACION
#
# Todo lo que define "como opera el negocio" vive aqui arriba. Si manana
# cambian los horarios o crece el equipo, se toca esta seccion y nada mas.
# ===========================================================================

# Zona horaria del negocio. Importa mas de lo que parece: el servidor de
# Railway corre en UTC, asi que si comparamos horas sin zona, el calculo de
# "faltan 24 horas" saldria corrido varias horas.
#
# ZoneInfo tambien resuelve solo el cambio de horario de verano. No hay que
# hacer nada especial: en marzo y noviembre el offset cambia por su cuenta.
TZ = ZoneInfo("America/New_York")

# Las franjas de trabajo del dia.
#   numero de franja -> (hora de inicio, hora de fin)
#
# Se usan franjas de dos horas en vez de horas exactas porque en oficios de
# campo el trafico y los imprevistos hacen imposible cumplir un "9:30 en
# punto". Una ventana es lo que usa la industria y evita llegar tarde.
#
# Para alargar la jornada, se agregan filas aqui. Todo lo demas
# (las etiquetas, la validacion, el conteo de cupos) se ajusta solo.
SLOTS = {
    1: (time(8), time(10)),
    2: (time(10), time(12)),
    3: (time(12), time(14)),
    4: (time(14), time(16)),
    5: (time(16), time(18)),
}

# Cuantas instalaciones caben AL MISMO TIEMPO en una franja.
#
# Esta es la perilla de crecimiento. El dia no se hace mas largo cuando
# contratas gente: lo que crece es cuantos trabajos van en paralelo.
#   CREWS = 1  ->  5 instalaciones al dia  (un equipo)
#   CREWS = 2  -> 10 instalaciones al dia  (dos equipos)
#   CREWS = 4  -> 20 instalaciones al dia
CREWS = 1

# Dias que se trabaja. Python numera los dias asi:
#   lunes=0, martes=1, miercoles=2, jueves=3, viernes=4, sabado=5, domingo=6
# Este conjunto es lunes a sabado; el domingo queda fuera.
WORK_WEEKDAYS = {0, 1, 2, 3, 4, 5}

# Cuanto tiempo minimo tiene que haber entre "ahora" y el inicio del trabajo.
# Sin esto, alguien podria reservar a las 7:50 AM la franja de las 8:00 AM.
LEAD_HOURS = 24

# Hasta cuantos dias hacia adelante se muestra el calendario. Mas de un mes
# llena la agenda de reservas que terminan cancelandose.
HORIZON_DAYS = 30

# Cuanto tiempo una reserva sin pagar sigue reteniendo su cupo.
#
# Cuando alguien llega al checkout de Stripe se crea la reserva en estado
# "pending" y su cupo queda apartado. Si abandona el pago, no hay que
# liberar nada a mano: pasados estos minutos deja de contarse y el hueco
# vuelve a ofrecerse.
#
# Esta constante no se usa en este archivo. Vive aqui porque es una regla
# del negocio, no de la base de datos. La consume db/bookings.py.
HOLD_MINUTES = 30

# Feriados y dias libres. Es un array de fechas "YYYY-MM-DD".
# Se lee en cada peticion, asi que editarlo tiene efecto sin tocar codigo.
BLOCKED_FILE = Path("data/blocked_dates.json")

# Deposito que se cobra al reservar. Igual en los tres planes: un solo
# numero es mas facil de comunicar ("$50 to book") que un porcentaje que
# cambia por plan. Se descuenta del total; el resto se paga al terminar.
#
# El valor vive en .env (BOOKING_DEPOSIT), no aqui: un "2" de prueba llego
# a produccion dentro de un commit y se quedo publicado. Desde .env se
# cambia sin tocar codigo.
DEPOSIT = settings.booking_deposit


class BookingUnavailable(Exception):
    """La franja que pidio el cliente ya no se puede reservar.

    Se define una excepcion propia (en vez de usar ValueError) para que la
    ruta pueda distinguir "el cliente eligio algo invalido" de cualquier
    otro error. El texto del mensaje se le muestra tal cual al cliente.
    """


# ===========================================================================
# FUNCIONES
# ===========================================================================

def slot_label(slot: int) -> str:
    """Convierte el numero de franja en texto legible.

        slot_label(1)  ->  "8:00 AM - 10:00 AM"

    El `%-I` (con guion) quita el cero de adelante: "8:00" en vez de "08:00".
    Ese formato funciona en Linux y macOS. En Windows seria "%#I" — no es
    problema aqui porque el servidor corre Linux.
    """
    start, end = SLOTS[slot]
    return f"{start:%-I:%M %p} - {end:%-I:%M %p}"


def open_days(taken: dict, ref: datetime | None = None) -> list[dict]:
    """Devuelve los dias que tienen al menos una franja libre.

    Args:
        taken: cupos ya ocupados (ver el formato arriba en el docstring).
        ref:   que momento se considera "ahora". Normalmente se deja vacio
               y usa el reloj real. Sirve para las pruebas: permite simular
               cualquier fecha sin cambiar el reloj de la maquina.

               OJO: si se pasa un valor, tiene que traer zona horaria. Un
               datetime sin zona hace que la resta de mas abajo falle con
               TypeError.

    Returns:
        Una lista lista para pintar en el HTML:

            [
              {
                "date":  "2026-08-21",
                "label": "Fri, Aug 21",
                "slots": [{"n": 1, "label": "8:00 AM - 10:00 AM"}, ...]
              },
              ...
            ]

        Solo aparecen los dias con algo disponible. Un dia lleno, un domingo
        o un feriado simplemente no salen en la lista.
    """
    ref = ref or datetime.now(TZ)

    # Cargar los feriados. Si el archivo tiene una fecha mal escrita
    # (por ejemplo "2026-13-45"), fromisoformat lanza ValueError y la pagina
    # falla. Eso es intencional: es preferible que reviente ahora, mientras
    # se prueba, a que la fecha se ignore en silencio y se termine tomando
    # una reserva el 25 de diciembre.
    blocked = {date.fromisoformat(d) for d in json.loads(BLOCKED_FILE.read_text())}

    days = []

    # Recorrer un dia a la vez desde hoy hasta el horizonte.
    # El "+ 1" hace que el ultimo dia tambien entre (range excluye el final).
    for i in range(HORIZON_DAYS + 1):
        day = ref.date() + timedelta(days=i)

        # Filtro 1: dias que no se trabajan. `continue` salta al siguiente
        # dia del bucle sin evaluar nada mas.
        if day.weekday() not in WORK_WEEKDAYS or day in blocked:
            continue

        # Cupos ya ocupados de ESTE dia. Si el dia no esta en el diccionario,
        # .get devuelve {} — o sea, dia completamente libre.
        used = taken.get(day.isoformat(), {})

        # Filtro 2 y 3: recorrer las franjas y quedarse con las que pasan
        # las dos condiciones.
        free = [
            n
            for n, (start, _) in SLOTS.items()
            # (a) Todavia hay cupo: los ocupados no llegan al maximo.
            if used.get(n, 0) < CREWS
            # (b) Falta suficiente anticipacion.
            #     datetime.combine junta la fecha del dia con la hora de
            #     inicio de la franja y le pone la zona horaria. Restar dos
            #     datetimes da un timedelta, que se compara directo contra
            #     las 24 horas.
            #     Es ">=", asi que exactamente 24 horas si califica.
            and datetime.combine(day, start, TZ) - ref >= timedelta(hours=LEAD_HOURS)
        ]

        # Si quedo alguna franja libre, el dia entra en la respuesta.
        if free:
            days.append({
                "date": day.isoformat(),                  # para el value del <select>
                "label": f"{day:%a, %b %-d}",             # "Fri, Aug 21" para el cliente
                "slots": [{"n": n, "label": slot_label(n)} for n in free],
            })

    return days


def validate_selection(day: str, slot: int, taken: dict, ref=None) -> tuple[date, int]:
    """Revisa que lo que llego del formulario siga siendo reservable.

    POR QUE EXISTE ESTA FUNCION
        Nunca se confia en lo que manda el navegador. Tres cosas pueden
        pasar entre que se pinta el calendario y llega el POST:

          1. El cliente dejo la pagina abierta media hora y el cupo se lleno.
          2. Otro cliente reservo esa misma franja hace 10 segundos.
          3. Alguien edito el POST a mano para forzar un domingo.

        Se llama SIEMPRE antes de crear la sesion de pago de Stripe. Cobrar
        primero y descubrir despues que la fecha no servia significa tener
        que devolver dinero.

    COMO ESTA HECHA
        No repite las reglas (dia habil, feriado, horizonte, anticipacion,
        cupo). En vez de eso le pregunta a open_days: "esta esta seleccion
        entre las opciones que yo mismo ofreci?".

        Eso importa: si las reglas estuvieran escritas dos veces, tarde o
        temprano se desincronizan — se cambia el horizonte en un lado, se
        olvida el otro, y el calendario ofrece un dia que la validacion
        rechaza. Con una sola fuente de verdad eso no puede pasar.

    Args:
        day:   fecha en texto ISO, tal como vino del formulario ("2026-08-21").
        slot:  numero de franja.
        taken: cupos ocupados, recien consultados a la base de datos.
        ref:   igual que en open_days, solo para pruebas.

    Returns:
        La tupla (date, slot) ya convertida a tipos de Python, lista para
        guardar en la base.

    Raises:
        BookingUnavailable: si la seleccion no esta disponible.
    """
    for d in open_days(taken, ref):
        if d["date"] == day and any(s["n"] == slot for s in d["slots"]):
            return date.fromisoformat(day), slot

    # Un solo mensaje para todos los casos de rechazo.
    #
    # Se podria decir exactamente que fallo ("eso es domingo", "faltan menos
    # de 24 horas"), pero no aporta: la interfaz solo ofrece opciones
    # validas. Quien llega hasta aqui o tiene la pagina vieja abierta — y
    # para el, "ya no esta disponible" es literalmente la verdad — o esta
    # manipulando el POST, y a ese no se le deben explicaciones.
    raise BookingUnavailable("That time is no longer available. Please pick another one.")