# Robot Framework OpenTelemetry Listener

The OpenTelemetryListener provides a convient way to publish test metrics to a [OpenTelemetry](https://opentelemetry.io/) (OT) collector from [RobotFramework](https://robotframework.org/) (RF).

## "Features"
 - one span for the Listener itselt (named "RobotListener" by default)
 - one span per test suite
 - one span per test
 - one meter ("Test Statistics")
    - one counter per test status

Test suite(s) and test hierachy is preserved.

### Attributes
Values are provided by robotframework (e.g. times are not adjusted or tempered with).

#### Suite and Test
 - `source`
 - `start_time` (isoformat)
 - `end_time` (isoformat) exists once suite/test is finished
 - `type` ("SUITE"/"TEST")
 - `status`, exists if suite/test neither passed nor failed. Set to the RF status.


#### Test
- `tags`


### Span status
Set to OK or ERROR for passed or failed suite/test respectively.
If suite/test failed then the RF result message is used as OT status description.


## Settings


### Arguments

| Name               | Description                              | Default       | Type   | Notes                                                      |
| ------------------ | ---------------------------------------- | ------------- | ------ | ---------------------------------------------------------- |
| url                | base URL for the span exporter endpoint. | None          | String | "/v1/traces" is appended automatically                     |
| listener_span_name | name for the span of the listener        | RobotListener | String | if OTEL_LISTENER_SPAN_NAME is set this argument is ignored |
| module_name        | module name for the tracer               | \_\_name__    | String |                                                            |


### Environment variables
| Name                              | Description                     | Default           | Type   | Notes                                                                         |
| --------------------------------- | ------------------------------- | ----------------- | ------ | ----------------------------------------------------------------------------- |
| OTEL_LISTENER_PROCESSOR           | Batch- or Simple span processor | "simple"          | Enum   | "simple" or "batch"                                                           |
| OTEL_LISTENER_SPAN_NAME           | name of listener span name      | "RobotListener"   | String | can also be changed as listener_span_name arg, envion var has priority if set |
| OTEL_LISTENER_STATUS_COUNTER_NAME | name of metric for test status  | "Test Statistics" | String |

For further configurations check the [OTel Documentation](https://opentelemetry.io/docs/specs/otel/protocol/exporter/).