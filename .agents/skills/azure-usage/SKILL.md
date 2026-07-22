---
name: azure-usage
description: Check Azure Foundry/OpenAI deployment usage and costs via az. Use when the user asks about Azure spend, Foundry cost, or deployment usage.
---

# Azure usage

Use `az` only. Resolve resources at runtime; never hardcode IDs or secrets.

## Scope

```bash
az account show --query "{name:name, id:id}" -o json
az cognitiveservices account list \
  --query "[?kind=='OpenAI' || kind=='AIServices' || kind=='CognitiveServices'].{name:name, rg:resourceGroup, kind:kind}" -o table
az cognitiveservices account deployment list -g "$RG" -n "$NAME" \
  --query "[].{name:name, model:properties.model.name, version:properties.model.version, capacity:sku.capacity}" -o table
```

## Costs

`az rest` Cost Management. Labels: `Foundry Models`, `Cognitive Services`, `Azure OpenAI`. Set `from`/`to` to the requested dates (UTC). Data often lags ~24h.

```bash
SUB=$(az account show --query id -o tsv)
az rest --method post \
  --url "/subscriptions/${SUB}/providers/Microsoft.CostManagement/query?api-version=2023-11-01" \
  --body "{
    \"type\": \"ActualCost\",
    \"timeframe\": \"Custom\",
    \"timePeriod\": { \"from\": \"YYYY-MM-DDT00:00:00Z\", \"to\": \"YYYY-MM-DDT23:59:59Z\" },
    \"dataset\": {
      \"granularity\": \"Daily\",
      \"aggregation\": { \"totalCost\": { \"name\": \"Cost\", \"function\": \"Sum\" } },
      \"filter\": { \"dimensions\": { \"name\": \"ServiceName\", \"operator\": \"In\",
        \"values\": [\"Foundry Models\", \"Cognitive Services\", \"Azure OpenAI\"] } },
      \"grouping\": [
        { \"type\": \"Dimension\", \"name\": \"Meter\" },
        { \"type\": \"Dimension\", \"name\": \"ResourceGroupName\" }
      ]
    }
  }"
```

Optional: filter `ResourceGroupName` to `$RG`. MTD: `"timeframe": "MonthToDate"`, drop `timePeriod`, `"granularity": "None"`. On 429 wait+retry once; on auth errors stop.

## Report

1. Period + currency + subscription display name (no IDs)
2. Deployments (name → model)
3. Daily totals, then by meter/model family
4. Note missing days (cost lag)
