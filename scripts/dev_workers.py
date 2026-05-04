#!/usr/bin/env python3
"""
dev_workers.py
==============
Lokale Job-Worker für die Self-Hosted Demo (docker-compose).

Registriert für jeden Send-/Service-Task im urlaubsantrag-BPMN einen Worker,
der den passenden Job verarbeitet — Send Tasks veröffentlichen die zugehörige
Nachricht, Service Tasks loggen nur und schliessen den Job ab. Damit läuft
der gesamte Prozess (Mitarbeiter -> Vorgesetzter -> HR -> Mitarbeiter) ohne
manuelle Eingriffe in Operate durch.

Voraussetzungen:
    pip install pyzeebe

Start:
    python scripts/dev_workers.py
"""

import asyncio
import logging
from typing import Any

from pyzeebe import ZeebeWorker, create_insecure_channel

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-5s  %(message)s")
log = logging.getLogger("workers")


async def main() -> None:
    channel = create_insecure_channel(grpc_address="localhost:26500")
    worker = ZeebeWorker(channel)

    @worker.task(task_type="send-antrag")
    async def send_antrag(antragId: str = "A000", **vars: Any) -> dict:
        log.info("send-antrag -> publish msg_urlaubsantrag (antragId=%s)", antragId)
        await worker.zeebe_adapter.publish_message(
            name="msg_urlaubsantrag",
            correlation_key=antragId,
            variables={"antragId": antragId, **vars},
            time_to_live_in_milliseconds=60_000,
        )
        return {}

    @worker.task(task_type="approve-request")
    async def approve_request(**vars: Any) -> dict:
        log.info("approve-request -> approved=true")
        return {"approved": True}

    @worker.task(task_type="reject-request")
    async def reject_request(**vars: Any) -> dict:
        log.info("reject-request -> approved=false")
        return {"approved": False}

    @worker.task(task_type="send-decision")
    async def send_decision(antragId: str = "A000", approved: bool = True, **vars: Any) -> dict:
        log.info("send-decision -> publish msg_entscheid (antragId=%s, approved=%s)", antragId, approved)
        await worker.zeebe_adapter.publish_message(
            name="msg_entscheid",
            correlation_key=antragId,
            variables={"approved": approved},
            time_to_live_in_milliseconds=60_000,
        )
        return {}

    @worker.task(task_type="notify-hr")
    async def notify_hr(antragId: str = "A000", approved: bool = True, **vars: Any) -> dict:
        log.info("notify-hr -> publish msg_hr_benachrichtigung (antragId=%s)", antragId)
        await worker.zeebe_adapter.publish_message(
            name="msg_hr_benachrichtigung",
            correlation_key="",
            variables={"antragId": antragId, "approved": approved},
            time_to_live_in_milliseconds=60_000,
        )
        return {}

    @worker.task(task_type="update-db")
    async def update_db(antragId: str = "A000", **vars: Any) -> dict:
        log.info("update-db -> Urlaubstage für %s eingetragen (Demo)", antragId)
        return {}

    @worker.task(task_type="log-rejection")
    async def log_rejection(antragId: str = "A000", **vars: Any) -> dict:
        log.info("log-rejection -> Ablehnung für %s protokolliert (Demo)", antragId)
        return {}

    @worker.task(task_type="send-confirmation")
    async def send_confirmation(antragId: str = "A000", **vars: Any) -> dict:
        log.info("send-confirmation -> publish msg_bestaetigung (antragId=%s)", antragId)
        await worker.zeebe_adapter.publish_message(
            name="msg_bestaetigung",
            correlation_key=antragId,
            variables={"antragId": antragId},
            time_to_live_in_milliseconds=60_000,
        )
        return {}

    log.info("Worker bereit — verbunden mit zeebe @ localhost:26500")
    await worker.work()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Worker beendet")
