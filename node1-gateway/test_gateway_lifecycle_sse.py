import asyncio
import json
from unittest.mock import AsyncMock

import main


def test_lifespan_initializes_store_and_stops_after_exception(monkeypatch):
    calls = []
    monkeypatch.setattr(main.task_store, 'init_db', lambda: calls.append('init'), raising=False)
    start = AsyncMock()
    stop = AsyncMock()
    monkeypatch.setattr(main.mqtt_service, 'start', start)
    monkeypatch.setattr(main.mqtt_service, 'stop', stop)
    monkeypatch.setattr(main.mqtt_service, 'set_broadcast_callback', lambda cb: None)

    async def exercise():
        try:
            async with main.lifespan(main.app):
                assert calls == ['init']
                raise RuntimeError('test shutdown')
        except RuntimeError as exc:
            assert str(exc) == 'test shutdown'
        else:
            raise AssertionError('lifespan suppressed the exception')

    asyncio.run(exercise())
    start.assert_awaited_once()
    stop.assert_awaited_once()


def test_initial_sse_event_has_real_newlines_and_cleans_up(monkeypatch):
    queues = []
    monkeypatch.setattr(main, 'sse_clients_list', queues)
    monkeypatch.setattr(main.mqtt_service, 'active_nodes', {'worker-1': {'info': {'status': 'online'}}})

    class Request:
        async def is_disconnected(self):
            return False

    async def exercise():
        response = await main.sse_stream(Request())
        iterator = response.body_iterator
        try:
            frame = await anext(iterator)
            assert frame.startswith('event: node_update\ndata: ')
            assert frame.endswith('\n\n')
            assert json.loads(frame.split('data: ', 1)[1]) == {'worker-1': {'status': 'online'}}
        finally:
            await iterator.aclose()
        assert queues == []

    asyncio.run(exercise())
