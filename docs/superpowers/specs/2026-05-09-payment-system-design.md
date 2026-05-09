# Payment System Design

## Goal

Add a future-ready billing design for LinKo Server. The product will start with a Free plan and a paid Pro monthly subscription. Pro increases the user's monthly usage allowance rather than unlocking a separate feature set.

This design chooses a payment provider direction and defines the server boundaries needed to add billing later without coupling the product entitlement logic to one vendor.

## Decision

Use Lemon Squeezy as the first payment provider candidate.

Lemon Squeezy is a Merchant of Record, which fits the current constraints better than a direct payment service provider integration:

- LinKo does not plan to register a business entity initially.
- The primary customers are outside Korea.
- The product is a digital SaaS subscription.
- The team should avoid taking on global VAT, sales tax, and payment compliance work at the start.

Stripe direct integration is not the first choice for this phase because it gives excellent low-level payment APIs but leaves more tax and compliance responsibility with LinKo. Paddle and Polar remain viable later alternatives, but Lemon Squeezy is the most practical initial default for a small Free/Pro SaaS.

## Product Model

Plans:

- Free: no payment required, lower monthly usage allowance.
- Pro: monthly subscription, higher monthly usage allowance.

The exact usage numbers are intentionally deferred. The billing architecture only needs stable plan identifiers and an internal policy layer that maps each plan to a monthly allowance.

Usage-based overage billing is out of scope for the first billing version. When a user reaches the monthly limit, the API should reject additional paid-feature usage until the next usage period or until the user upgrades.

## Architecture

```text
Frontend
  -> LinKo Server: request checkout session
  -> Lemon Squeezy hosted checkout: complete payment
  -> LinKo Server: fetch current subscription and usage state

Lemon Squeezy
  -> LinKo Server webhook: subscription created, renewed, updated, cancelled, payment failed

LinKo Server
  - users
  - subscriptions
  - usage_periods
  - payment_provider_events
```

The frontend never calls Lemon Squeezy with secret credentials. It asks LinKo Server to create a checkout URL, then redirects the user to the hosted checkout page.

LinKo Server uses Lemon Squeezy APIs only from trusted backend code. It receives webhooks from Lemon Squeezy and stores the resulting subscription state locally.

Product access checks use LinKo's database, not live payment provider API calls. This keeps normal API requests fast and avoids making product availability depend on provider API latency.

## Components

### Checkout API

Authenticated users can request a Pro checkout URL from LinKo Server.

The server creates a Lemon Squeezy checkout session for the configured Pro variant and includes enough metadata to map the payment back to the internal user, such as `user_id`.

The API returns only the hosted checkout URL to the frontend.

### Webhook Receiver

The webhook receiver is the trusted path for payment state changes.

It should:

- Verify Lemon Squeezy webhook signatures.
- Store provider event IDs for idempotency.
- Map provider customer and subscription IDs to internal users.
- Update the internal subscription record.
- Return success for duplicate already-processed events.

### Subscription Store

The internal subscription table should represent product entitlement, not every provider-specific field.

Suggested fields:

- `id`
- `user_id`
- `provider`
- `provider_customer_id`
- `provider_subscription_id`
- `plan`
- `status`
- `current_period_start`
- `current_period_end`
- `cancel_at_period_end`
- timestamps

Initial statuses:

- `free`
- `active`
- `past_due`
- `cancelled`
- `expired`

`active` grants Pro allowance. `past_due`, `cancelled`, and `expired` should not grant Pro allowance unless a later grace-period policy is explicitly added.

### Usage Periods

Usage should be tracked by user and billing period.

Suggested fields:

- `id`
- `user_id`
- `period_start`
- `period_end`
- `used_count`
- timestamps

The first version can count the number of successful paid-feature operations, such as video metadata or analysis requests, depending on the final product packaging.

Usage checks should happen in the same server-side flow that performs the billable operation. If the operation is allowed and succeeds, increment the usage counter.

### Provider Adapter

Keep Lemon Squeezy-specific API and webhook parsing in a small adapter module.

The rest of the application should depend on internal concepts:

- plan: `free` or `pro`
- status: `active`, `past_due`, `cancelled`, `expired`
- allowance: monthly count
- usage period: start and end timestamps

This makes a future Paddle or Polar migration possible without rewriting the entitlement checks throughout the application.

## Data Flow

### Upgrade to Pro

```text
1. User clicks upgrade in the frontend.
2. Frontend calls LinKo Server to create a checkout.
3. Server creates a Lemon Squeezy checkout URL with user metadata.
4. Frontend redirects the user to Lemon Squeezy hosted checkout.
5. User completes payment.
6. Lemon Squeezy sends a webhook to LinKo Server.
7. Server verifies the webhook and updates the subscription row to active Pro.
8. Frontend reloads subscription state from LinKo Server.
```

### Use a Limited Feature

```text
1. Frontend calls a protected LinKo API.
2. Server authenticates the user.
3. Server loads subscription and current usage period.
4. Server resolves the user's monthly allowance.
5. If usage remains, the server performs the operation and increments usage.
6. If the limit is reached, the server returns a limit error.
```

### Cancel or Payment Failure

```text
1. Lemon Squeezy sends subscription update or payment failure webhook.
2. Server verifies and stores the event.
3. Server updates subscription status and period dates.
4. Future entitlement checks use the updated local status.
```

## API Surface

Future endpoints:

```text
POST /api/billing/checkout
GET  /api/billing/subscription
POST /api/webhooks/lemon-squeezy
```

`POST /api/billing/checkout` requires authentication and returns a hosted checkout URL.

`GET /api/billing/subscription` requires authentication and returns the current plan, subscription status, current period, monthly allowance, and used count.

`POST /api/webhooks/lemon-squeezy` is unauthenticated at the application user level but must verify the provider webhook signature.

## Error Handling

Checkout creation failures should return `502` when Lemon Squeezy is unavailable or rejects the request unexpectedly.

Invalid webhook signatures should return `401` or `400` and must not mutate state.

Duplicate webhook events should return `200` after confirming the event has already been processed.

Limited feature requests should return `402 Payment Required` when the user has exhausted the monthly allowance. The response body should use the standard application error shape and include enough information for the frontend to show an upgrade or limit-reached state.

## Testing

Cover billing behavior with focused tests:

- Checkout creation requires authentication.
- Checkout creation calls the provider adapter with the current user ID.
- Webhook signature verification rejects invalid signatures.
- Webhook processing is idempotent.
- Subscription-created webhook grants Pro status.
- Subscription-cancelled or payment-failed webhook removes Pro allowance.
- Free users receive the Free monthly allowance.
- Pro users receive the Pro monthly allowance.
- Requests over the monthly limit are rejected.
- Successful limited operations increment usage once.

Provider API calls should be mocked in tests. Product entitlement and usage logic should be tested without depending on live Lemon Squeezy network calls.

## Open Decisions

These values should be chosen before implementation:

- Free monthly usage allowance.
- Pro monthly usage allowance.
- Pro monthly price.
- Whether `past_due` gets a short grace period.
- Whether the limited operation is metadata lookup, deeper video analysis, or another product action.

## References

- Lemon Squeezy Merchant of Record: https://docs.lemonsqueezy.com/help/payments/merchant-of-record
- Lemon Squeezy supported countries: https://docs.lemonsqueezy.com/help/getting-started/supported-countries
- Lemon Squeezy fees: https://docs.lemonsqueezy.com/help/getting-started/fees
- Paddle supported countries: https://developer.paddle.com/concepts/sell/supported-countries-locales
- Polar Merchant of Record: https://polar.sh/docs/merchant-of-record/introduction
- Stripe Tax: https://stripe.com/tax
