from typing import Dict, Any
from base_datos.modelos import Conversacion
import json

class GestorEstados:
    """
    Clase que se encarga de gestionar los estados de los usuarios.

    El estado de un usuario es un diccionario que contiene los siguientes campos:
    - "paso": El paso actual en el flujo de conversación.
    - "nombre": El nombre del usuario.
    - "rol": El rol del usuario.
    - "ha_pagado": Un booleano que indica si el usuario ha pagado.
    """
    def __init__(self):
        """
        Constructor de la clase.

        Inicializa el diccionario que se utiliza para almacenar los estados de los
        usuarios.
        """
        self.estados_usuario: Dict[str, Dict[str, Any]] = {}

    def obtener_estado_inicial(self, remitente: str) -> Dict[str, Any]:
        """
        Crea un estado inicial para el usuario.

        Args:
            remitente (str): Identificador único del usuario.

        Returns:
            Dict[str, Any]: Estado inicial del usuario.
        """
        return {
            "paso": "inicio",
            "nombre": None,
            "rol": None,
            "acceso_tecnico": False,
            "remitente": remitente,
            "historial_conversacion": []
        }

    import json

    def obtener_estado(self, remitente, db):
        estado_obj = db.query(Conversacion).filter_by(remitente=remitente).first()
        if not estado_obj:
            estado_obj = Conversacion(
                remitente=remitente,
                paso="inicio",
                nombre=None,
                rol=None,
                acceso_tecnico=False,
                historial_conversacion=json.dumps([]),  # Guardar como JSON
                mensaje="",
                respuesta=""
            )
            db.add(estado_obj)
            db.commit()

        # Convertir historial_conversacion de texto a lista
        estado = {
            "paso": estado_obj.paso,
            "nombre": estado_obj.nombre,
            "rol": estado_obj.rol,
            "acceso_tecnico": estado_obj.acceso_tecnico,
            "remitente": estado_obj.remitente,
            "historial_conversacion": json.loads(estado_obj.historial_conversacion or "[]")
        }
        return estado


    def actualizar_estado(self, remitente, estado, db):
        estado_obj = db.query(Conversacion).filter_by(remitente=remitente).first()
        if not estado_obj:
            estado_obj = Conversacion(remitente=remitente)

        estado_obj.paso = estado["paso"]
        estado_obj.nombre = estado["nombre"]
        estado_obj.rol = estado["rol"]
        estado_obj.acceso_tecnico = estado["acceso_tecnico"]
        estado_obj.historial_conversacion = json.dumps(estado["historial_conversacion"])  # Guardar como JSON

        db.add(estado_obj)
        db.commit()



    def reanudar_estado(self, remitente: str) -> str:
        """
        Reanuda la conversación desde el último estado guardado.

        Args:
            remitente (str): Identificador único del usuario.

        Returns:
            str: Mensaje para reanudar la conversación.
        """
        estado = self.obtener_estado(remitente)
        if estado["paso"] == "inicio":
            return "¡Hola de nuevo! ¿Cómo puedo ayudarte?"
        return f"Continuemos desde donde lo dejamos, {estado['paso']}."

gestor_estados = GestorEstados()
