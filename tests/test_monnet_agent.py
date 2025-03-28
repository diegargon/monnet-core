import unittest
from unittest.mock import patch, MagicMock, call
import sys
import time
import signal
from datetime import datetime
import psutil
import argparse

# Mockear módulos externos para las pruebas
sys.modules['info_linux'] = MagicMock()
sys.modules['tasks'] = MagicMock()
sys.modules['monnet_agent.agent_globals'] = MagicMock()
sys.modules['datastore'] = MagicMock()
sys.modules['event_processor'] = MagicMock()
sys.modules['constants'] = MagicMock(LogLevel=MagicMock(), EventType=MagicMock())
sys.modules['shared.mconfig'] = MagicMock()
sys.modules['shared.logger'] = MagicMock()
sys.modules['monnet_agent.notifications'] = MagicMock()

# Importar el módulo a testear después de configurar los mocks
from monnet_agent.monnet_agent_linux import run

class TestMonnetAgentLinux(unittest.TestCase):

    def setUp(self):
        self.mock_config = {
            "token": "test_token",
            "default_interval": 10,
            "interval": 10,
            "CONFIG_FILE_PATH": "/fake/path/config.json"
        }

    @patch('monnet_agent.monnet_agent_linux.agent_globals', MagicMock())
    @patch('monnet_agent.monnet_agent_linux.load_config')
    @patch('monnet_agent.monnet_agent_linux.validate_agent_config')
    @patch('monnet_agent.monnet_agent_linux.Datastore')
    @patch('monnet_agent.monnet_agent_linux.EventProcessor')
    @patch('monnet_agent.monnet_agent_linux.psutil.cpu_times')
    @patch('monnet_agent.monnet_agent_linux.send_notification')
    @patch('monnet_agent.monnet_agent_linux.send_request')
    @patch('monnet_agent.monnet_agent_linux.validate_response')
    @patch('monnet_agent.monnet_agent_linux.handle_signal')
    @patch('monnet_agent.monnet_agent_linux.time.sleep')

    def test_run_normal_operation(
        self, mock_sleep, mock_handle_signal, mock_validate_response,
        mock_send_request, mock_send_notification, mock_cpu_times,
        mock_event_processor, mock_datastore, mock_validate_config,
        mock_load_config
    ):
        # Configurar mocks
        mock_load_config.return_value = self.mock_config

        # Mockear Datastore
        mock_datastore_instance = MagicMock()
        mock_datastore.return_value = mock_datastore_instance
        mock_datastore_instance.get_data.side_effect = lambda x: None

        # Mockear EventProcessor
        mock_event_processor_instance = MagicMock()
        mock_event_processor.return_value = mock_event_processor_instance
        mock_event_processor_instance.process_changes.return_value = []

        # Mockear CPU times
        mock_cpu_times.return_value = (1, 2, 3, 4, 5)

        # Mockear respuesta del servidor
        mock_response = {
            "data": {},
            "refresh": 10,
            "token": "test_token"
        }
        mock_validate_response.return_value = mock_response
        mock_send_request.return_value = mock_response

        # Mockear info_linux
        mock_info_linux = MagicMock()
        mock_info_linux.get_cpus.return_value = 4
        mock_info_linux.get_uptime.return_value = 12345
        mock_info_linux.get_load_avg.return_value = {'load1': 0.5}
        mock_info_linux.get_memory_info.return_value = {'mem_total': 1000}
        mock_info_linux.get_disks_info.return_value = {'disk_total': 2000}
        mock_info_linux.get_iowait.return_value = 1.23

        # Inyectar nuestro mock
        sys.modules['info_linux'] = mock_info_linux

        # Mockear tasks
        mock_tasks = MagicMock()
        sys.modules['tasks'] = mock_tasks

        # Simular una sola iteración del bucle
        def stop_loop(*args, **kwargs):
            import monnet_agent.monnet_agent_linux
            monnet_agent.monnet_agent_linux.running = False
        mock_sleep.side_effect = stop_loop

        # Ejecutar la función
        run()

        # Verificaciones
        mock_load_config.assert_called_once_with(self.mock_config["CONFIG_FILE_PATH"])
        mock_validate_config.assert_called_once_with(self.mock_config)

        # Verificar que se envió la notificación de inicio
        starting_call = call(self.mock_config, 'starting', {
            'msg': unittest.mock.ANY,
            'ncpu': 4,
            'uptime': 12345,
            'log_level': unittest.mock.ANY,
            'event_type': unittest.mock.ANY
        })
        self.assertIn(starting_call, mock_send_notification.call_args_list)

        # Verificar que se llamó a las funciones de tasks
        mock_tasks.check_listen_ports.assert_called_once_with(
            self.mock_config, mock_datastore_instance, mock_send_notification, startup=1
        )
        mock_tasks.send_stats.assert_called_once_with(
            self.mock_config, mock_datastore_instance, mock_send_notification
        )

        # Verificar que se procesaron los cambios
        mock_event_processor_instance.process_changes.assert_called()

        # Verificar que se envió el ping
        mock_send_request.assert_called_once_with(
            self.mock_config, cmd="ping", data=unittest.mock.ANY
        )

    @patch('monnet_agent.monnet_agent_linux.load_config')
    def test_run_with_invalid_config(self, mock_load_config):
        mock_load_config.return_value = None

        # Mockear logger para verificar el mensaje de error
        mock_logger = MagicMock()
        sys.modules['shared.logger'] = mock_logger

        run()

        mock_logger.log.assert_called_with("Cant load config. Finishing", "err")

    @patch('monnet_agent.monnet_agent_linux.load_config')
    @patch('monnet_agent.monnet_agent_linux.validate_agent_config')
    def test_run_with_config_validation_error(self, mock_validate_config, mock_load_config):
        mock_load_config.return_value = self.mock_config
        mock_validate_config.side_effect = ValueError("Invalid config")

        # Mockear logger
        mock_logger = MagicMock()
        sys.modules['shared.logger'] = mock_logger

        run()

        mock_logger.log.assert_called_with("Invalid config", "err")

    @patch('monnet_agent.monnet_agent_linux.argparse.ArgumentParser')
    def test_main_no_daemon(self, mock_arg_parser):
        mock_args = MagicMock()
        mock_args.no_daemon = True
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_arg_parser.return_value = mock_parser

        # Mockear la función run
        with patch('monnet_agent.monnet_agent_linux.run') as mock_run:
            # Necesitamos importar el módulo principal para probar __main__
            with patch('monnet_agent.monnet_agent_linux.__name__', '__main__'):
                import monnet_agent.monnet_agent_linux
                # Simular la ejecución del módulo como script
                monnet_agent.monnet_agent_linux.run = mock_run
                monnet_agent.monnet_agent_linux.main()

        mock_run.assert_called_once()

    @patch('monnet_agent.monnet_agent_linux.daemon.DaemonContext')
    @patch('monnet_agent.monnet_agent_linux.argparse.ArgumentParser')
    def test_main_with_daemon(self, mock_arg_parser, mock_daemon_context):
        mock_args = MagicMock()
        mock_args.no_daemon = False
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_arg_parser.return_value = mock_parser

        mock_context = MagicMock()
        mock_daemon_context.return_value = mock_context
        mock_context.__enter__.return_value = None

        # Mockear la función run
        with patch('monnet_agent.monnet_agent_linux.run') as mock_run:
            # Necesitamos importar el módulo principal para probar __main__
            with patch('monnet_agent.monnet_agent_linux.__name__', '__main__'):
                import monnet_agent.monnet_agent_linux
                # Simular la ejecución del módulo como script
                monnet_agent.monnet_agent_linux.run = mock_run
                monnet_agent.monnet_agent_linux.main()

        mock_run.assert_called_once()
        mock_daemon_context.assert_called_once()

if __name__ == '__main__':
    unittest.main()