# Feature: Grounded Answer Generation
**Owner:** Backend | **Module:** Question & Answer

## Goal
Generate an answer using only the retrieved chunks — never the model's
own general knowledge.

## Scope
- Sends the retrieved chunks + the question to the Gemini chat endpoint
  (via OpenAI SDK), with an explicit instruction to answer only from the
  provided context and to say so if the context doesn't contain the
  answer.
- Tags which chunk(s) supported which part of the answer, so citations
  can be attached (see FEAT-18).
