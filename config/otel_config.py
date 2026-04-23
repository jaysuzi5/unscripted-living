import logging
import os


def init_otel_logging():
    try:
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

        log_level_name = os.environ.get('OTEL_LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_name, logging.INFO)

        logger_provider = LoggerProvider()
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(OTLPLogExporter())
        )
        handler = logging.getLogger('unscripted')
        handler.setLevel(log_level)
    except Exception:
        pass
