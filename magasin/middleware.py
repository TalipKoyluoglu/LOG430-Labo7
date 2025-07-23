import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from prometheus_client import Counter, Histogram, Gauge

# Configuration du logger
logger = logging.getLogger("magasin")

# Métriques Prometheus personnalisées
REQUEST_COUNT = Counter(
    "django_http_requests_total",
    "Total des requêtes HTTP",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "django_http_request_duration_seconds",
    "Durée des requêtes HTTP",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge("django_http_requests_active", "Requêtes actives", ["method"])


class ObservabilityMiddleware(MiddlewareMixin):
    """
    Middleware pour l'observabilité : logging structuré et métriques Prometheus
    """

    def process_request(self, request):
        # Marquer le début de la requête
        request.start_time = time.time()

        # Incrémenter le compteur de requêtes actives
        ACTIVE_REQUESTS.labels(method=request.method).inc()

        # Log de début de requête
        logger.info(
            "Début de requête",
            extra={
                "request_id": getattr(request, "id", "unknown"),
                "method": request.method,
                "path": request.path,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "ip": self._get_client_ip(request),
                "user": (
                    str(request.user) if request.user.is_authenticated else "anonymous"
                ),
            },
        )

    def process_response(self, request, response):
        # Calculer la durée de la requête
        duration = time.time() - getattr(request, "start_time", time.time())

        # Décrémenter le compteur de requêtes actives
        ACTIVE_REQUESTS.labels(method=request.method).dec()

        # Enregistrer les métriques Prometheus
        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.path, status=response.status_code
        ).inc()

        REQUEST_DURATION.labels(method=request.method, endpoint=request.path).observe(
            duration
        )

        # Log de fin de requête
        logger.info(
            "Fin de requête",
            extra={
                "request_id": getattr(request, "id", "unknown"),
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "content_length": (
                    len(response.content) if hasattr(response, "content") else 0
                ),
                "user": (
                    str(request.user) if request.user.is_authenticated else "anonymous"
                ),
            },
        )

        return response

    def process_exception(self, request, exception):
        # Log des erreurs
        logger.error(
            "Exception dans la requête",
            extra={
                "request_id": getattr(request, "id", "unknown"),
                "method": request.method,
                "path": request.path,
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "user": (
                    str(request.user) if request.user.is_authenticated else "anonymous"
                ),
            },
            exc_info=True,
        )

        # Décrémenter le compteur de requêtes actives en cas d'erreur
        ACTIVE_REQUESTS.labels(method=request.method).dec()

    def _get_client_ip(self, request):
        """Extraire l'IP du client"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
