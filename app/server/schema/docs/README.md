# Documentation for Blind Charging API

<a name="documentation-for-api-endpoints"></a>
## Documentation for API Endpoints

All URIs are relative to *http://localhost*

| Class | Method | HTTP request | Description |
|------------ | ------------- | ------------- | -------------|
| *ExperimentsApi* | [**logExposure**](Apis/ExperimentsApi.md#logexposure) | **POST** /exposure | Log an exposure event |
*ExperimentsApi* | [**logOutcome**](Apis/ExperimentsApi.md#logoutcome) | **POST** /outcome | Log an outcome event |
| *OperationsApi* | [**healthCheck**](Apis/OperationsApi.md#healthcheck) | **GET** /health | Health check |
| *RedactionApi* | [**getRedactionStatus**](Apis/RedactionApi.md#getredactionstatus) | **GET** /redact/{jurisdictionId}/{caseId} | Get status of document redaction for a case. |
*RedactionApi* | [**redactDocument**](Apis/RedactionApi.md#redactdocument) | **POST** /redact | Redact a document |
| *ReviewApi* | [**getBlindReviewInfo**](Apis/ReviewApi.md#getblindreviewinfo) | **GET** /blindreview/{jurisdictionId}/{caseId} | Get information about blind review for a given case. |


<a name="documentation-for-models"></a>
## Documentation for Models

 - [APIStatus](./Models/APIStatus.md)
 - [BlindChargeOutcome](./Models/BlindChargeOutcome.md)
 - [BlindReviewDecision](./Models/BlindReviewDecision.md)
 - [BlindReviewDecision_outcome](./Models/BlindReviewDecision_outcome.md)
 - [BlindReviewInfo](./Models/BlindReviewInfo.md)
 - [Defendant](./Models/Defendant.md)
 - [Defendant_name](./Models/Defendant_name.md)
 - [DisqualifyOutcome](./Models/DisqualifyOutcome.md)
 - [DocumentLink](./Models/DocumentLink.md)
 - [DocumentText](./Models/DocumentText.md)
 - [Error](./Models/Error.md)
 - [Exposure](./Models/Exposure.md)
 - [FinalChargeOutcome](./Models/FinalChargeOutcome.md)
 - [FinalReviewDecision](./Models/FinalReviewDecision.md)
 - [HumanName](./Models/HumanName.md)
 - [MaskedDefendant](./Models/MaskedDefendant.md)
 - [RedactionRequest](./Models/RedactionRequest.md)
 - [RedactionRequest_documents_inner](./Models/RedactionRequest_documents_inner.md)
 - [RedactionResult](./Models/RedactionResult.md)
 - [RedactionResultCompleted](./Models/RedactionResultCompleted.md)
 - [RedactionResultError](./Models/RedactionResultError.md)
 - [RedactionResultPending](./Models/RedactionResultPending.md)
 - [RedactionResultSuccess](./Models/RedactionResultSuccess.md)
 - [RedactionStatus](./Models/RedactionStatus.md)
 - [Review](./Models/Review.md)
 - [ReviewDecision](./Models/ReviewDecision.md)
 - [ReviewProtocol](./Models/ReviewProtocol.md)
 - [ReviewTimestamps](./Models/ReviewTimestamps.md)


<a name="documentation-for-authorization"></a>
## Documentation for Authorization

All endpoints do not require authorization.
