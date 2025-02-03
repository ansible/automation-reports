# import dramatiq
# from dramatiq.brokers.redis import RedisBroker
# from typing import Any, cast
# from backend.apps.clusters.connector import ApiConnector
# from backend.apps.clusters.models import Cluster
# from dramatiq import Message, Middleware, results
#
#
#
#
# @dramatiq.actor(queue_name="automation-reports-sync-data", priority=0)
# def add(x, y):
#     add.logger.debug(f"x + y = {x + y}")
#     print("Fetching external data...")
#     # clusters = Cluster.objects.all()
#     # for cluster in clusters:
#     #     connector = ApiConnector(cluster=cluster)
#     #     connector.sync()
#     return {"success": True}
#
# class NoLazyQueueDeclareRedisBroker(RedisBroker):
#
#     def __init__(self, *, result_backend=None, **kwargs) -> None:
#         self.disable_queue_declaration = False
#         super().__init__(**kwargs)
#
#     def enqueue(self, message: Message[Any], *, delay: int | None = None) -> Message[Any]:
#         self.disable_queue_declaration = True
#         result = super().enqueue(message, delay=delay)
#         self.disable_queue_declaration = False
#         return cast(Message[Any], result)
#
#     def declare_queue(self, queue_name: str) -> None:
#         if self.disable_queue_declaration:
#             return
#         super().declare_queue(queue_name)
