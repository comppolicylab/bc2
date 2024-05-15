# Blind Charging API

> Version 0.1.1

Status: **DRAFT**

**_This is a draft specification. The objects and routes are subject to revision._**

This API lets an application communicate with the CPL Blind Charging module via an HTTP REST API.


## Path Table

| Method | Path | Description |
| --- | --- | --- |
| GET | [/health](#gethealth) | Health check |
| POST | [/redact](#postredact) | Redact a document |
| GET | [/redact/{jurisdictionId}/{caseId}](#getredactjurisdictionidcaseid) | Get status of document redaction for a case. |
| GET | [/blindreview/{jurisdictionId}/{caseId}](#getblindreviewjurisdictionidcaseid) | Get information about blind review for a given case. |
| POST | [/exposure](#postexposure) | Log an exposure event |
| POST | [/outcome](#postoutcome) | Log an outcome event |

## Reference Table

| Name | Path | Description |
| --- | --- | --- |
| Error | [#/components/schemas/Error](#componentsschemaserror) |  |
| DocumentLink | [#/components/schemas/DocumentLink](#componentsschemasdocumentlink) |  |
| DocumentText | [#/components/schemas/DocumentText](#componentsschemasdocumenttext) |  |
| BlindReviewInfo | [#/components/schemas/BlindReviewInfo](#componentsschemasblindreviewinfo) |  |
| RedactionResultSuccess | [#/components/schemas/RedactionResultSuccess](#componentsschemasredactionresultsuccess) |  |
| RedactionResultError | [#/components/schemas/RedactionResultError](#componentsschemasredactionresulterror) |  |
| RedactionResultPending | [#/components/schemas/RedactionResultPending](#componentsschemasredactionresultpending) |  |
| RedactionResultCompleted | [#/components/schemas/RedactionResultCompleted](#componentsschemasredactionresultcompleted) | A completed redaction job. Similar to `RedactionResult`,
but where it is not possible to see a result in an incomplete (pending or queued) state.
 |
| RedactionResult | [#/components/schemas/RedactionResult](#componentsschemasredactionresult) | Information about a redaction job.
 |
| RedactionStatus | [#/components/schemas/RedactionStatus](#componentsschemasredactionstatus) | The status of redaction for a case.
 |
| HumanName | [#/components/schemas/HumanName](#componentsschemashumanname) | A structured representation of someone's name. |
| MaskedDefendant | [#/components/schemas/MaskedDefendant](#componentsschemasmaskeddefendant) | Mapping between a defendant's ID to their alias. |
| Defendant | [#/components/schemas/Defendant](#componentsschemasdefendant) | Mapping between a defendant's ID to their name(s). |
| RedactionRequest | [#/components/schemas/RedactionRequest](#componentsschemasredactionrequest) |  |
| ReviewTimestamps | [#/components/schemas/ReviewTimestamps](#componentsschemasreviewtimestamps) |  |
| FinalChargeOutcome | [#/components/schemas/FinalChargeOutcome](#componentsschemasfinalchargeoutcome) |  |
| BlindChargeOutcome | [#/components/schemas/BlindChargeOutcome](#componentsschemasblindchargeoutcome) |  |
| DisqualifyOutcome | [#/components/schemas/DisqualifyOutcome](#componentsschemasdisqualifyoutcome) |  |
| ReviewProtocol | [#/components/schemas/ReviewProtocol](#componentsschemasreviewprotocol) |  |
| BlindReviewDecision | [#/components/schemas/BlindReviewDecision](#componentsschemasblindreviewdecision) |  |
| FinalReviewDecision | [#/components/schemas/FinalReviewDecision](#componentsschemasfinalreviewdecision) |  |
| ReviewDecision | [#/components/schemas/ReviewDecision](#componentsschemasreviewdecision) |  |
| Exposure | [#/components/schemas/Exposure](#componentsschemasexposure) |  |
| Review | [#/components/schemas/Review](#componentsschemasreview) |  |
| APIStatus | [#/components/schemas/APIStatus](#componentsschemasapistatus) |  |

## Path Details

***

### [GET]/health

- Summary
Health check

- Description
Check the health of the API.


#### Responses

- 200 OK

`application/json`

```ts
{
  detail: string
}
```

- 500 Not OK

`application/json`

```ts
{
  detail: string
}
```

***

### [POST]/redact

- Summary
Redact a document

- Description
Submit a document for redaction. Redaction happens asynchronously and may take some time.
When finished, the redacted document will be posted to the provided callback URL.

A callback will be POSTed to the provided URL when the redaction process is completed for each input document.
The callback will contain either `RedactionResultSuccess` or `RedactionResultError`.


#### RequestBody

- application/json

```ts
{
  jurisdictionId: string
  caseId: string
  // Mapping between a defendant's ID to their name(s).
  defendants: {
    defendantId: string
    name: string | #/components/schemas/HumanName
    aliases?: string | #/components/schemas/HumanName[]
  }[]
  documents?: #/components/schemas/DocumentLink | #/components/schemas/DocumentText[]
  callbackUrl: string
}
```

#### Responses

- 201 Accepted

***

### [GET]/redact/{jurisdictionId}/{caseId}

- Summary
Get status of document redaction for a case.

- Description
Get the status of redaction for all documents in a case.
This will return a list of document IDs and their redaction status.

Generally, the push mechanism provided by the callback URL passed to the `/redact` endpoint should be used to determine when the redaction process is completed.
However, this endpoint can be used to poll for the status of redaction if necessary.


#### Parameters(Query)

```ts
defendantId?: string
```

#### Responses

- 200 OK

`application/json`

```ts
// The status of redaction for a case.
//
{
  jurisdictionId: string
  caseId: string
  // Information about a redaction job.
  //
  requests?: #/components/schemas/RedactionResultSuccess | #/components/schemas/RedactionResultError | #/components/schemas/RedactionResultPending[]
}
```

***

### [GET]/blindreview/{jurisdictionId}/{caseId}

- Summary
Get information about blind review for a given case.

- Description
This endpoint provides information about the blind review process for the given case.

The payload will indicate whether blind review is required for this case.

If blind review is required, this endpoint will also provide a list of redacted documents to present for review.


#### Parameters(Query)

```ts
defendantId?: string
```

#### Responses

- 200 OK

`application/json`

```ts
{
  jurisdictionId: string
  caseId: string
  blindReviewRequired: boolean
  // Mapping between a defendant's ID to their alias.
  maskedDefendants: {
    defendantId: string
    alias: string
  }[]
  redactedDocuments: {
    attachmentType: enum[LINK]
    documentId: string
    url: string
  }[]
}
```

- 424 Documents are not processed yet

`application/json`

```ts
{
  message: string
}
```

***

### [POST]/exposure

- Summary
Log an exposure event

- Description
This endpoint records which information is presented to attorneys and when, prior to them making a decision.

Sending "exposure" events is required for all cases involved in research experiments, _both for blind review and also final review_.


#### RequestBody

- application/json

```ts
{
  jurisdictionId: string
  caseId: string
  defendantId: string
  reviewingAttorneyUserId: string
  documentIds?: string[]
  protocol: enum[BLIND_REVIEW, FINAL_REVIEW]
}
```

#### Responses

- 201 Accepted

***

### [POST]/outcome

- Summary
Log an outcome event

- Description
This endpoint records the charging decisions made by attorneys, both for blind review and final review.

Sending "outcome" events is required for all cases involved in research experiments, _regardless of whether the case is subject to blind review or not_.


#### RequestBody

- application/json

```ts
{
  jurisdictionId: string
  caseId: string
  defendantId: string
  reviewingAttorneyUserId: string
  documentIds?: string[]
  decision: #/components/schemas/BlindReviewDecision | #/components/schemas/FinalReviewDecision
  timestamps: {
    pageOpen: string
    decision: string
  }
}
```

#### Responses

- 201 Accepted

## References

### #/components/schemas/Error

```ts
{
  message: string
}
```

### #/components/schemas/DocumentLink

```ts
{
  attachmentType: enum[LINK]
  documentId: string
  url: string
}
```

### #/components/schemas/DocumentText

```ts
{
  attachmentType: enum[TEXT]
  documentId: string
  content: string
}
```

### #/components/schemas/BlindReviewInfo

```ts
{
  jurisdictionId: string
  caseId: string
  blindReviewRequired: boolean
  // Mapping between a defendant's ID to their alias.
  maskedDefendants: {
    defendantId: string
    alias: string
  }[]
  redactedDocuments: {
    attachmentType: enum[LINK]
    documentId: string
    url: string
  }[]
}
```

### #/components/schemas/RedactionResultSuccess

```ts
{
  jurisdictionId: string
  caseId: string
  // Mapping between a defendant's ID to their alias.
  maskedDefendants: {
    defendantId: string
    alias: string
  }[]
  inputDocument: {
    attachmentType: enum[LINK]
    documentId: string
    url: string
  }
  redactedDocument:#/components/schemas/DocumentLink
  status: enum[COMPLETE]
}
```

### #/components/schemas/RedactionResultError

```ts
{
  jurisdictionId: string
  caseId: string
  // Mapping between a defendant's ID to their alias.
  maskedDefendants: {
    defendantId: string
    alias: string
  }[]
  inputDocument: {
    attachmentType: enum[LINK]
    documentId: string
    url: string
  }
  error: string
  status: enum[ERROR]
}
```

### #/components/schemas/RedactionResultPending

```ts
{
  jurisdictionId: string
  caseId: string
  // Mapping between a defendant's ID to their alias.
  maskedDefendants: {
    defendantId: string
    alias: string
  }[]
  inputDocument: {
    attachmentType: enum[LINK]
    documentId: string
    url: string
  }
  status: enum[QUEUED, PROCESSING]
}
```

### #/components/schemas/RedactionResultCompleted

```ts
{
  "description": "A completed redaction job. Similar to `RedactionResult`,\nbut where it is not possible to see a result in an incomplete (pending or queued) state.\n",
  "oneOf": [
    {
      "$ref": "#/components/schemas/RedactionResultSuccess"
    },
    {
      "$ref": "#/components/schemas/RedactionResultError"
    }
  ],
  "discriminator": {
    "propertyName": "status",
    "mapping": {
      "COMPLETE": "#/components/schemas/RedactionResultSuccess",
      "ERROR": "#/components/schemas/RedactionResultError"
    }
  }
}
```

### #/components/schemas/RedactionResult

```ts
{
  "description": "Information about a redaction job.\n",
  "oneOf": [
    {
      "$ref": "#/components/schemas/RedactionResultSuccess"
    },
    {
      "$ref": "#/components/schemas/RedactionResultError"
    },
    {
      "$ref": "#/components/schemas/RedactionResultPending"
    }
  ],
  "discriminator": {
    "propertyName": "status",
    "mapping": {
      "COMPLETE": "#/components/schemas/RedactionResultSuccess",
      "ERROR": "#/components/schemas/RedactionResultError",
      "QUEUED": "#/components/schemas/RedactionResultPending",
      "PROCESSING": "#/components/schemas/RedactionResultPending"
    }
  }
}
```

### #/components/schemas/RedactionStatus

```ts
// The status of redaction for a case.
//
{
  jurisdictionId: string
  caseId: string
  // Information about a redaction job.
  //
  requests?: #/components/schemas/RedactionResultSuccess | #/components/schemas/RedactionResultError | #/components/schemas/RedactionResultPending[]
}
```

### #/components/schemas/HumanName

```ts
// A structured representation of someone's name.
{
  firstName: string
  lastName?: string
  middleName?: string
  suffix?: string
}
```

### #/components/schemas/MaskedDefendant

```ts
// Mapping between a defendant's ID to their alias.
{
  defendantId: string
  alias: string
}
```

### #/components/schemas/Defendant

```ts
// Mapping between a defendant's ID to their name(s).
{
  defendantId: string
  name: string | #/components/schemas/HumanName
  aliases?: string | #/components/schemas/HumanName[]
}
```

### #/components/schemas/RedactionRequest

```ts
{
  jurisdictionId: string
  caseId: string
  // Mapping between a defendant's ID to their name(s).
  defendants: {
    defendantId: string
    name: string | #/components/schemas/HumanName
    aliases?: string | #/components/schemas/HumanName[]
  }[]
  documents?: #/components/schemas/DocumentLink | #/components/schemas/DocumentText[]
  callbackUrl: string
}
```

### #/components/schemas/ReviewTimestamps

```ts
{
  pageOpen: string
  decision: string
}
```

### #/components/schemas/FinalChargeOutcome

```ts
{
  // The final charging decision.
  chargingDecision: enum[CHARGE, DECLINE]
  chargingDecisionExplanation?: string
}
```

### #/components/schemas/BlindChargeOutcome

```ts
{
  chargingDecision: enum[CHARGE_LIKELY, CHARGE_MAYBE, DECLINE_MAYBE, DECLINE_LIKELY]
  chargingDecisionExplanation: string
  additionalEvidence?: string
}
```

### #/components/schemas/DisqualifyOutcome

```ts
{
  outcomeType: enum[DISQUALIFY]
  disqualifyingReason: enum[ASSIGNED_TO_UNBLIND, CASE_TYPE_INELIGIBLE, PRIOR_KNOWLEDGE_BIAS, NARRATIVE_INCOMPLETE, REDACTION_MISSING, REDACTION_ILLEGIBLE, OTHER]
  disqualifyingReasonExplanation?: string
}
```

### #/components/schemas/ReviewProtocol

```ts
{
  "type": "string",
  "enum": [
    "BLIND_REVIEW",
    "FINAL_REVIEW"
  ]
}
```

### #/components/schemas/BlindReviewDecision

```ts
{
  protocol: enum[BLIND_REVIEW]
  outcome: #/components/schemas/BlindChargeOutcome | #/components/schemas/DisqualifyOutcome
}
```

### #/components/schemas/FinalReviewDecision

```ts
{
  protocol: enum[FINAL_REVIEW]
  outcome: {
    // The final charging decision.
    chargingDecision: enum[CHARGE, DECLINE]
    chargingDecisionExplanation?: string
  }
}
```

### #/components/schemas/ReviewDecision

```ts
{
  "oneOf": [
    {
      "$ref": "#/components/schemas/BlindReviewDecision"
    },
    {
      "$ref": "#/components/schemas/FinalReviewDecision"
    }
  ],
  "discriminator": {
    "propertyName": "protocol",
    "mapping": {
      "BLIND_REVIEW": "#/components/schemas/BlindReviewDecision",
      "FINAL_REVIEW": "#/components/schemas/FinalReviewDecision"
    }
  }
}
```

### #/components/schemas/Exposure

```ts
{
  jurisdictionId: string
  caseId: string
  defendantId: string
  reviewingAttorneyUserId: string
  documentIds?: string[]
  protocol: enum[BLIND_REVIEW, FINAL_REVIEW]
}
```

### #/components/schemas/Review

```ts
{
  jurisdictionId: string
  caseId: string
  defendantId: string
  reviewingAttorneyUserId: string
  documentIds?: string[]
  decision: #/components/schemas/BlindReviewDecision | #/components/schemas/FinalReviewDecision
  timestamps: {
    pageOpen: string
    decision: string
  }
}
```

### #/components/schemas/APIStatus

```ts
{
  detail: string
}
```
