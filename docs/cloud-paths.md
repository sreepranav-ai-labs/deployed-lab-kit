# Cloud paths

*Companion to* Deployed: How Forward Deployed Engineers Take Frontier AI Into Production. *Product names as of October 2026; providers rename and move features often, so check their current documentation.*

## Why the labs run locally

Every lab runs on a laptop with an open-weight model served by Ollama. Anyone can run them free, without a cloud account, a credit card or anyone's approval, and every result in the book can be reproduced exactly.

The case companies in the book run on real platforms: Varuna Bank on Azure, Surya Assurance on AWS, Akasha Telecom on Google Cloud, Agni Components on Databricks, Prithvi Industrial Supply on Snowflake and Salesforce. Those platforms are the production architecture each story describes. The parts of each lab that carry its lessons do not change when the platform does:

- the model makes one narrow judgement, and code checks it and decides;
- instructions hidden in documents are removed before the model reads them;
- every change is scored on a development split, and the golden split is scored once;
- a gate decides whether a change ships.

What changes on a platform is the plumbing around them: where the data lives, how documents are read, how search works, how steps are orchestrated, where secrets are kept and how the system is watched.

## Each lab and its platform

| Lab | Platform in the book | Local milestone | Cloud milestone |
| --- | --- | --- | --- |
| State Revenue Department | On-premises open source | m1 to m3, released | Runs on premises by design |
| Varuna Bank | Azure: Microsoft Foundry, Azure AI Search | m1, released | m3-azure, after launch |
| Surya Assurance | AWS: Amazon Bedrock, Textract, Step Functions | m1, released | m3-aws, after launch |
| Akasha Telecom | Google Cloud: Gemini models on Gemini Enterprise Agent Platform (formerly Vertex AI), BigQuery | m1, released | m3-gcp, after launch |
| Prithvi Industrial Supply | Snowflake Cortex and Salesforce | m1, released | m3-snowflake, after launch |
| Agni Components | Databricks: Unity Catalog, Vector Search, MLflow | in progress | m3-databricks, after launch |
| Chandra Finance | AWS or Azure in an Indian region | planned | after launch |
| Ashvini Health Network | Azure in India: Document Intelligence, Speech, Foundry | planned | after launch |

Each cloud milestone will be built and tested end to end before it is released, as the local milestones were.

## The same building blocks on each platform

| Building block | In the labs | Azure | AWS | Google Cloud | Snowflake | Databricks |
| --- | --- | --- | --- | --- | --- | --- |
| Model endpoint | Ollama, local | Microsoft Foundry | Amazon Bedrock | Gemini Enterprise Agent Platform | Cortex AI | Model Serving and AI Gateway |
| Records and history | JSON Lines files | Azure SQL, Fabric | S3, RDS | BigQuery | Tables | Delta tables in Unity Catalog |
| Search over documents | (m2 milestones) | Azure AI Search | OpenSearch, Bedrock Knowledge Bases | Vector Search | Cortex Search | Vector Search |
| Reading scans and forms | OCR text in the data | Document Intelligence | Textract | Document AI | Document AI functions | Document parsing functions |
| Orchestration | Python | Functions, Logic Apps | Step Functions, Lambda | Cloud Run, Workflows | Tasks, Snowpark | Jobs, Lakeflow |
| Secrets | Environment variables | Key Vault | Secrets Manager | Secret Manager | Secrets | Secret scopes |
| Traces and evaluation | `deployed_kit` tracer and gate | Application Insights, Foundry evaluations | CloudWatch, Bedrock evaluations | Cloud Logging, evaluation service | Event tables, AI observability | MLflow tracing and evaluation |

## Pointing a lab at a hosted model today

Every lab calls its model through the kit's gateway, so swapping the local model for a hosted one is configuration, not code. Each platform below offers an OpenAI-compatible chat completions endpoint. Set the variables, then run the lab's usual commands.

**Status: these configurations follow each provider's documentation but have not yet been run against the labs.** Each will be confirmed when that lab's cloud milestone is built. Use synthetic lab data only, watch your costs, and keep keys out of files you commit.

Common settings:

```powershell
$env:LAB_PROVIDER = "openai_compatible"
$env:LAB_BASE_URL = "<base URL from the table below>"
$env:LAB_API_KEY  = "<key or token>"
$env:LAB_MODEL    = "<model or deployment name>"
# If the provider rejects the JSON-mode parameter:
$env:LAB_JSON_MODE = "0"
```

| Platform | `LAB_BASE_URL` | `LAB_API_KEY` | `LAB_MODEL` |
| --- | --- | --- | --- |
| Microsoft Foundry (Azure) | `https://<resource>.openai.azure.com/openai/v1` | The resource's API key | Your deployment name |
| Amazon Bedrock | `https://bedrock-runtime.<region>.amazonaws.com/openai/v1` | An Amazon Bedrock API key | A model whose card lists Chat Completions, for example `openai.gpt-oss-120b-1:0` |
| Google Cloud | `https://<region>-aiplatform.googleapis.com/v1/projects/<project>/locations/<region>/endpoints/openapi` | The output of `gcloud auth print-access-token` (it expires after about an hour) | A Gemini model, in the form `google/<model>` |
| Snowflake Cortex | `https://<account>.snowflakecomputing.com/api/v2/cortex/v1` | A programmatic access token; the user's role needs `SNOWFLAKE.CORTEX_USER` | A Snowflake-hosted model available in your region |
| Databricks | `https://<workspace>/ai-gateway/mlflow/v1` | A personal access token for development; OAuth machine-to-machine in production | A served model, for example `system.ai.<model>` |

The Google Cloud URL is the form documented for Vertex AI. Google renamed Vertex AI as Gemini Enterprise Agent Platform in 2026, so check the current documentation for the endpoint.

Things to expect when you switch:

- **Results will change.** A larger hosted model may pass a gate the local model failed, or fail one it passed. Score the dev split first, and the golden split once, as the book describes.
- **Cost becomes real.** Set `LAB_PRICE_IN_PER_1K` and `LAB_PRICE_OUT_PER_1K` so the run reports cost per task.
- **Where the data goes matters.** Pick a region that matches the story: the Indian case companies keep data in India.

## Sources

- Microsoft: Azure OpenAI in Microsoft Foundry Models v1 API, learn.microsoft.com/azure/foundry/openai/api-version-lifecycle
- AWS: Chat Completions API in Amazon Bedrock, docs.aws.amazon.com/bedrock/latest/userguide/inference-chat-completions.html
- Google Cloud: OpenAI compatibility, docs.cloud.google.com/vertex-ai/generative-ai/docs/start/openai
- Snowflake: Cortex Chat Completions API, docs.snowflake.com/user-guide/snowflake-cortex/open_ai_sdk
- Databricks: Get started querying LLMs on Databricks, docs.databricks.com/aws/en/large-language-models/llm-serving-intro
