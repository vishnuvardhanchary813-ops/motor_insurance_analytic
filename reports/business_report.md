# Motor Insurance Analytics Business Report

## Executive Summary
[Complete after KPIs and findings are calculated.]

## Business Problem
Management needs a clear view of policy activity, premium income, claim costs,
settlement performance, and customer and vehicle patterns.

## Data and Table Summary
| Table | Rows | Purpose |
|---|---:|---|
| Customers | 20,000 | Customer and demographic details |
| Policies | 25,000 | Coverage, premium, and policy status |
| Vehicles | 25,000 | Vehicle attributes |
| Claims | 10,000 | Claim events, amounts, and outcomes |
| Payments | 7,000 | Claim payment records |

## Data Quality Findings
[Add the missing-value, duplicate, and relationship-check results from the notebook.]

## Cleaning Performed
[Describe the cleaning pipeline: whitespace trimming, date and numeric conversion,
duplicate removal, validation, and derived columns.]

## KPI Summary
[Add calculated policy, premium, claim, approval, rejection, and settlement KPIs.]

## EDA Findings
[Summarize the important patterns shown by the notebook charts.]

## Important Patterns
[Record data-supported patterns and evidence.]

## Business Insights
[Explain what each important pattern means for the insurer.]

## Recommendations
[Recommend actions that follow from the evidence.]

## Dashboard Summary
[Complete after the Streamlit dashboard is built.]

## Deployment Summary
[Complete after Docker and AWS deployment.]

## Conclusion
[Complete after analysis and deployment.]

## KPI Summary

- Total policies: 25,000
- Active policies: 7,551
- Expired policies: 10,464
- Cancelled policies: 320
- Renewed policies: 6,665
- Total premium: 795,568,771.71
- Average premium per policy: 31,822.75
- Total claims: 10,000
- Total claim amount: 2,885,436,440.65
- Average claim amount: 288,543.64
- Claim approval rate: 37.90% (approved claims / all claims)
- Claim rejection rate: 11.60% (rejected claims / all claims)
- Average settlement time: 23.93 days, calculated for claims with a settlement date

### Claims by State

Maharashtra had the most claims (1,178), while Telangana had the highest total claim amount (334,109,600). West Bengal had the highest average claim amount (317,080.82) among the states shown, based on 318 claims. This suggests different states lead on claim volume, total cost, and average claim size.

These figures describe claim counts and amounts. They do not establish which state has the highest claim frequency or risk, because that comparison also needs the number of policies in each state.
### Premium by Policy Type

Comprehensive policies generated the highest total premium (544,963,600) and had the most policies (15,085). Zero Depreciation had the highest average premium per policy (47,318.45), while Third Party had the lowest (12,152.36).

### Claims by Claim Type

Accident claims were the most common (4,838) and had the highest total claim amount (1,377,621,000). Fire claims had the highest average claim amount (299,284.75), based on 759 claims. Accident claims therefore drive the greatest overall claim volume and cost, while fire claims have the highest average amount among the listed types.
## Statistical Analysis

### Descriptive Statistics
[Add the mean, median, standard deviation, variance, and mode results from the notebook.]

### Correlations
[Add the correlation matrix results for claim amount, premium, and vehicle value.]

Correlations show association between numeric variables; they do not establish that one variable causes another.
## Important Patterns

### Pattern 1: Comprehensive policies lead premium income
**Evidence:** Comprehensive policies produced 544,963,600 in total premium across 15,085 policies. Zero Depreciation policies had the highest average premium per policy at 47,318.45.

### Pattern 2: Accident claims drive the largest total claim cost
**Evidence:** Accident claims were the most common type (4,838) and had the highest total claim amount (1,377,621,000). Fire claims had the highest average claim amount (299,284.75), based on 759 claims.

### Pattern 3: States differ in claim volume and average claim amount
**Evidence:** Maharashtra had the most claims (1,178). Telangana had the highest total claim amount (334,109,600). West Bengal had the highest average claim amount (317,080.82) among the listed states, based on 318 claims.

## Business Insights and Recommendations

- Comprehensive policies contribute the largest total premium in this dataset. Continue monitoring their premium and claim performance together.
- Accident claims account for the greatest total claim cost. Review accident claims by severity, vehicle age, and settlement time to identify operational areas for investigation.
- Fire claims have the highest average amount, but fewer claims than accident claims. Review a sample of high-value fire claims for patterns in severity and settlement.
- State-level totals differ, but they do not adjust for the number of policies in each state. Compare claim counts and costs per policy before making regional pricing or risk decisions.