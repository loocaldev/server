import analytics

def track_event(user_id, event_name, properties=None):
    """
    Envía un evento a Segment.
    :param user_id: ID del usuario asociado al evento.
    :param event_name: Nombre del evento.
    :param properties: Propiedades del evento.
    """
    analytics.track(user_id, event_name, properties or {})
