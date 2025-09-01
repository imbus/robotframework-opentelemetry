import os
from typing import get_type_hints, get_args

from robot.running import TestCase as RunningTestCase
from robot.result import TestCase as ResultTestCase
from robot.running import TestSuite as RunningTestSuite
from robot.result import TestSuite as ResultTestSuite
from robot.result.model import StatusMixin

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.metrics._internal.instrument import _ProxyCounter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import _Span
from opentelemetry.context.context import Context

OTEL_LISTENER_SPAN_NAME_DEFAULT = "RobotListener"
OTEL_LISTENER_STATUS_COUNTER_NAME_DEFAULT = "Test Statistics"


class OpenTelemetryListener:

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, url: str = None, listener_span_name: str=OTEL_LISTENER_SPAN_NAME_DEFAULT, module_name: str=None):
        self.url = url

        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(__name__ if module_name is None else module_name)

        # Set up OTLP exporter (using HTTP protocol)
        self.otlp_exporter = OTLPSpanExporter(endpoint=None if url is None else f"{self.url}/v1/traces")

        match os.environ.get("OTEL_LISTENER_PROCESSOR"):
            case "batch":
                self.span_processor = BatchSpanProcessor(self.otlp_exporter)
            case "simple" | _:
                self.span_processor = SimpleSpanProcessor(self.otlp_exporter)
        trace.get_tracer_provider().add_span_processor(self.span_processor)

        self.span_context: dict[str, tuple[_Span, Context]] = {}

        listener_span = self.tracer.start_span(name=os.environ.get("OTEL_LISTENER_SPAN_NAME", listener_span_name), attributes={"type": "LISTENER"})
        self.span_context[None] = listener_span, trace.set_span_in_context(listener_span)


        self.metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=None if url is None else f"{self.url}/v1/metrics"))
        self.metric_provider = MeterProvider(metric_readers=[self.metric_reader])

        self.test_meter = self.metric_provider.get_meter(os.environ.get("OTEL_LISTENER_STATUS_COUNTER_NAME", OTEL_LISTENER_STATUS_COUNTER_NAME_DEFAULT)) # attributes?
        self.test_counter: dict[str, _ProxyCounter] = {}
        for status in get_args(get_type_hints(StatusMixin)["status"]):
            # I have not found any specification that would not allow whitespace but the SDK throws an exception
            self.test_counter[status] = self.test_meter.create_counter(status.replace(" ", "_"), "test")
        

    def start_suite(self, suite: RunningTestSuite, result: ResultTestSuite):
        suite_span = self.tracer.start_span(suite.name, self.span_context[suite.parent.id if suite.parent is not None else None][1],
                                            attributes={"source": str(suite.source), "start_time": result.start_time.isoformat(), "type": suite.type})
        self.span_context[suite.id] = suite_span, trace.set_span_in_context(suite_span)


    def start_test(self, test: RunningTestCase, result: ResultTestCase):
        self.span_context[test.id] = self.tracer.start_span(test.name, self.span_context[test.parent.id if test.parent is not None else None][1],
                                                            attributes={"source": str(test.source), "start_time": result.start_time.isoformat(), "type": test.type,
                                                                        "tags": test.tags}), None


    def end_test(self, test: RunningTestCase, result: ResultTestCase):
        self.span_context[test.id][0].set_attribute("end_time", result.end_time.isoformat())
        if result.passed:
            self.span_context[test.id][0].set_status(trace.StatusCode.OK)
        elif result.failed:
            self.span_context[test.id][0].set_status(trace.StatusCode.ERROR, result.message)
        else:
            # self.test_span.set_status(trace.StatusCode.UNSET, result.status) # description is not set when status is UNSET
            self.span_context[test.id][0].set_attribute("status", result.status)
        self.test_counter[result.status].add(1, {"name": test.name})
        self.span_context.pop(test.id)[0].end()


    def end_suite(self, suite: RunningTestSuite, result: ResultTestSuite):
        self.span_context[suite.id][0].set_attribute("end_time", result.end_time.isoformat())
        if result.passed:
            self.span_context[suite.id][0].set_status(trace.StatusCode.OK)
        elif result.failed:
            self.span_context[suite.id][0].set_status(trace.StatusCode.ERROR, result.message)
        else:
            # self.suite_span.set_status(trace.StatusCode.UNSET, result.status) # description is not set when status is UNSET
            self.span_context[suite.id][0].set_attribute("status", result.status)
        self.span_context.pop(suite.id)[0].end()


    def close(self):
        self.span_context[None][0].end()