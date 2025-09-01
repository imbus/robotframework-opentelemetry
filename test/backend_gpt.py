"""
This is a small backend to receive OpenTelemetry data from a exporter/collector and saving that data for testing the listener.
It does likely not comply to the OpenTelementry specification (e.g. the responses it sends back)!
"""
from threading import Thread
import gzip
from flask import Flask, request
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest


class OTLPTraceReceiver:
    def __init__(self, host="localhost", port=4318):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        # self.span_names = []  # Store span names here
        self.spans = []
        self.metrics = []

        @self.app.route("/v1/traces", methods=["POST"])
        def receive_traces():
            try:
                data = request.data
                if request.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)

                req = ExportTraceServiceRequest()
                req.ParseFromString(data)

                new_spans = []
                for resource_span in req.resource_spans:
                    for scope_span in resource_span.scope_spans:
                        for span in scope_span.spans:
                            # new_spans.append(span.name)
                            print(f"Received span: {span.name}")
                            self.spans.append(span)

                # self.span_names.extend(new_spans)
                return "", 200
            except Exception as e:
                print("Error parsing trace data:", e)
                return "Invalid request", 400
        
        @self.app.route("/v1/metrics", methods=["POST"])
        def receive_metrics():
            try:
                data = request.data
                if request.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)

                req = ExportMetricsServiceRequest()
                req.ParseFromString(data)

                for resource_metric in req.resource_metrics:
                    for scope_metric in resource_metric.scope_metrics:
                        for metric in scope_metric.metrics:
                            self.metrics.append(metric)

              
                # self.span_names.extend(new_spans)
                return "", 200
            except Exception as e:
                print("Error parsing metric data:", e)
                return "Invalid request", 400

    def start(self):
        # Run the Flask app in a background thread
        thread = Thread(target=self.app.run, kwargs={"host": self.host, "port": self.port})
        thread.daemon = True
        thread.start()
        print(f"OTLPTraceReceiver started at http://{self.host}:{self.port}/v1/traces")
    
    def shutdown(self):
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return 'Server shutting down...'


# Example usage
if __name__ == "__main__":
    receiver = OTLPTraceReceiver()
    receiver.start()

    import time
    print("Waiting for spans...")

    # Keep the main thread alive and print received spans every 5 seconds
    try:
        while True:
            time.sleep(5)
            if receiver.spans:
                print("Received span names so far:", [span.name for span in receiver.spans])
            else:
                print("No spans received yet...")
    except KeyboardInterrupt:
        print("Server stopped.")

    # receiver.shutdown()