import os

from celery import Celery, Task
from langchain import hub

from celery_app.celery_config import config
from service import create_politician_json

prompt = hub.pull("kaliani/generate_politicans")

celery_app = Celery(__name__)
celery_app.config_from_object(config)
celery_app.conf.broker_url = os.getenv("CELERY_BROKER_URL")
celery_app.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

celery_app.log.setup(loglevel="DEBUG")
celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.broker_transport_options = {"visibility_timeout": 6 * 60 * 60}
celery_app.autodiscover_tasks()


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)
    max_retries = 5
    default_retry_delay = 5
    retry_backoff = False
    retry_backoff_max = 700
    retry_jitter = False


@celery_app.task
def create_politician(name: str, wikidata_id: str):
    dossier = create_politician_json(name, wikidata_id, prompt.template)
    return dossier if dossier else {"error": "Failed to create and index politician dossier"}
