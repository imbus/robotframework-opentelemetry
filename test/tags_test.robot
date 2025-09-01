*** Settings ***
Test Tags       gui    html

*** Test Cases ***
No own tags
    [Documentation]    Keyword has tags 'gui' and 'html'.
    No Operation

Own tags
    [Documentation]    Keyword has tags 'gui', 'html', 'own' and 'tags'.
    [Tags]    own    tags
    No Operation

Remove common tag
    [Documentation]    Test has tags 'gui' and 'own'.
    [Tags]    own    -html
    No Operation