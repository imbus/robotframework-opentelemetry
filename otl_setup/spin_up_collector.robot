*** Settings ***
Documentation       This file contains keywords to start, stop, and restart the OpenTelemetry Collector using Podman.

Library             Process


*** Tasks ***
Start Collector
    ${result}    Start Collector
    Sleep    2s
    # Should Be Equal As Strings    ${result.rc}    0    Starting OpenTelemetry Collector failed
    [Teardown]    Log To Console    ${result.stderr.read()}

Restart Collector
    ${result}    Stop Collector
    ${result}    Start Collector

    # Should Be Equal As Integers    ${result.rc}    0    Restarting OpenTelemetry Collector failed
    [Teardown]    Log To Console    ${result.stderr}

Stop Collector
    ${result}    Stop Collector

    Should Be Equal As Integers    ${result.rc}    0    Stopping OpenTelemetry Collector failed
    [Teardown]    Log To Console    ${result.stderr}


*** Keywords ***
Start Collector
    ${result}    Start Process    podman
    ...    run
    ...    --name
    ...    otel-collector
    ...    --detach
    ...    --rm
    ...    -p
    ...    127.0.0.1:4317:4317
    ...    -p
    ...    127.0.0.1:4318:4318
    # ...    -v
    # ...    ${CURDIR}/otel-collector-config.yaml:/etc/otelcol/config.yaml
    ...    otel/opentelemetry-collector-contrib:latest
    RETURN    ${result}

Stop Collector
    ${result}    Run Process    podman
    ...    stop
    ...    otel-collector
    RETURN    ${result}
