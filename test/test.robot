*** Settings ***
Library    String

*** Test Cases ***
Create A Random String
    Log To Console    We are going to generate a random string
    Generate Random String    10
    Log To Console    We finished generating a random string

Skip this test
    Skip If    1 == 1
    Log To Console    You should never see this

Fail this test
    Should Be Equal    1    2

Fail this test2
    Should Be Equal    1    2