import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.packages.enums import TaskPriority, TASK_PRIORITY_MAP
from app.services.publisher import TaskPublisher


class TestTaskPublisher:
    @pytest.mark.asyncio
    async def test_publish_task_calls_correct_routing_key(self):
        mock_exchange = AsyncMock()
        mock_channel = AsyncMock()
        mock_channel.default_exchange = mock_exchange
        mock_connection = AsyncMock()
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.publisher.aio_pika.connect_robust", return_value=mock_connection), \
             patch("app.services.publisher.aio_pika.Message", MagicMock()):
            publisher = TaskPublisher("amqp://localhost/")
            await publisher.publish_task("test-id", TaskPriority.HIGH)
            mock_exchange.publish.assert_awaited_once()
            assert mock_exchange.publish.call_args.kwargs["routing_key"] == "tasks"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("priority,expected", [
        (TaskPriority.LOW, TASK_PRIORITY_MAP[TaskPriority.LOW]),
        (TaskPriority.MEDIUM, TASK_PRIORITY_MAP[TaskPriority.MEDIUM]),
        (TaskPriority.HIGH, TASK_PRIORITY_MAP[TaskPriority.HIGH]),
    ])
    async def test_publish_task_priority_mapping(self, priority, expected):
        mock_message_cls = MagicMock()
        mock_exchange = AsyncMock()
        mock_channel = AsyncMock()
        mock_channel.default_exchange = mock_exchange
        mock_connection = AsyncMock()
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.publisher.aio_pika.connect_robust", return_value=mock_connection), \
             patch("app.services.publisher.aio_pika.Message", mock_message_cls):
            await TaskPublisher("amqp://localhost/").publish_task("nomer_testovoy_zandacchi_:)", priority)
            kwargs = mock_message_cls.call_args.kwargs
            assert kwargs["priority"] == expected
            assert kwargs["body"] == b"nomer_testovoy_zandacchi_:)"
