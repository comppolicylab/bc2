Blind Charging (v2)
===

TODO (jnu) write docs

## Azure config instructions

Uses Azure DocumentIntelligence and Azure OpenAI services to redact police narratives.

(More instructions to come.)

Azure configuration instructions:
1. To train extraction models in Form Recognizer Studio, you need to create a system-assigned identity within the Document Intelligence service.
    1. On the Document Intelligence setting page, navigate to "Identity".
    2. Turn on "Status" under the system-assigned tab.
    3. Click save.
    4. Once the save has registered, click the "Azure role assignments" button.
    5. Click "Add role assignment".
    6. Select Scope = "Storage", Subscription = the correct subscription, Resource = the correct resource, and Role = "Storage Blob Data Reader".
    7. Click save.
    8. Give it up to 30 minutes to propogate (it won't appear in the list at first).
    9. Now in Form Recognizer you should be able to train a model using labeled documents on the relevant storage blob.

(these are very incomplete, ACW adding one specific step to start)
