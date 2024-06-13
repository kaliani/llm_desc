config = {
    "database_engine_options": {"echo": False},
    "worker_concurrency": 4,
    "task_acks_late": True,
    "accept_content": ["json", "application/x-python-serialize"],
    "task_serializer": "json",
    "result_serializer": "json",
    "event_serializer": "json",
    "result_expires": 7200,
    "task_compression": "gzip",
    "result_compression": "gzip",
    "redis_max_connections": 2,
    "broker_transport_options": {"max_connections": 2},
    "broker_pool_limit": 2,
}
