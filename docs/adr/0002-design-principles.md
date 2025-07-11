# 2. Design principles

Date: 2025-07-11

## Status

Accepted

## Context

There are a few ways we can approach the solution; here we set down some principles
to guide our thinking.

## Decision

The following principles will be followed:

1. Use [event notifications](https://github.com/CSCfi/rems/blob/9b45fc2d63b0124a9b19ae8096c7a3d5ce0aef68/docs/event-notification.md#event-notification) where possible.
1. Use other configurable endpoints where necessary (e.g. [entitlement POST](https://github.com/CSCfi/rems/blob/9b45fc2d63b0124a9b19ae8096c7a3d5ce0aef68/docs/configuration.md#entitlement-post-v1))
1. Avoid compiled plugins if at all possible.
1. No changes to REMS origin core code.

## Consequences

1. Externally processing event notifications gives us complete decoupling
   from the REMS codebase. All that is required is configuration of [`:event-notification-targets`](https://github.com/CSCfi/rems/blob/9b45fc2d63b0124a9b19ae8096c7a3d5ce0aef68/resources/config-defaults.edn#L159).
1. Ditto, using entitlements POST.
1. Avoiding plugins keeps us away from `clj` and `lein`.
1. Abstaining from changes to REMS core gives the benefits of avoiding plugins
   as well as lets us track with all updates from origin.
