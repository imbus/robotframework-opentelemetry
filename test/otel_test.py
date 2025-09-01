import os
import time
from urllib.parse import urlparse
from backend_gpt import OTLPTraceReceiver
from robot.api import ExecutionResult
from robot.result.model import TestSuite, TestCase
from opentelemetry.proto.trace.v1.trace_pb2 import Status
from opentelemetry.proto.metrics.v1.metrics_pb2 import Metric

from opentelemetry.proto.common.v1.common_pb2 import KeyValue, AnyValue, ArrayValue

def get_attr_value(value: AnyValue) -> str | bool | int | float | list | dict | bytes:
    match value.WhichOneof("value"):
        case "string_value":
            return value.string_value
        case "bool_value":
            return value.bool_value
        case "int_value":
            return value.int_value
        case "double_value":
            return value.double_value 
        case "array_value":
            return [get_attr_value(_value) for _value in value.array_value.values]
        case "kvlist_value":
            raise NotImplementedError("never tested!")
            return {_key: get_attr_value(_value) for _key, _value in value.kvlist_value}
        case "bytes_value":
            return value.bytes_value

def print_spans(return_spans: dict, indent=0):
    for key, value in return_spans.items():
        print(" "*indent, key, sep="")
        print_spans(value["children"], indent+2)


def get_otel_spans(received_spans):
    spans: dict = {}

    for span in received_spans:
        spans[span.span_id] = {"name": span.name, "_parent": span.parent_span_id, "status": span.status, "attributes": {}, "children": {}}
        #print(span.status) # description?
        for attr in span.attributes:
            # print("\t", attr.key, attr.value.string_value)
            attr: KeyValue = attr
            spans[span.span_id]["attributes"][attr.key] = get_attr_value(attr.value) # .string_value

    for span in spans.values():
        # print(span["name"], span["_parent"])
        if parent_id := span["_parent"]:
            spans[parent_id]["children"][span["name"]] = span
    
    return_spans = {value["name"]: value for key, value in spans.items() if not value["_parent"]}

    for span in spans.values():
        del span["_parent"]
    return return_spans



def check_common(result: TestSuite | TestCase, otel_span: dict):
    assert result.start_time.isoformat() == otel_span["attributes"]["start_time"]
    assert result.end_time.isoformat() == otel_span["attributes"]["end_time"]
    assert str(result.source) == otel_span["attributes"]["source"]
    match result.status:
        case "PASS":
            assert otel_span["status"].code == Status.STATUS_CODE_OK
            assert not otel_span["status"].message
        case "FAIL":
            assert otel_span["status"].code == Status.STATUS_CODE_ERROR
            assert result.message == otel_span["status"].message
        case "SKIP":
            assert otel_span["status"].code == Status.STATUS_CODE_UNSET
            assert result.status == otel_span["attributes"]["status"]


def check_suite(result_suite: TestSuite, otel_span: dict):
    # validates RF report against received otel span
    assert otel_span["attributes"]["type"] == "SUITE"
    check_common(result_suite, otel_span)

    assert len(result_suite.suites) == len([key for key, value in otel_span["children"].items() if value["attributes"]["type"] == "SUITE"])
    for suite in result_suite.suites:
        check_suite(suite, otel_span["children"][suite.name])
    
    assert len(list(result_suite.tests)) == len([key for key, value in otel_span["children"].items() if value["attributes"]["type"] == "TEST"])
    for test in result_suite.tests:
        check_test(test, otel_span["children"][test.name])


def check_test(result_test: TestCase, otel_span: dict):
    # validates RF report against received otel span
    assert otel_span["attributes"]["type"] == "TEST"
    assert result_test.tags == otel_span["attributes"]["tags"]
    check_common(result_test, otel_span)
    assert not otel_span["children"] # test cannot have children


def check_metrics(result_suite: TestSuite, metrics: list[Metric]):
    metrics: dict[str, dict[str, int]] = {metric.name: {[attr.value.string_value for attr in dp.attributes if attr.key == "name"][0]: dp.as_int for dp in metric.sum.data_points} for metric in metrics}

    for test_case in result_suite.all_tests:
        metric = metrics[test_case.status.replace(" ", "_").lower()] # get metric for test status
        assert test_case.name in metric # check if test name is a data point in metric
        assert metric[test_case.name] == 1  # check if value of test case is one
    

def test_otel_listener():
    # receiver = OTLPTraceReceiver(COLLECTOR_IP, 1236)
    print(os.environ["COL_EXPORTER_OTLPHTTP_ENDPOINT"])
    receiver_url = urlparse(os.environ["COL_EXPORTER_OTLPHTTP_ENDPOINT"])
    receiver_host = receiver_url.hostname
    receiver_port = receiver_url.port
    receiver = OTLPTraceReceiver(receiver_host, receiver_port)
    receiver.start()

    # os.system(f"robot --listener \"OpenTelemetryListener\OpenTelemetryListener.py\" test\\test.robot")
    listerner_path = "OpenTelemetryListener/OpenTelemetryListener.py"
    test_path = "test/" # test.robot"
    os.system(f"robot --listener \"{os.path.normpath(listerner_path)}\" {os.path.normpath(test_path)}")

    time.sleep(5) # I know explicit wait is bad - but for know it will do

    result = ExecutionResult('output.xml')
    otel_spans = get_otel_spans(receiver.spans)

    otel_spans: dict = otel_spans[os.environ.get("OTEL_LISTENER_SPAN_NAME", "RobotListener")]["children"]

    # generic checks
    assert result.suite.name in otel_spans
    check_suite(result.suite, otel_spans[result.suite.name])

    check_metrics(result.suite, receiver.metrics)


    otel_spans = otel_spans[result.suite.name]["children"]
    # specific checks
    assert "Create A Random String" in otel_spans["Test"]["children"]
    assert otel_spans["Test"]["children"]["Create A Random String"]["status"].code  == Status.STATUS_CODE_OK

    assert "Skip this test" in otel_spans["Test"]["children"]
    assert otel_spans["Test"]["children"]["Skip this test"]["status"].code  == Status.STATUS_CODE_UNSET
    assert otel_spans["Test"]["children"]["Skip this test"]["attributes"]["status"] == "SKIP"
    
    assert "Fail this test" in otel_spans["Test"]["children"]
    assert otel_spans["Test"]["children"]["Fail this test"]["status"].code  == Status.STATUS_CODE_ERROR
    assert otel_spans["Test"]["children"]["Fail this test"]["status"].message  == "1 != 2"

    assert otel_spans["Tags Test"]["children"]["No own tags"]["attributes"]["tags"] == ["gui", "html"]
    assert otel_spans["Tags Test"]["children"]["Own tags"]["attributes"]["tags"] == ["gui", "html", "own", "tags"]
    assert otel_spans["Tags Test"]["children"]["Remove common tag"]["attributes"]["tags"] == ["gui", "own"]

    print("done")

if __name__ == "__main__":
    test_otel_listener()