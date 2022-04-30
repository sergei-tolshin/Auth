import functools
from typing import Optional

import flask
from opentelemetry import trace as ot_trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter)


class Tracer:
    def __init__(self,
                 app: Optional[flask.Flask] = None,
                 config_prefix='TRACER',
                 console=True,
                 request_id=True,
                 **kwargs):
        self.config_prefix = config_prefix
        self.console = console
        self.request_id = request_id

        if app is not None:
            self.init_app(app)

    def init_app(self, app: flask.Flask):
        self.configure_tracer(app.config)
        FlaskInstrumentor().instrument_app(app)

        if not hasattr(app, 'extensions'):
            app.extensions = {}

        if self.request_id:
            app.before_request(self._get_request_id)

        app.extensions[self.config_prefix.lower()] = self

    def _get_request_id(self):
        request_id = flask.request.headers.get('X-Request-Id')

        if not request_id:
            raise RuntimeError('request id is required')

        current_span = ot_trace.get_current_span()
        current_span.set_attribute('http.request_id', request_id)

    def configure_tracer(self, config) -> None:
        ot_trace.set_tracer_provider(TracerProvider(
            resource=Resource.create(
                {SERVICE_NAME: config.get(
                    '{0}_SERVICE_NAME'.format(self.config_prefix), None)})
        ))
        ot_trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(
                JaegerExporter(
                    agent_host_name=config.get(
                        '{0}_JAEGER_HOST'.format(self.config_prefix), None),
                    agent_port=config.get(
                        '{0}_JAEGER_PORT'.format(self.config_prefix), None),
                )
            )
        )
        # Чтобы видеть трейсы в консоли
        if self.console:
            ot_trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter()))


def trace(func):
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        tracer = ot_trace.get_tracer(func.__module__)
        with tracer.start_as_current_span(func.__name__):
            return func(*args, **kwargs)
    return decorated
